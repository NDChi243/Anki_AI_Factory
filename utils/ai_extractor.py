"""
🤖 AI Vocabulary Extractor — Dùng OpenAI-compatible API để trích xuất từ vựng từ văn bản

Hỗ trợ: OpenAI, DeepSeek, Claude (qua proxy), Ollama, LM Studio, và các API tương thích.
Cache thông minh: cache kết quả AI + cache danh sách từ vựng hiện có trong deck để tiết kiệm token.
Tự động quét deck Anki để tránh trùng lặp từ đã có.
V16.0: API key encryption at rest.
"""

import json
import os
import re
import hashlib
import time
import base64
import http.client
import ssl
import threading
from typing import Optional, Callable, List
from urllib.parse import urlparse

from .logger import get_logger

logger = get_logger()

# ═══════════════════════════════════════════════════════════
#  API KEY ENCRYPTION (AES-GCM via Fernet, fallback XOR)
# ═══════════════════════════════════════════════════════════

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False


def _get_machine_key() -> bytes:
    """Tạo key từ machine-specific info (username + hostname + salt)."""
    import getpass, socket
    raw = f"{getpass.getuser()}:{socket.gethostname()}:anki_tool_v15_salt"
    return hashlib.sha256(raw.encode()).digest()


def _derive_fernet_key() -> bytes:
    """Derive Fernet key từ machine key + PBKDF2 (nếu có cryptography)."""
    if not _HAS_CRYPTO:
        return _get_machine_key()[:16]
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"anki_tool_fernet_salt_v1",
        iterations=480_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(_get_machine_key()))


def _encrypt_api_key(plain_text: str) -> str:
    """Encrypt API key với AES-GCM (Fernet) nếu có cryptography, fallback XOR."""
    if not plain_text:
        return ""
    if _HAS_CRYPTO:
        try:
            f = Fernet(_derive_fernet_key())
            encrypted = f.encrypt(plain_text.encode("utf-8"))
            return "f:" + base64.b64encode(encrypted).decode("ascii")
        except Exception:
            pass
    # Fallback: XOR + base64
    key = _get_machine_key()[:16]
    data = plain_text.encode("utf-8")
    encrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
    return "x:" + base64.b64encode(encrypted).decode("ascii")


def _decrypt_api_key(encrypted_text: str) -> str:
    """Decrypt API key, auto-detect format (Fernet / XOR / plaintext)."""
    if not encrypted_text:
        return ""
    # Plaintext fallback (old format)
    if not encrypted_text.startswith(("f:", "x:")):
        return encrypted_text
    try:
        prefix = encrypted_text[:2]
        data = base64.b64decode(encrypted_text[2:])
        if prefix == "f:" and _HAS_CRYPTO:
            f = Fernet(_derive_fernet_key())
            return f.decrypt(data).decode("utf-8")
        elif prefix == "x:":
            key = _get_machine_key()[:16]
            decrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
            return decrypted.decode("utf-8")
    except Exception:
        pass
    return encrypted_text  # Fallback: return as-is

# ═══════════════════════════════════════════════════════════
#  HTTP HELPER — Connection reuse + chunked reading
# ═══════════════════════════════════════════════════════════
# SSL context MẶC ĐỊNH: verify đầy đủ (dùng cho cloud API như
# DeepSeek/OpenAI/OpenRouter — bảo vệ API key khỏi MITM).
_SSL_CONTEXT_SECURE = ssl.create_default_context()

# SSL context KHÔNG verify: CHỈ dùng khi host là localhost/127.0.0.1
# (Ollama, LM Studio thường tự ký chứng chỉ hoặc chạy HTTP thuần).
_SSL_CONTEXT_LOCAL = ssl.create_default_context()
_SSL_CONTEXT_LOCAL.check_hostname = False
_SSL_CONTEXT_LOCAL.verify_mode = ssl.CERT_NONE

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}

# OpenRouter — phát hiện để áp dụng rate limit phù hợp (free tier ~20 req/phút)
_OPENROUTER_MARKERS = ("openrouter.ai", "openrouter")


def is_openrouter(api_base: str = None) -> bool:
    """Kiểm tra xem API base có phải OpenRouter không (để áp dụng rate limit phù hợp)."""
    if not api_base:
        cfg = get_api_config()
        api_base = cfg.get("api_base", "")
    base = (api_base or "").lower()
    return any(m in base for m in _OPENROUTER_MARKERS)


def _pick_ssl_context(host: str) -> ssl.SSLContext:
    """Chọn SSL context: không verify chỉ khi host thực sự là local."""
    if (host or "").lower() in _LOCAL_HOSTS:
        return _SSL_CONTEXT_LOCAL
    return _SSL_CONTEXT_SECURE

# Connection pool cache theo thread — mỗi thread có connection riêng
# (tránh race condition khi nhiều QThread/ThreadPoolExecutor gọi API song song)
_conn_pool_local = threading.local()


def _create_conn(host: str, port: int, use_ssl: bool, timeout: int, ssl_context=None):
    """Tạo connection mới."""
    if use_ssl:
        return http.client.HTTPSConnection(host, port, timeout=timeout, context=ssl_context)
    return http.client.HTTPConnection(host, port, timeout=timeout)


def _get_thread_conn(pool_key: str, host: str, port: int, use_ssl: bool,
                     timeout: int, ssl_context=None, force_new: bool = False):
    """Lấy (hoặc tạo) connection từ pool của thread hiện tại."""
    pool = getattr(_conn_pool_local, "pool", None)
    if pool is None:
        pool = {}
        _conn_pool_local.pool = pool
    conn = pool.get(pool_key)
    if force_new or conn is None:
        conn = _create_conn(host, port, use_ssl, timeout, ssl_context)
        pool[pool_key] = conn
    return conn


# Rate limit state — theo dõi số lần gặp 429 để tự giảm tốc
_rate_limit_state = threading.local()


def _get_rate_limit_delay() -> float:
    """Lấy delay hiện tại giữa các request (tự tăng khi gặp 429)."""
    return getattr(_rate_limit_state, "delay", 0.0)


def _bump_rate_limit_delay():
    """Tăng delay khi gặp rate limit (429) — tự giảm tốc dần."""
    current = getattr(_rate_limit_state, "delay", 0.0)
    if current == 0.0:
        _rate_limit_state.delay = 3.2  # OpenRouter free ~20 req/phút → ~3s/request
    else:
        _rate_limit_state.delay = min(10.0, current * 1.5)  # 3.2 → 4.8 → 7.2 → 10


def _reset_rate_limit_delay():
    """Reset delay về 0 khi không còn gặp 429 (thành công liên tục)."""
    _rate_limit_state.delay = 0.0


def _http_post_json(url: str, payload: dict, headers: dict,
                    timeout: int = 300,
                    progress_callback: Optional[Callable[[str], None]] = None,
                    should_abort: Optional[Callable[[], bool]] = None) -> str:
    """Gửi POST request với JSON body, trả về response body dạng string.

    Dùng http.client thay vì urllib.request để:
    - Connection reuse (HTTP/1.1 keep-alive) theo thread
    - Đọc response theo chunk → progress callback
    - Timeout thực sự hoạt động
    - Xử lý HTTP 429 (Rate Limit) chuyên biệt: đọc Retry-After, retry mạnh hơn
    """
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path + ("?" + parsed.query if parsed.query else "")
    use_ssl = parsed.scheme == "https"
    ssl_context = _pick_ssl_context(host)

    # Lấy hoặc tạo connection từ pool của thread hiện tại (không cần lock)
    pool_key = f"{host}:{port}"
    conn = _get_thread_conn(pool_key, host, port, use_ssl, timeout, ssl_context)

    body_bytes = json.dumps(payload).encode("utf-8")
    headers["Content-Length"] = str(len(body_bytes))

    # Nếu đang bị rate limit (từ lần trước), chờ trước khi gửi
    rate_delay = _get_rate_limit_delay()
    if rate_delay > 0:
        if progress_callback:
            progress_callback(f"⏳ Đang chờ {rate_delay:.1f}s (tránh rate limit)...")
        time.sleep(rate_delay)

    last_error = None
    # Retry nhiều hơn cho 429 (rate limit thường tạm thời) — tối đa 5 lần
    max_retries = 5
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                # Tạo connection MỚI khi retry (connection cũ có thể đã hỏng)
                conn = _get_thread_conn(pool_key, host, port, use_ssl, timeout, ssl_context,
                                        force_new=True)

            conn.request("POST", path, body=body_bytes, headers=headers)
            resp = conn.getresponse()

            if resp.status == 429:
                # Rate limit — đọc Retry-After nếu có, chờ đúng thời gian
                retry_after = resp.getheader("Retry-After")
                err_body = resp.read().decode("utf-8", errors="replace")[:300]
                _bump_rate_limit_delay()
                if retry_after:
                    try:
                        wait = float(retry_after)
                    except ValueError:
                        wait = 30.0
                else:
                    wait = 30.0
                if progress_callback:
                    progress_callback(
                        f"⚠️ Rate limit (429) — chờ {wait:.0f}s rồi thử lại...\n"
                        f"💡 OpenRouter free giới hạn ~20 req/phút. Đang tự chậm lại."
                    )
                time.sleep(wait)
                last_error = http.client.HTTPException(
                    f"HTTP 429 Rate Limit: {err_body}"
                )
                continue

            if resp.status >= 400:
                err_body = resp.read().decode("utf-8", errors="replace")[:500]
                raise http.client.HTTPException(
                    f"HTTP {resp.status} {resp.reason}: {err_body}"
                )

            # Đọc response theo chunk
            chunks = []
            total_read = 0
            content_length = int(resp.getheader("Content-Length", 0))
            while True:
                if should_abort and should_abort():
                    conn.close()
                    raise RuntimeError("⏹ Đã hủy bởi người dùng")
                chunk = resp.read(8192)
                if not chunk:
                    break
                chunks.append(chunk)
                total_read += len(chunk)
                if progress_callback and content_length > 0 and total_read % 65536 < 8192:
                    pct = min(99, total_read * 100 // content_length)
                    progress_callback(f"⏳ Đang nhận dữ liệu... {pct}%")

            body = b"".join(chunks).decode("utf-8")
            # Thành công → reset rate limit delay (nếu có)
            _reset_rate_limit_delay()
            return body

        except (http.client.HTTPException, ConnectionError, TimeoutError, OSError) as e:
            last_error = e
            if attempt < max_retries:
                delay = 2.0 * (2 ** attempt)
                if progress_callback:
                    progress_callback(f"🔄 Retry {attempt + 1}/{max_retries} sau {delay:.0f}s...")
                time.sleep(delay)
                continue
            raise RuntimeError(f"❌ Lỗi kết nối sau {max_retries + 1} lần thử: {last_error}")

    raise RuntimeError(f"❌ Không thể kết nối: {last_error}")

# ═══════════════════════════════════════════════════════════
#  PATHS
# ═══════════════════════════════════════════════════════════
_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_CONFIG_DIR, "ai_config.json")
_CACHE_DIR = os.path.join(_CONFIG_DIR, "ai_cache")
_DECK_VOCAB_CACHE_TTL = 30 * 60  # 30 phút


def _ensure_cache_dir():
    os.makedirs(_CACHE_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
def _load_config() -> dict:
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_config(cfg: dict):
    """Ghi config với atomic write (tmp → rename) để tránh mất dữ liệu nếu crash."""
    tmp_path = _CONFIG_PATH + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, _CONFIG_PATH)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise


def get_api_config() -> dict:
    defaults = {
        "api_key": "",
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "max_tokens": 8192,
        # Độ dài nội dung tối đa gửi trong 1 request (ký tự) — DeepSeek 64k context
        "max_chars": 45000,
        # Kích thước chunk khi chia văn bản dài (ký tự).
        # 8k = cắt mịn → chất lượng cao hơn; an toàn với giới hạn OUTPUT ~8192 token.
        "chunk_size": 8000,
        # Mức độ nỗ lực suy nghĩ: "" / auto (không gửi), "low", "medium", "high"
        "reasoning_effort": "",
    }
    cfg = _load_config()
    for k, v in defaults.items():
        cfg.setdefault(k, v)
    # Sanitize các giá trị đã lưu (VD bản cũ đang để chunk 45k → gây cắt output)
    try:
        cfg["max_chars"] = max(10000, min(45000, int(cfg.get("max_chars") or 45000)))
        cfg["chunk_size"] = max(3000, min(15000, int(cfg.get("chunk_size") or 8000)))
    except Exception:
        cfg["max_chars"] = 45000
        cfg["chunk_size"] = 8000
    # Decrypt API key nếu đã được encrypt (f: = Fernet, x: = XOR)
    if cfg.get("api_key") and cfg["api_key"].startswith(("f:", "x:")):
        cfg["api_key"] = _decrypt_api_key(cfg["api_key"])
    return cfg


def save_api_config(api_key: str, api_base: str, model: str, temperature: float = 0.3,
                    max_chars: int = 45000, chunk_size: int = 8000,
                    reasoning_effort: str = ""):
    # Sanitize input
    api_base = api_base.strip().rstrip("/")
    if api_base and not api_base.startswith(("http://", "https://")):
        api_base = "https://" + api_base
    model = model.strip()
    temperature = max(0.0, min(2.0, temperature))
    max_chars = max(10000, min(45000, int(max_chars)))
    # 3k-15k — cắt mịn hơn để chất lượng tốt & không tràn output token (DeepSeek ~8192)
    chunk_size = max(3000, min(15000, int(chunk_size)))
    reasoning_effort = (reasoning_effort or "").strip().lower()
    if reasoning_effort not in ("low", "medium", "high"):
        reasoning_effort = ""

    cfg = {
        "api_key": _encrypt_api_key(api_key.strip()) if api_key.strip() else "",
        "api_base": api_base,
        "model": model,
        "temperature": temperature,
        "max_tokens": 8192,
        "max_chars": max_chars,
        "chunk_size": chunk_size,
        "reasoning_effort": reasoning_effort,
    }
    _save_config(cfg)


def _apply_reasoning_effort(payload: dict, cfg: dict):
    """Thêm reasoning_effort vào payload nếu được cấu hình (OpenAI o1/o3/o4, DeepSeek-compatible).

    Mức độ suy nghĩ cao → chất lượng tốt hơn nhưng tốn NHIỀU token output hơn.
    """
    effort = (cfg.get("reasoning_effort") or "").strip().lower()
    if effort in ("low", "medium", "high"):
        payload["reasoning_effort"] = effort
    return payload


def _check_truncated_output(content: str, progress_callback: Optional[Callable[[str], None]] = None):
    """Cảnh báo khi output JSON bị cắt (kết thúc không phải ] hoặc }).

    DeepSeek giới hạn output ~8192 token/response → nếu chunk quá lớn,
    JSON sẽ bị cắt giữa chừng gây lỗi parse.
    """
    if not content:
        return
    c = content.strip()
    if c and not (c.endswith("]") or c.endswith("}")):
        if progress_callback:
            progress_callback(
                "⚠️ Kết quả bị CẮT do giới hạn token output (max_tokens).\n"
                "💡 Giảm 'Độ dài xử lý mỗi lần gọi' trong Cài Đặt AI (VD 6k-10k) "
                "hoặc chia nhỏ văn bản."
            )


# ═══════════════════════════════════════════════════════════
#  TOKEN & COST TRACKING
# ═══════════════════════════════════════════════════════════

# DeepSeek pricing per 1M tokens (USD)
_DEEPSEEK_PRICING = {
    "deepseek-chat":      (0.14, 0.28),   # input, output
    "deepseek-reasoner":  (0.55, 2.19),
}


def _calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> dict:
    """Tính chi phí USD từ token usage. Trả về dict đầy đủ thông tin."""
    input_price, output_price = _DEEPSEEK_PRICING.get(model, (0.14, 0.28))
    input_cost = (prompt_tokens / 1_000_000) * input_price
    output_cost = (completion_tokens / 1_000_000) * output_price
    total = input_cost + output_cost
    return {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total, 6),
    }


def _format_token_report(token_info: dict) -> str:
    """Format token + cost thành text hiển thị."""
    tc = token_info
    return (
        f"🔢 Token: {tc['prompt_tokens']:,} in + {tc['completion_tokens']:,} out "
        f"= {tc['total_tokens']:,} total | "
        f"💰 ${tc['total_cost']:.6f} "
        f"(in: ${tc['input_cost']:.6f} / out: ${tc['output_cost']:.6f})"
    )


# ═══════════════════════════════════════════════════════════
#  CACHE (AI results)
# ═══════════════════════════════════════════════════════════
# Bump version mỗi khi thay đổi prompt/chiến lược → invalidate cache cũ
_PROMPT_VERSION = 3


def _ai_cache_key(text: str, lang: str, instruction: str, existing_hash: str, kind: str = "vocab") -> str:
    raw = f"{_PROMPT_VERSION}|{kind}|{lang}|{instruction}|{existing_hash}|{text}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _ai_cache_get(text: str, lang: str, instruction: str, existing_hash: str, kind: str = "vocab") -> Optional[list]:
    _ensure_cache_dir()
    key = _ai_cache_key(text, lang, instruction, existing_hash, kind=kind)
    cache_file = os.path.join(_CACHE_DIR, f"ai_{key}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # TTL cache: 14 ngày nếu dùng OpenRouter (giảm request lặp lại do rate limit),
            # 7 ngày cho provider khác
            ttl = 14 * 24 * 3600 if is_openrouter() else 7 * 24 * 3600
            if time.time() - data.get("_cached_at", 0) < ttl:
                return data.get("vocab", [])
        except Exception:
            pass
    return None


def _ai_cache_set(text: str, lang: str, instruction: str, existing_hash: str, vocab_list: list, kind: str = "vocab"):
    _ensure_cache_dir()
    key = _ai_cache_key(text, lang, instruction, existing_hash, kind=kind)
    cache_file = os.path.join(_CACHE_DIR, f"ai_{key}.json")
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({
                "vocab": vocab_list,
                "_kind": kind,
                "_cached_at": time.time(),
                "_lang": lang,
                "_text_preview": text[:200],
            }, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def clear_cache():
    """Xóa toàn bộ cache"""
    if os.path.exists(_CACHE_DIR):
        import shutil
        shutil.rmtree(_CACHE_DIR)


# ═══════════════════════════════════════════════════════════
#  DECK VOCAB CACHE (re-export from utils/deck_cache.py)
# ═══════════════════════════════════════════════════════════
from .deck_cache import (
    get_existing_vocab_from_deck,
    invalidate_deck_cache,
    make_existing_hash as _make_existing_hash,
)


# ═══════════════════════════════════════════════════════════
#  SYSTEM PROMPTS NÂNG CAO
# ═══════════════════════════════════════════════════════════

_CHINESE_JSON_TEMPLATE = """{
  "simplified": "学习",
  "traditional": "學習",
  "pinyin": "xuéxí",
  "meaning": "học tập",
  "sino_vietnamese": "học tập",
  "hsk_level": "HSK1",
  "topic": "Động từ",
  "example": "我每天学习中文。",
  "example_pinyin": "Wǒ měitiān xuéxí zhōngwén.",
  "example_vn": "Mỗi ngày tôi học tiếng Trung.",
  "example_2": "他在图书馆认真学习。",
  "example_2_pinyin": "Tā zài túshūguǎn rènzhēn xuéxí.",
  "example_2_vn": "Anh ấy học tập chăm chỉ ở thư viện."
}"""

_CHINESE_SYSTEM_PROMPT = f"""Bạn là chuyên gia tiếng Trung. Trích xuất TẤT CẢ từ vựng từ văn bản → mảng JSON chính xác.

MẪU:
{_CHINESE_JSON_TEMPLATE}

LUẬT:
1. Đủ 13 trường; thiếu → "". example_pinyin & example_2_pinyin LUÔN phải có, pinyin chuẩn có dấu thanh; thiếu → từ không hợp lệ.
2. VÍ DỤ CÓ HỒN + ĐÚNG CẤP ĐỘ (quan trọng nhất):
   - Ex1: khẩu ngữ đời thực (cà phê, nhắn tin, than thở, MXH...), cảm xúc thật.
   - Ex2: trang trọng, lịch sự, formal (công việc, hội họp, thư từ).
   - Cấp độ ví dụ khớp HSK: HSK1 → câu cực ngắn; HSK2-3 → đơn giản; HSK4 → trung bình; HSK5-6 → phức tạp, thành ngữ. TUYỆT ĐỐI không nhồi từ khó vào từ cấp thấp.
   - TRÁNH câu SGK vô hồn ("我是学生"). Từ đa nghĩa → 2 nghĩa khác nhau ở 2 ví dụ. Ví dụ ngắn gọn, 5-12 từ.
3. CHỐNG TRÙNG: bỏ qua mọi từ trong "TỪ ĐÃ CÓ".
4. CHÍNH XÁC: pinyin, ngữ pháp, từ vựng chuẩn. topic ngắn, đúng HSK.
5. Xuất theo thứ tự xuất hiện trong văn bản.

ĐẦU RA: CHỈ mảng JSON thuần, không markdown, không giải thích thừa. Cuối: {{"_comment":"≤15 từ"}}"""

_JAPANESE_JSON_TEMPLATE = """{
  "front": "食べる",
  "furigana": "たべる",
  "meaning": "ăn",
  "sino-vietnamese": "thực",
  "jlptlevel": "N5",
  "topic": "Động từ",
  "example": "毎日ご飯を食べるよ。",
  "example_vn": "Hàng ngày tớ ăn cơm đó.",
  "example_2": "お客様とご一緒に夕食を召し上がりました。",
  "example_2_vn": "Tôi đã dùng bữa tối cùng với quý khách."
}"""

_JAPANESE_SYSTEM_PROMPT = f"""Bạn là chuyên gia tiếng Nhật. Trích xuất TẤT CẢ từ vựng từ văn bản → mảng JSON chính xác.

MẪU:
{_JAPANESE_JSON_TEMPLATE}

LUẬT:
1. Đủ 10 trường; thiếu → "".
2. VÍ DỤ CÓ HỒN + ĐÚNG CẤP ĐỘ (quan trọng nhất):
   - Ex1: khẩu ngữ đời thực (quán cà phê, LINE, than thở, MXH...), cảm xúc thật, trợ từ cuối câu tự nhiên (よ/ね/よね/じゃん).
   - Ex2: trang trọng, lịch sự (です・ます/敬語).
   - Cấp độ ví dụ khớp JLPT: N5 → câu cực ngắn; N4 → đơn giản; N3 → trung bình; N2-N1 → phức tạp, thành ngữ. TUYỆT ĐỐI không nhồi từ khó vào từ cấp thấp.
   - TRÁNH câu SGK vô hồn. Từ đa nghĩa → 2 nghĩa khác nhau ở 2 ví dụ. Ví dụ ngắn gọn, 5-12 từ.
3. CHỐNG TRÙNG: bỏ qua mọi từ trong "TỪ ĐÃ CÓ".
4. CHÍNH XÁC: furigana, ngữ pháp, từ vựng chuẩn. topic ngắn, đúng JLPT.
5. Xuất theo thứ tự xuất hiện trong văn bản.

ĐẦU RA: CHỈ mảng JSON thuần, không markdown, không giải thích thừa. Cuối: {{"_comment":"≤15 từ"}}"""

_KOREAN_JSON_TEMPLATE = """{
  "front": "먹다",
  "romanization": "meokda",
  "meaning": "ăn",
  "sino_vietnamese": "",
  "topik_level": "TOPIK I",
  "topic": "Động từ",
  "example": "아침에 밥을 먹어요.",
  "example_romanization": "achime babeul meogeoyo.",
  "example_vn": "Buổi sáng tôi ăn cơm.",
  "example_2": "친구와 함께 저녁을 먹었어요.",
  "example_2_romanization": "chin-guwa hamkke jeonyeogeul meogeosseoyo.",
  "example_2_vn": "Tôi đã ăn tối cùng bạn bè."
}"""

_KOREAN_SYSTEM_PROMPT = f"""Bạn là chuyên gia tiếng Hàn. Trích xuất TẤT CẢ từ vựng từ văn bản → mảng JSON chính xác.

MẪU:
{_KOREAN_JSON_TEMPLATE}

LUẬT:
1. Đủ 12 trường; thiếu → "". example_romanization & example_2_romanization LUÔN phải có, romanization chuẩn (Revised Romanization); thiếu → từ không hợp lệ.
2. VÍ DỤ CÓ HỒN + ĐÚNG CẤP ĐỘ (quan trọng nhất):
   - Ex1: khẩu ngữ đời thực (cà phê, nhắn tin, than thở, MXH...), cảm xúc thật, kết thúc câu tự nhiên (어요/아요/거야/잖아).
   - Ex2: trang trọng, lịch sự (습니다/습니다/존댓말).
   - Cấp độ ví dụ khớp TOPIK: TOPIK I → câu cực ngắn, đơn giản; TOPIK II → trung bình/phức tạp. TUYỆT ĐỐI không nhồi từ khó vào từ cấp thấp.
   - TRÁNH câu SGK vô hồn. Từ đa nghĩa → 2 nghĩa khác nhau ở 2 ví dụ. Ví dụ ngắn gọn, 5-12 từ.
3. CHỐNG TRÙNG: bỏ qua mọi từ trong "TỪ ĐÃ CÓ".
4. CHÍNH XÁC: Hangul, romanization, ngữ pháp, từ vựng chuẩn. topic ngắn, đúng TOPIK.
5. Xuất theo thứ tự xuất hiện trong văn bản.

ĐẦU RA: CHỈ mảng JSON thuần, không markdown, không giải thích thừa. Cuối: {{"_comment":"≤15 từ"}}"""

_SYSTEM_PROMPTS = {
    "japanese": _JAPANESE_SYSTEM_PROMPT,
    "chinese": _CHINESE_SYSTEM_PROMPT,
    "korean": _KOREAN_SYSTEM_PROMPT,
}

_JSON_TEMPLATES = {
    "japanese": _JAPANESE_JSON_TEMPLATE,
    "chinese": _CHINESE_JSON_TEMPLATE,
    "korean": _KOREAN_JSON_TEMPLATE,
}


def get_json_template(lang: str) -> str:
    return _JSON_TEMPLATES.get(lang, _JAPANESE_JSON_TEMPLATE)


# ═══════════════════════════════════════════════════════════
#  GRAMMAR SYSTEM PROMPTS — Note Type ngữ pháp riêng
# ═══════════════════════════════════════════════════════════

_JAPANESE_GRAMMAR_JSON_TEMPLATE = """{
  "pattern": "〜てもいい",
  "reading": "てもいい",
  "meaning": "được phép làm gì đó",
  "jlptlevel": "N5",
  "topic": "Cho phép / Xin phép",
  "usage": "Vて + もいいです",
  "explanation": "Dùng để xin phép hoặc cho phép ai làm gì. Thân mật: 〜てもいいよ",
  "example": "ここで写真を撮ってもいいですか。",
  "example_vn": "Tôi chụp ảnh ở đây được không?",
  "example_2": "明日は休んでもいいよ。",
  "example_2_vn": "Mai nghỉ cũng được nhé."
}"""

_JAPANESE_GRAMMAR_SYSTEM_PROMPT = f"""Bạn là chuyên gia NGỮ PHÁP tiếng Nhật (文法). Trích xuất TẤT CẢ cấu trúc ngữ pháp từ văn bản → mảng JSON chính xác.

MẪU:
{_JAPANESE_GRAMMAR_JSON_TEMPLATE}

LUẬT:
1. Đủ 11 trường; thiếu → "".
2. pattern: cấu trúc CHÍNH — LUÔN viết bằng CHỮ GỐC (kanji + kana), ghi rõ chỗ điền bằng "〜" hoặc ký hiệu loại từ (V/イA/ナA/N). KHÔNG dùng romaji (VD viết "〜てもいい", không viết "te mo ii").
3. reading: cách đọc nếu là từ/trợ từ cụ thể; bỏ trống nếu cấu trúc có biến tố.
4. usage: CÔNG THỨC ghép dễ nhớ (VD: "Vて + もいいです").
5. explanation: TỐI ĐA 2 câu — cách dùng + sắc thái + lỗi người Việt hay mắc + đồng nghĩa/trái nghĩa (nếu có). Gọn, không lan man.
6. VÍ DỤ CÓ HỒN + ĐÚNG CẤP ĐỘ:
   - Ex1: khẩu ngữ đời thực (普通体), cảm xúc thật, trợ từ よ/ね/よね.
   - Ex2: trang trọng, lịch sự (です・ます/敬語).
   - Cấp độ ví dụ khớp JLPT của pattern; KHÔNG nhồi từ khó. Ví dụ 5-12 từ.
7. CHÍNH XÁC: ngữ pháp, cách dùng, từ vựng chuẩn. topic ngắn, đúng trọng tâm.
8. NHƯ GIẢNG VIÊN ĐỌC GIÁO TRÌNH: Đọc kỹ TOÀN BỘ văn bản, hiểu ngữ cảnh + từ vựng đi kèm rồi mới trích. Ví dụ phải bám ngữ cảnh thực của bài, dùng từ vựng ĐA DẠNG (không lặp cùng 1 cụm từ trong mọi ví dụ).
9. CÙNG PATTERN – KHÁC NGHĨA: Nếu 1 pattern xuất hiện nhiều lần với từ đi kèm khác nhau tạo NGHĨA/CÁCH DÙNG khác nhau → tạo NHIỀU entry riêng (meaning khác nhau, ví dụ khác nhau) thay vì gộp. Không tạo trùng lặp máy móc nếu thực sự giống nghĩa.
10. ĐÁNH DẤU PATTERN: Trong example/example_2, BỌC phần thể hiện pattern bằng <b>…</b> để nổi bật trên thẻ (Anki render HTML, ví dụ: "ここで写真を撮<b>ってもいい</b>ですか。").

ĐẦU RA: CHỈ mảng JSON thuần, không markdown, không giải thích thừa. Cuối: {{"_comment":"≤15 từ"}}"""

_CHINESE_GRAMMAR_JSON_TEMPLATE = """{
  "pattern": "把 + N + V",
  "pinyin": "bǎ + N + V",
  "meaning": "đem/ làm gì đó với ... (nhấn mạnh kết quả)",
  "hsk_level": "HSK3",
  "topic": "Cấu trúc câu",
  "usage": "Chủ ngữ + 把 + 宾语 + Động từ + Kết quả",
  "explanation": "Dùng khi nhấn mạnh việc tác động lên vật và kết quả. Lỗi người Việt hay quên: câu 把 bắt buộc có kết quả (了/补语).",
  "example": "我把作业做完了。",
  "example_pinyin": "Wǒ bǎ zuòyè zuò wán le.",
  "example_vn": "Tôi đã làm xong bài tập.",
  "example_2": "请把门关上。",
  "example_2_pinyin": "Qǐng bǎ mén guān shàng.",
  "example_2_vn": "Làm ơn đóng cửa lại."
}"""

_CHINESE_GRAMMAR_SYSTEM_PROMPT = f"""Bạn là chuyên gia NGỮ PHÁP tiếng Trung (语法). Trích xuất TẤT CẢ cấu trúc ngữ pháp từ văn bản → mảng JSON chính xác.

MẪU:
{_CHINESE_GRAMMAR_JSON_TEMPLATE}

LUẬT:
1. Đủ 13 trường; thiếu → "". example_pinyin & example_2_pinyin LUÔN phải có, pinyin chuẩn có dấu thanh.
2. pattern: cấu trúc CHÍNH — LUÔN viết bằng HÁN TỰ gốc, ghi rõ chỗ điền bằng ký hiệu loại từ (N/V/Adj). KHÔNG viết pattern bằng pinyin (VD viết "把字句", không viết "bǎ zì jù").
3. pinyin: phiên âm phần cấu trúc.
4. usage: CÔNG THỨC ghép dễ nhớ (VD: "Chủ ngữ + 把 + 宾语 + V + 结果").
5. explanation: TỐI ĐA 2 câu — cách dùng + sắc thái + lỗi người Việt hay mắc + đồng nghĩa (nếu có). Gọn.
6. VÍ DỤ CÓ HỒN + ĐÚNG CẤP ĐỘ:
   - Ex1: khẩu ngữ đời thực, cảm xúc thật. Ex2: trang trọng, formal.
   - Cấp độ ví dụ khớp HSK của pattern; KHÔNG nhồi từ khó. Ví dụ 5-12 từ.
   - MỌI ví dụ PHẢI kèm pinyin đầy đủ, có dấu thanh.
7. CHÍNH XÁC: ngữ pháp, pinyin, cách dùng chuẩn. topic ngắn, đúng trọng tâm.
8. NHƯ GIẢNG VIÊN ĐỌC GIÁO TRÌNH: Đọc kỹ TOÀN BỘ văn bản, hiểu ngữ cảnh + từ vựng đi kèm rồi mới trích. Ví dụ phải bám ngữ cảnh thực của bài, dùng từ vựng ĐA DẠNG (không lặp cùng 1 cụm từ trong mọi ví dụ).
9. CÙNG PATTERN – KHÁC NGHĨA: Nếu 1 pattern xuất hiện nhiều lần với từ đi kèm khác nhau tạo NGHĨA/CÁCH DÙNG khác nhau → tạo NHIỀU entry riêng (meaning khác nhau, ví dụ khác nhau) thay vì gộp. Không tạo trùng lặp máy móc nếu thực sự giống nghĩa.
10. ĐÁNH DẤU PATTERN: Trong example/example_2, BỌC phần thể hiện pattern bằng <b>…</b> để nổi bật trên thẻ (Anki render HTML, ví dụ: "我把作业做<b>完了</b>。").

ĐẦU RA: CHỈ mảng JSON thuần, không markdown, không giải thích thừa. Cuối: {{"_comment":"≤15 từ"}}"""

_KOREAN_GRAMMAR_JSON_TEMPLATE = """{
  "pattern": "~아/어요",
  "romanization": "a/eoyo",
  "meaning": "dạng lịch sự thân mật (hiện tại)",
  "topik_level": "TOPIK I",
  "topic": "Kết thúc câu",
  "usage": "Động từ/tính từ + 아요 (âm cuối 양/ㅗ/ㅏ) hoặc + 어요 (các âm còn lại)",
  "explanation": "Dạng kết thúc câu lịch sự thông dụng nhất trong giao tiếp. Lỗi người Việt hay nhầm giữa 아요 và 어요.",
  "example": "지금 학교에 가요.",
  "example_romanization": "jigeum hakgyoe gayo.",
  "example_vn": "Bây giờ tôi đi học.",
  "example_2": "밥을 맛있게 먹어요.",
  "example_2_romanization": "babeul masitge meogeoyo.",
  "example_2_vn": "Tôi ăn cơm ngon lành."
}"""

_KOREAN_GRAMMAR_SYSTEM_PROMPT = f"""Bạn là chuyên gia NGỮ PHÁP tiếng Hàn (한국어 문법). Trích xuất TẤT CẢ cấu trúc ngữ pháp từ văn bản → mảng JSON chính xác.

MẪU:
{_KOREAN_GRAMMAR_JSON_TEMPLATE}

LUẬT:
1. Đủ 13 trường; thiếu → "". example_romanization & example_2_romanization LUÔN phải có, romanization chuẩn (Revised Romanization).
2. pattern: cấu trúc CHÍNH — LUÔN viết bằng HANGUL gốc, ghi rõ chỗ điền bằng "~" hoặc ký hiệu loại từ (V/A/N). KHÔNG dùng romanization làm pattern (VD viết "~아/어요", không viết "a/eoyo").
3. romanization: phiên âm phần cấu trúc.
4. usage: CÔNG THỨC ghép dễ nhớ (VD: "Động từ + 아요/어요").
5. explanation: TỐI ĐA 2 câu — cách dùng + sắc thái + lỗi người Việt hay mắc + đồng nghĩa (nếu có). Gọn.
6. VÍ DỤ CÓ HỒN + ĐÚNG CẤP ĐỘ:
   - Ex1: khẩu ngữ đời thực, cảm xúc thật. Ex2: trang trọng, lịch sự.
   - Cấp độ ví dụ khớp TOPIK của pattern; KHÔNG nhồi từ khó. Ví dụ 5-12 từ.
   - MỌI ví dụ PHẢI kèm romanization đầy đủ.
7. CHÍNH XÁC: ngữ pháp, romanization, cách dùng chuẩn. topic ngắn, đúng trọng tâm.
8. NHƯ GIẢNG VIÊN ĐỌC GIÁO TRÌNH: Đọc kỹ TOÀN BỘ văn bản, hiểu ngữ cảnh + từ vựng đi kèm rồi mới trích. Ví dụ phải bám ngữ cảnh thực của bài, dùng từ vựng ĐA DẠNG (không lặp cùng 1 cụm từ trong mọi ví dụ).
9. CÙNG PATTERN – KHÁC NGHĨA: Nếu 1 pattern xuất hiện nhiều lần với từ đi kèm khác nhau tạo NGHĨA/CÁCH DÙNG khác nhau → tạo NHIỀU entry riêng (meaning khác nhau, ví dụ khác nhau) thay vì gộp. Không tạo trùng lặp máy móc nếu thực sự giống nghĩa.
10. ĐÁNH DẤU PATTERN: Trong example/example_2, BỌC phần thể hiện pattern bằng <b>…</b> để nổi bật trên thẻ (Anki render HTML, ví dụ: "지금 학교에 <b>가요</b>.").

ĐẦU RA: CHỈ mảng JSON thuần, không markdown, không giải thích thừa. Cuối: {{"_comment":"≤15 từ"}}"""

_GRAMMAR_SYSTEM_PROMPTS = {
    "japanese": _JAPANESE_GRAMMAR_SYSTEM_PROMPT,
    "chinese": _CHINESE_GRAMMAR_SYSTEM_PROMPT,
    "korean": _KOREAN_GRAMMAR_SYSTEM_PROMPT,
}

_GRAMMAR_JSON_TEMPLATES = {
    "japanese": _JAPANESE_GRAMMAR_JSON_TEMPLATE,
    "chinese": _CHINESE_GRAMMAR_JSON_TEMPLATE,
    "korean": _KOREAN_GRAMMAR_JSON_TEMPLATE,
}


def get_grammar_json_template(lang: str) -> str:
    return _GRAMMAR_JSON_TEMPLATES.get(lang, _JAPANESE_GRAMMAR_JSON_TEMPLATE)


# ═══════════════════════════════════════════════════════════
#  TEXT EXTRACTION — đọc nội dung file làm tài liệu tham khảo
#  Hỗ trợ: txt, md, csv, pdf, docx, doc, xlsx, xls
#  Lưu ý: DeepSeek/OpenAI chat chỉ nhận TEXT → trích text tại máy.
# ═══════════════════════════════════════════════════════════

def _pip_install(package: str) -> bool:
    """Tự động cài đặt thư viện Python bằng pip (giống pattern TTS)."""
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", package])
        return True
    except Exception:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            return True
        except Exception:
            logger.warning("Không thể tự cài %s — cài thủ công: pip install %s", package, package)
            return False


def _install_docx() -> bool:
    try:
        import docx  # noqa: F401
        return True
    except ImportError:
        return _pip_install("python-docx")


def _install_openpyxl() -> bool:
    try:
        import openpyxl  # noqa: F401
        return True
    except ImportError:
        return _pip_install("openpyxl")


def extract_text_from_file(filepath: str) -> str:
    """Đọc nội dung text từ file. Hỗ trợ txt/md/csv/pdf/docx/doc/xlsx/xls.

    Trả về "" (không raise) nếu không đọc được / file không tồn tại.
    """
    if not filepath or not os.path.exists(filepath):
        return ""

    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".txt":
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    if ext in (".md", ".markdown"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass

    if ext == ".csv":
        return _extract_csv_text(filepath)

    if ext == ".pdf":
        return _extract_pdf_text(filepath)

    if ext == ".docx":
        return _extract_docx_text(filepath)

    if ext == ".doc":
        # .doc (Word cũ) không đọc bằng python-docx → thử, nếu fail trả message
        result = _extract_docx_text(filepath)
        if result:
            return result
        return "⚠️ File .doc (Word cũ) chưa hỗ trợ. Vui lòng lưu lại thành .docx hoặc .txt rồi thử lại."

    if ext in (".xlsx", ".xls"):
        return _extract_sheet_text(filepath)

    # Fallback: thử đọc như text thuần
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        pass

    return ""


def extract_text_from_files(filepaths) -> list:
    """Đọc text từ NHIỀU file. Trả về list [(name, text), ...] — bỏ file không đọc được."""
    results = []
    for filepath in filepaths or []:
        try:
            text = extract_text_from_file(filepath)
            if text and text.strip():
                results.append((os.path.basename(filepath), text))
        except Exception as e:
            logger.warning("Lỗi đọc file %s: %s", filepath, e)
    return results


def _extract_csv_text(filepath: str) -> str:
    """Đọc file CSV — nối các ô bằng dấu phẩy, mỗi dòng 1 hàng."""
    try:
        import csv as _csv
        rows = []
        with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
            for row in _csv.reader(f):
                cells = [c.strip() for c in row if c and str(c).strip()]
                if cells:
                    rows.append(", ".join(cells))
        return "\n".join(rows)
    except Exception:
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                return f.read()
        except Exception:
            return ""


def _extract_sheet_text(filepath: str) -> str:
    """Đọc file Excel (xlsx/xls) — mỗi sheet + mỗi ô trên 1 dòng."""
    # Ưu tiên openpyxl (auto-install nếu thiếu)
    if _install_openpyxl():
        try:
            import openpyxl
            wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
            parts = []
            for ws in wb.worksheets:
                parts.append(f"### Sheet: {ws.title}")
                for row in ws.iter_rows(values_only=True):
                    cells = [str(c).strip() for c in row if c is not None and str(c).strip()]
                    if cells:
                        parts.append(" | ".join(cells))
            wb.close()
            if parts:
                return "\n".join(parts)
        except Exception as e:
            logger.warning("openpyxl đọc lỗi %s: %s", filepath, e)

    # Fallback: pandas (nếu có)
    try:
        import pandas as pd
        parts = []
        xl = pd.ExcelFile(filepath)
        for sheet in xl.sheet_names:
            df = xl.parse(sheet, header=None)
            parts.append(f"### Sheet: {sheet}")
            parts.append(df.to_string(index=False, header=False))
        if parts:
            return "\n".join(parts)
    except ImportError:
        pass
    except Exception as e:
        logger.warning("pandas đọc lỗi %s: %s", filepath, e)

    return ""


def _extract_pdf_text(filepath: str) -> str:
    for lib in ["pdfplumber", "PyPDF2", "fitz"]:
        try:
            if lib == "pdfplumber":
                import pdfplumber
                parts = []
                with pdfplumber.open(filepath) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t: parts.append(t)
                return "\n".join(parts)
            elif lib == "PyPDF2":
                from PyPDF2 import PdfReader
                parts = []
                for page in PdfReader(filepath).pages:
                    t = page.extract_text()
                    if t: parts.append(t)
                return "\n".join(parts)
            elif lib == "fitz":
                import fitz
                doc = fitz.open(filepath)
                parts = [page.get_text() for page in doc if page.get_text()]
                doc.close()
                return "\n".join(parts)
        except ImportError:
            continue
    return ""


def _extract_docx_text(filepath: str) -> str:
    if not _install_docx():
        return ""
    try:
        from docx import Document
        parts = [p.text for p in Document(filepath).paragraphs if p.text.strip()]
        return "\n".join(parts)
    except Exception as e:
        logger.warning("python-docx đọc lỗi %s: %s", filepath, e)
        return ""


# ═══════════════════════════════════════════════════════════
#  AI API CALL (cache + existing_words context)
# ═══════════════════════════════════════════════════════════

# Số mục tối đa đưa vào prompt (giới hạn token input)
_MAX_EXISTING_SHOWN = 400


def _format_existing_context(existing: List[str], text: str, label: str = "TỪ") -> str:
    """Tạo chuỗi 'mục đã có' GỌN cho prompt — tối ưu token input.

    Chỉ liệt kê các mục THỰC SỰ xuất hiện trong nội dung đang xử lý
    (khả năng AI trùng cao nhất), không gửi toàn bộ deck hàng nghìn từ.
    Không có mục trùng → chỉ báo tổng số, AI cứ trích xuất bình thường.
    """
    if not existing:
        return ""
    text_lower = text.lower()
    overlap = []
    seen = set()
    for w in existing:
        w = (w or "").strip()
        if not w:
            continue
        key = w.lower()
        if key in seen:
            continue
        seen.add(key)
        if key in text_lower:
            overlap.append(w)

    if not overlap:
        return (
            f"\n\n⚠️ DECK ĐÃ CÓ {len(existing)} {label} (KHÔNG CÓ MỤC NÀO TRÙNG "
            f"với nội dung trên) → cứ trích xuất bình thường, không cần lo trùng."
        )

    if len(overlap) > _MAX_EXISTING_SHOWN:
        shown = overlap[:_MAX_EXISTING_SHOWN]
        note = f"\n(Còn {len(overlap) - _MAX_EXISTING_SHOWN} mục khác trùng nội dung; tổng deck {len(existing)} mục)"
    else:
        shown = overlap
        note = f"\n(Tổng deck {len(existing)} mục — chỉ liệt kê mục trùng với nội dung)"

    return (
        f"\n\n⚠️ {label} ĐÃ CÓ TRONG DECK — TUYỆT ĐỐI KHÔNG XUẤT RA:\n"
        + ", ".join(shown)
        + note
    )


def extract_vocabulary_with_ai(
    text: str,
    lang: str,
    custom_instruction: str = "",
    existing_words: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
    token_callback: Optional[Callable[[dict], None]] = None,
) -> list:
    """
    Gửi văn bản đến AI API để trích xuất từ vựng. Cache thông minh.

    Args:
        text: Văn bản nguồn
        lang: "japanese" hoặc "chinese"
        custom_instruction: Hướng dẫn bổ sung
        existing_words: Danh sách mặt chữ ĐÃ CÓ trong deck (để AI tránh trùng)
        progress_callback: Callback trạng thái
        force_refresh: Bỏ qua cache

    Returns:
        List các dict từ vựng (chỉ từ mới, không trùng deck)
    """
    existing_hash = _make_existing_hash(existing_words or [])

    # Cache
    if not force_refresh:
        cached = _ai_cache_get(text, lang, custom_instruction, existing_hash)
        if cached is not None:
            if progress_callback:
                progress_callback(f"📦 Cache: {len(cached)} từ vựng!")
            return cached

    cfg = get_api_config()
    if not cfg.get("api_key") and "localhost" not in cfg.get("api_base", ""):
        raise ValueError("⚠️ Chưa cấu hình API Key. Vào Cài đặt AI để nhập key.")

    system_prompt = _SYSTEM_PROMPTS.get(lang, _JAPANESE_SYSTEM_PROMPT)

    # Giới hạn text — có thể cấu hình (mặc định 45k ký tự, DeepSeek 64k context)
    max_chars = cfg.get("max_chars", 45000)
    if len(text) > max_chars:
        if progress_callback:
            progress_callback(f"📝 Văn bản {len(text)} ký tự → cắt còn {max_chars}")
        text = text[:max_chars]

    if progress_callback:
        progress_callback(f"🤖 Đang gọi {cfg['model']}...")

    # User message: text + existing words context (đã lọc gọn để tiết kiệm token)
    user_msg = f"Hãy trích xuất tất cả từ vựng từ văn bản sau:\n\n{text}"

    if existing_words and len(existing_words) > 0:
        user_msg += _format_existing_context(existing_words, text, label="TỪ")

    if custom_instruction.strip():
        user_msg += f"\n\nYÊU CẦU BỔ SUNG (ưu tiên cao nhất):\n{custom_instruction.strip()}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg.get("temperature", 0.3),
        "max_tokens": cfg.get("max_tokens", 8192),
    }
    _apply_reasoning_effort(payload, cfg)

    api_base = cfg["api_base"].rstrip("/")
    url = f"{api_base}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }

    if progress_callback:
        progress_callback("⏳ Đang chờ AI phản hồi...")

    _timeout = 600 if "reasoner" in cfg.get("model", "") else 300
    body = _http_post_json(url, payload, headers, timeout=_timeout,
                           progress_callback=progress_callback)

    result = json.loads(body)
    if "choices" not in result or len(result["choices"]) == 0:
        raise RuntimeError(f"❌ API không có kết quả.\n{body[:500]}")

    # Parse token usage & cost
    token_info = None
    usage = result.get("usage", {})
    if usage and usage.get("total_tokens"):
        token_info = _calculate_cost(
            cfg["model"],
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )
        if token_callback:
            try:
                token_callback(token_info)
            except Exception:
                pass

    msg = result["choices"][0]["message"]
    content = msg.get("content", "") or ""

    # DeepSeek Reasoner: nếu content rỗng, thử lấy reasoning_content
    if not content.strip():
        reasoning = msg.get("reasoning_content", "") or ""
        if reasoning.strip():
            content = reasoning.strip()
            if progress_callback:
                progress_callback("⚠️ Dùng reasoning_content (model không có content)...")
        else:
            raise RuntimeError("❌ Model không trả về nội dung (content rỗng).")

    if progress_callback:
        progress_callback("🔍 Đang parse JSON...")

    _check_truncated_output(content, progress_callback)
    vocab_list, comment = _parse_ai_json_with_comment(content)

    # Lọc bỏ từ trùng với existing_words (safety net)
    if existing_words:
        existing_set = set(w.lower().strip() for w in existing_words)
        original_count = len(vocab_list)
        vocab_list = [
            v for v in vocab_list
            if (v.get("front") or v.get("simplified") or "").lower().strip() not in existing_set
        ]
        if len(vocab_list) < original_count and progress_callback:
            progress_callback(f"🔍 Đã lọc {original_count - len(vocab_list)} từ trùng deck")

    if progress_callback:
        msg = f"✅ {len(vocab_list)} từ vựng mới!"
        if comment:
            msg += f"\n💬 {comment[:100]}"
        if token_info:
            msg += f"\n{_format_token_report(token_info)}"
        progress_callback(msg)

    # Lưu cache
    if vocab_list:
        _ai_cache_set(text, lang, custom_instruction, existing_hash, vocab_list)

    return vocab_list


def _parse_ai_json_with_comment(content: str) -> tuple:
    """Parse JSON, tách _comment"""
    comment = ""
    content = content.strip()

    if content.startswith("```"):
        lines = content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        data = json.loads(content)
        if isinstance(data, list):
            if data and isinstance(data[-1], dict) and "_comment" in data[-1] and len(data[-1]) == 1:
                comment = data[-1]["_comment"]
                data = data[:-1]
            return data, comment
        if isinstance(data, dict):
            if "_comment" in data:
                comment = data.pop("_comment")
            for v in data.values():
                if isinstance(v, list):
                    return v, comment
            return [data], comment
    except json.JSONDecodeError:
        pass

    array_match = re.search(r'\[.*\]', content, re.DOTALL)
    if array_match:
        try:
            data = json.loads(array_match.group(0))
            if isinstance(data, list):
                if data and isinstance(data[-1], dict) and "_comment" in data[-1] and len(data[-1]) == 1:
                    comment = data[-1]["_comment"]
                    data = data[:-1]
                return data, comment
        except json.JSONDecodeError:
            pass

    from .json_parser import safe_parse_json
    results = safe_parse_json(content)
    if results:
        return results, comment

    raise RuntimeError(
        "⚠️ Không parse được JSON — thường do KẾT QUẢ BỊ CẮT vì vượt giới hạn "
        "token output (DeepSeek ~8192/response).\n"
        "💡 Cách khắc phục: Vào Cài Đặt AI → giảm 'Độ dài xử lý mỗi lần gọi' "
        "xuống 8k-12k, rồi thử lại. Văn bản dài vẫn được xử lý hết (tự chia đoạn).\n"
        f"Nội dung nhận được:\n{content[:400]}"
    )


# ═══════════════════════════════════════════════════════════
#  SMART ANKI QUERY — truy vấn thông minh, không quét toàn bộ
# ═══════════════════════════════════════════════════════════

def query_anki_context(user_message: str, lang: str = "japanese") -> dict:
    """
    Thu thập ngữ cảnh Anki MỘT CÁCH THÔNG MINH dựa trên yêu cầu của người dùng.
    Chỉ query những gì liên quan, không quét toàn bộ database.
    
    Returns:
        dict với các key: decks, current_deck_stats, language, query_hint
    """
    context = {
        "language": lang,
        "decks": [],
        "current_deck_stats": {},
        "note": "",
    }
    
    try:
        from aqt import mw
        
        # 1. Lấy danh sách deck (nhẹ, chỉ tên + số lượng)
        deck_names = mw.col.decks.all_names()
        deck_list = []
        for name in deck_names:
            try:
                did = mw.col.decks.id(name)
                # Chỉ đếm số thẻ trong deck này (có giới hạn)
                count = mw.col.decks.card_count(did, include_subdecks=False)
                deck_list.append({"name": name, "card_count": count})
            except Exception:
                deck_list.append({"name": name, "card_count": "?"})
        context["decks"] = deck_list
        
        # 2. Nếu user đề cập đến deck cụ thể, lấy thêm stats
        msg_lower = user_message.lower()
        for d in deck_list:
            if d["name"].lower() in msg_lower:
                try:
                    did = mw.col.decks.id(d["name"])
                    # Stats cơ bản (không quét từng thẻ)
                    due_count = 0
                    new_count = 0
                    try:
                        # Due cards
                        due = mw.col.find_cards(f'"deck:{d["name"]}" is:due')
                        due_count = len(due) if due else 0
                        # New cards
                        new = mw.col.find_cards(f'"deck:{d["name"]}" is:new')
                        new_count = len(new) if new else 0
                    except Exception:
                        pass
                    
                    context["current_deck_stats"] = {
                        "name": d["name"],
                        "total_cards": d["card_count"],
                        "due_cards": due_count,
                        "new_cards": new_count,
                    }
                except Exception:
                    pass
                break
        
        # Nếu không tìm thấy deck cụ thể, dùng deck đầu tiên
        if not context["current_deck_stats"] and deck_list:
            d = deck_list[0]
            try:
                did = mw.col.decks.id(d["name"])
                due = mw.col.find_cards(f'"deck:{d["name"]}" is:due')
                due_count = len(due) if due else 0
                new = mw.col.find_cards(f'"deck:{d["name"]}" is:new')
                new_count = len(new) if new else 0
                context["current_deck_stats"] = {
                    "name": d["name"],
                    "total_cards": d["card_count"],
                    "due_cards": due_count,
                    "new_cards": new_count,
                }
            except Exception:
                pass
    
    except Exception as e:
        context["note"] = f"(Không thể truy vấn Anki: {e})"
    
    return context


def _build_anki_context_text(context: dict) -> str:
    """Xây dựng text mô tả ngữ cảnh Anki để gửi cho AI, kèm lịch sử import"""
    parts = []
    parts.append(f"🌐 Ngôn ngữ hiện tại: {context.get('language', 'japanese')}")
    
    decks = context.get("decks", [])
    if decks:
        parts.append(f"\n📦 Danh sách Deck ({len(decks)} deck):")
        for d in decks[:20]:  # Giới hạn 20 deck
            parts.append(f"   - {d['name']} ({d['card_count']} thẻ)")
        if len(decks) > 20:
            parts.append(f"   ... và {len(decks) - 20} deck khác")
    
    stats = context.get("current_deck_stats", {})
    if stats:
        parts.append(f"\n📊 Deck hiện tại ({stats.get('name', '?')}):")
        parts.append(f"   - Tổng: {stats.get('total_cards', '?')} thẻ")
        parts.append(f"   - Đến hạn: {stats.get('due_cards', '?')} thẻ")
        parts.append(f"   - Mới: {stats.get('new_cards', '?')} thẻ")
    
    note = context.get("note", "")
    if note:
        parts.append(f"\n⚠️ {note}")

    # Thêm lịch sử import (chỉ lấy summary, không chi tiết từng từ để tiết kiệm token)
    try:
        lang = context.get('language', 'japanese')
        history_text = get_history_summary_text(lang=lang, max_words_for_ai=30)
        if history_text:
            parts.append(f"\n{'═' * 40}")
            parts.append(history_text)
    except Exception:
        pass
    
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════
#  AI CHAT — giao tiếp tự do với AI, không cần text trích xuất
# ═══════════════════════════════════════════════════════════

_AI_ASSISTANT_SYSTEM_PROMPT = """Bạn là GIA SƯ NGÔN NGỮ cho người Việt — dạy tiếng Trung & Nhật. Bạn từng sống nhiều năm ở Trung Quốc và Nhật Bản, ấm áp, kiên nhẫn, có gu. Bạn không phải sách giáo khoa — bạn là người thật. Bạn ghét ví dụ vô hồn, viết như người bản xứ thực sự nói/viết: có cảm xúc, có ngữ cảnh, có lý do để câu đó tồn tại.

Bạn cũng có quyền truy cập hệ thống Anki của người dùng (deck, lịch sử import bên dưới) để biết từ nào đã có, phân tích phân bố cấp độ/chủ đề, và đề xuất từ mới.

TÍNH CÁCH:
- Như anh/chị đi trước chia sẻ kinh nghiệm, không robot.
- Khi sửa lỗi: khen điều đúng trước, góp ý sau. Không phán xét.
- Có thể hài hước nhẹ, ví von đời thường để dễ nhớ.
- Súc tích, vào thẳng ví dụ. Tránh lan man lý thuyết trừ khi được yêu cầu.

NGUYÊN TẮC VÀNG KHI TẠO VÍ DỤ:
1. Ví dụ phải có ngữ cảnh thật: quán cà phê, tin nhắn, than thở với đồng nghiệp, post mạng xã hội, cãi nhau nhẹ... Đừng ngại cho ví dụ có cảm xúc (vui, bực, tiếc, mỉa mai, ngại).
2. Ưu tiên khẩu ngữ tự nhiên hơn văn viết. Dùng từ đệm/trợ từ ngữ khí đúng chỗ: 啊、呢、吧、了、って、よね、じゃん...
3. Sau mỗi ví dụ, giải thích "vibe": thân mật hay lịch sự? Dùng sai ngữ cảnh sẽ kỳ thế nào?
4. So sánh từ gần nghĩa: tại sao chọn từ này không phải từ kia? (đây là phần khó tự học nhất)
5. 2-4 ví dụ chất lượng > 10 ví dụ hời hợt. Không gây ngợp.
6. Tự điều chỉnh độ khó theo trình độ. Nếu không rõ → hỏi hoặc đưa mức trung cấp.
7. Chủ động nhắc lỗi người Việt hay mắc (了 vs quá khứ, は/が, 的/得/地, âm Hán Việt...).

ĐỊNH DẠNG ƯU TIÊN (khi giải thích từ/cấu trúc):
[Chữ Hán] (Pinyin) → Nghĩa Việt  |  [Kanji] (Furigana) → Nghĩa Việt
📍 Ngữ cảnh: [tình huống cụ thể]
💬 Sắc thái: [thân mật/lịch sự/trang trọng + lưu ý nếu dùng sai]
⚠ Với tiếng Trung: MỌI câu ví dụ trong chat PHẢI kèm pinyin bên dưới. Không có ngoại lệ.
⚠ CẤU TRÚC NGỮ PHÁP LUÔN viết NGUYÊN CHỮ: tiếng Nhật dùng kanji + kana (VD 〜てもいい、〜ばいい、〜そうだ), tiếng Trung dùng Hán tự (VD 把字句、是...的、越来越). TUYỆT ĐỐI KHÔNG viết cấu trúc bằng Pinyin (bǎ...) hay Romaji. Pinyin/Furigana chỉ là dòng phụ chú CÁCH ĐỌC bên dưới, không thay thế chữ gốc.

ANKI INTEGRATION:
- Dùng dữ liệu ngữ cảnh bên dưới để phân tích và đề xuất.
- Khi đề xuất từ vựng mới: CHỈ từ chưa có, kèm JSON block (```json...```) ở cuối để import 1-click.
- Format JSON đúng mẫu: Japanese {front,furigana,meaning,sino-vietnamese,jlptlevel,topic,example,example_vn,example_2,example_2_vn} | Chinese {simplified,traditional,pinyin,meaning,sino_vietnamese,hsk_level,topic,example,example_pinyin,example_vn,example_2,example_2_pinyin,example_2_vn}.
- Khi đề xuất NGỮ PHÁP: dùng mẫu Japanese Grammar {pattern,reading,meaning,jlptlevel,topic,usage,explanation,example,example_vn,example_2,example_2_vn} | Chinese Grammar {pattern,pinyin,meaning,hsk_level,topic,usage,explanation,example,example_pinyin,example_vn,example_2,example_2_pinyin,example_2_vn}. Trường pattern LUÔN là CHỮ GỐC (kanji/hanzi), không phải pinyin/romaji.
- BẮT BUỘC với tiếng Trung: MỌI từ phải có example_pinyin và example_2_pinyin — KHÔNG ĐƯỢC BỎ TRỐNG. Pinyin phải chuẩn, có dấu thanh đầy đủ.
- Điền ĐẦY ĐỦ tất cả các trường cho từng từ, không bỏ sót trường nào.
- Không tự ý quét/truy vấn thêm ngoài dữ liệu có sẵn.

Trả lời bằng TIẾNG VIỆT, thân thiện."""


def chat_with_ai(
    user_message: str,
    lang: str = "japanese",
    conversation_history: Optional[List[dict]] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Gửi tin nhắn đến AI và nhận phản hồi. AI có ngữ cảnh Anki.
    
    Args:
        user_message: Tin nhắn của người dùng
        lang: "japanese" hoặc "chinese"
        conversation_history: Lịch sử hội thoại (list of {"role":"user"/"assistant", "content":"..."})
        progress_callback: Callback trạng thái
    
    Returns:
        dict với keys: "reply" (text phản hồi), "vocab_json" (nếu AI xuất từ vựng), "error"
    """
    cfg = get_api_config()
    if not cfg.get("api_key") and "localhost" not in cfg.get("api_base", ""):
        return {"reply": "", "vocab_json": None, "error": "⚠️ Chưa cấu hình API Key. Vào Cài đặt AI để nhập key."}
    
    # Thu thập ngữ cảnh Anki THÔNG MINH dựa trên yêu cầu
    if progress_callback:
        progress_callback("🔍 Đang thu thập ngữ cảnh Anki...")
    
    context = query_anki_context(user_message, lang)
    context_text = _build_anki_context_text(context)
    
    if progress_callback:
        progress_callback(f"🤖 Đang gọi {cfg['model']}...")
    
    # Xây dựng messages
    system_content = _AI_ASSISTANT_SYSTEM_PROMPT + "\n\n" + "═" * 50 + "\n"
    system_content += "THÔNG TIN HỆ THỐNG ANKI (chỉ dùng dữ liệu này):\n" + context_text
    
    messages = [{"role": "system", "content": system_content}]
    
    # Thêm lịch sử hội thoại (giới hạn 10 tin gần nhất để tiết kiệm token)
    if conversation_history:
        for msg in conversation_history[-20:]:
            messages.append(msg)
    
    messages.append({"role": "user", "content": user_message})
    
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg.get("temperature", 0.3),
        "max_tokens": cfg.get("max_tokens", 8192),
    }
    _apply_reasoning_effort(payload, cfg)
    
    api_base = cfg["api_base"].rstrip("/")
    url = f"{api_base}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    
    if progress_callback:
        progress_callback("⏳ Đang chờ AI phản hồi...")

    _timeout = 600 if "reasoner" in cfg.get("model", "") else 300
    try:
        body = _http_post_json(url, payload, headers, timeout=_timeout,
                               progress_callback=progress_callback)
    except RuntimeError as e:
        return {"reply": "", "vocab_json": None, "token_info": None, "error": str(e)}
    
    result = json.loads(body)
    if "choices" not in result or len(result["choices"]) == 0:
        return {"reply": "", "vocab_json": None, "token_info": None, "error": f"❌ API không có kết quả.\n{body[:500]}"}
    
    # Parse token usage & cost
    token_info = None
    usage = result.get("usage", {})
    if usage and usage.get("total_tokens"):
        token_info = _calculate_cost(
            cfg["model"],
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )
    
    msg = result["choices"][0]["message"]
    content = msg.get("content", "") or ""
    
    # DeepSeek Reasoner: nếu content rỗng, thử lấy từ reasoning_content
    if not content.strip():
        reasoning = msg.get("reasoning_content", "") or ""
        if reasoning.strip():
            # Dùng reasoning_content làm phản hồi (thường là quá trình suy nghĩ)
            content = f"[Model suy nghĩ]\n{reasoning.strip()}\n\n⚠️ Model không trả về kết quả cuối cùng."
            if progress_callback:
                progress_callback("⚠️ Model chỉ trả về reasoning, không có kết quả.")
        else:
            return {"reply": "", "vocab_json": None, "token_info": None, "error": "❌ Model không trả về nội dung (content rỗng)."}
    
    # Tách JSON từ vựng nếu có
    reply_text = content
    vocab_json = None
    
    # Tìm JSON block trong phản hồi
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, list) and len(parsed) > 0:
                vocab_json = parsed
                # Xóa JSON block khỏi reply
                reply_text = content[:json_match.start()] + content[json_match.end():]
                reply_text = reply_text.strip()
        except Exception:
            pass
    
    # Nếu không có JSON block, thử tìm JSON array trực tiếp (non-greedy)
    if not vocab_json:
        array_match = re.search(r'\[\s*\{.*?\}\s*\]', content, re.DOTALL)
        if array_match:
            try:
                parsed = json.loads(array_match.group(0))
                if isinstance(parsed, list) and len(parsed) > 0:
                    vocab_json = parsed
                    reply_text = content[:array_match.start()] + content[array_match.end():]
                    reply_text = reply_text.strip()
            except Exception:
                pass
    
    if progress_callback:
        end_msg = "✅ Hoàn tất!"
        if token_info:
            end_msg += f"\n{_format_token_report(token_info)}"
        progress_callback(end_msg)
    
    return {"reply": reply_text or content, "vocab_json": vocab_json, "token_info": token_info, "error": None}


# ═══════════════════════════════════════════════════════════
#  XỬ LÝ VĂN BẢN DÀI
# ═══════════════════════════════════════════════════════════

def extract_vocabulary_long_text(
    text: str,
    lang: str,
    custom_instruction: str = "",
    existing_words: Optional[List[str]] = None,
    chunk_size: Optional[int] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
) -> list:
    """Xử lý văn bản dài: chia đoạn, gọi AI, loại trùng, tổng hợp token."""
    if chunk_size is None:
        chunk_size = get_api_config().get("chunk_size", 8000)
    if len(text) <= chunk_size:
        return extract_vocabulary_with_ai(
            text, lang, custom_instruction, existing_words,
            progress_callback, force_refresh,
        )

    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    if progress_callback:
        progress_callback(f"📦 {len(chunks)} đoạn, đang xử lý...")

    all_vocab = []
    seen = set()
    existing_set = set(w.lower().strip() for w in (existing_words or []))
    # Từ đã trích ở đoạn trước → bổ sung vào danh sách "đã có" cho đoạn sau
    # (giúp AI không trích trùng qua biên giới đoạn → chất lượng + tiết kiệm output)
    prior_fronts = []

    # Bộ gộp token/chi phí toàn bộ lần chạy
    agg = {
        "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
        "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0,
    }

    def _acc(ti: dict):
        agg["prompt_tokens"] += ti.get("prompt_tokens", 0)
        agg["completion_tokens"] += ti.get("completion_tokens", 0)
        agg["total_tokens"] += ti.get("total_tokens", 0)
        agg["input_cost"] += ti.get("input_cost", 0)
        agg["output_cost"] += ti.get("output_cost", 0)
        agg["total_cost"] += ti.get("total_cost", 0)

    for idx, chunk in enumerate(chunks):
        if progress_callback:
            progress_callback(f"🔄 Đoạn {idx + 1}/{len(chunks)}...")

        try:
            combined_existing = (existing_words or []) + prior_fronts
            vocab_chunk = extract_vocabulary_with_ai(
                chunk, lang, custom_instruction, combined_existing,
                progress_callback=None, force_refresh=force_refresh,
                token_callback=_acc,
            )
            for item in vocab_chunk:
                if not isinstance(item, dict):
                    continue
                key = (item.get("front") or item.get("simplified") or "").strip().lower()
                if key and key not in seen and key not in existing_set:
                    seen.add(key)
                    all_vocab.append(item)
                    prior_fronts.append(key)
            # Giới hạn danh sách prior để tránh phình prompt
            if len(prior_fronts) > 400:
                prior_fronts = prior_fronts[-400:]
        except Exception as e:
            if progress_callback:
                progress_callback(f"⚠️ Lỗi đoạn {idx + 1}: {e}")

    if progress_callback:
        if agg["total_tokens"] > 0:
            progress_callback(
                f"✅ Tổng: {len(all_vocab)} từ mới | "
                f"🔢 {agg['total_tokens']:,} tokens (in {agg['prompt_tokens']:,} + out {agg['completion_tokens']:,}) | "
                f"💰 ${agg['total_cost']:.4f}"
            )
        else:
            progress_callback(f"✅ Tổng: {len(all_vocab)} từ mới")

    return all_vocab


# ═══════════════════════════════════════════════════════════
#  GRAMMAR EXTRACTION — trích xuất NGỮ PHÁP qua AI
#  (Note Type ngữ pháp riêng, dùng prompt riêng)
# ═══════════════════════════════════════════════════════════

def extract_grammar_with_ai(
    text: str,
    lang: str,
    custom_instruction: str = "",
    existing_patterns: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
    token_callback: Optional[Callable[[dict], None]] = None,
) -> list:
    """
    Gửi văn bản đến AI API để trích xuất CẤU TRÚC NGỮ PHÁP (khác từ vựng).

    Args:
        text: Văn bản nguồn
        lang: "japanese" hoặc "chinese"
        custom_instruction: Hướng dẫn bổ sung
        existing_patterns: Danh sách pattern ĐÃ CÓ trong deck (để AI tránh trùng)
        progress_callback: Callback trạng thái
        force_refresh: Bỏ qua cache

    Returns:
        List các dict ngữ pháp (chỉ pattern mới, không trùng deck)
    """
    existing_hash = _make_existing_hash(existing_patterns or [])

    # Cache
    if not force_refresh:
        cached = _ai_cache_get(text, lang, custom_instruction, existing_hash, kind="grammar")
        if cached is not None:
            if progress_callback:
                progress_callback(f"📦 Cache: {len(cached)} cấu trúc ngữ pháp!")
            return cached

    cfg = get_api_config()
    if not cfg.get("api_key") and "localhost" not in cfg.get("api_base", ""):
        raise ValueError("⚠️ Chưa cấu hình API Key. Vào Cài đặt AI để nhập key.")

    system_prompt = _GRAMMAR_SYSTEM_PROMPTS.get(lang, _GRAMMAR_SYSTEM_PROMPTS["japanese"])

    # Giới hạn text — có thể cấu hình (mặc định 45k ký tự, DeepSeek 64k context)
    max_chars = cfg.get("max_chars", 45000)
    if len(text) > max_chars:
        if progress_callback:
            progress_callback(f"📝 Văn bản {len(text)} ký tự → cắt còn {max_chars}")
        text = text[:max_chars]

    if progress_callback:
        progress_callback(f"🤖 Đang gọi {cfg['model']}...")

    # User message: text + existing patterns context (đã lọc gọn để tiết kiệm token)
    user_msg = f"Hãy trích xuất tất cả cấu trúc ngữ pháp từ văn bản sau:\n\n{text}"

    if existing_patterns and len(existing_patterns) > 0:
        user_msg += _format_existing_context(existing_patterns, text, label="CẤU TRÚC NGỮ PHÁP")

    if custom_instruction.strip():
        user_msg += f"\n\nYÊU CẦU BỔ SUNG (ưu tiên cao nhất):\n{custom_instruction.strip()}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg.get("temperature", 0.3),
        "max_tokens": cfg.get("max_tokens", 8192),
    }
    _apply_reasoning_effort(payload, cfg)

    api_base = cfg["api_base"].rstrip("/")
    url = f"{api_base}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }

    if progress_callback:
        progress_callback("⏳ Đang chờ AI phản hồi...")

    _timeout = 600 if "reasoner" in cfg.get("model", "") else 300
    body = _http_post_json(url, payload, headers, timeout=_timeout,
                           progress_callback=progress_callback)

    result = json.loads(body)
    if "choices" not in result or len(result["choices"]) == 0:
        raise RuntimeError(f"❌ API không có kết quả.\n{body[:500]}")

    # Parse token usage & cost
    token_info = None
    usage = result.get("usage", {})
    if usage and usage.get("total_tokens"):
        token_info = _calculate_cost(
            cfg["model"],
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )
        if token_callback:
            try:
                token_callback(token_info)
            except Exception:
                pass

    msg = result["choices"][0]["message"]
    content = msg.get("content", "") or ""

    # DeepSeek Reasoner: nếu content rỗng, thử lấy reasoning_content
    if not content.strip():
        reasoning = msg.get("reasoning_content", "") or ""
        if reasoning.strip():
            content = reasoning.strip()
            if progress_callback:
                progress_callback("⚠️ Dùng reasoning_content (model không có content)...")
        else:
            raise RuntimeError("❌ Model không trả về nội dung (content rỗng).")

    if progress_callback:
        progress_callback("🔍 Đang parse JSON...")

    _check_truncated_output(content, progress_callback)
    grammar_list, comment = _parse_ai_json_with_comment(content)

    # Chỉ giữ các item có pattern
    grammar_list = [
        g for g in grammar_list
        if isinstance(g, dict) and (g.get("pattern") or "").strip()
    ]

    # Lọc bỏ pattern trùng với existing_patterns (safety net)
    if existing_patterns:
        existing_set = set(p.lower().strip() for p in existing_patterns)
        original_count = len(grammar_list)
        grammar_list = [
            g for g in grammar_list
            if (g.get("pattern") or "").strip().lower() not in existing_set
        ]
        if len(grammar_list) < original_count and progress_callback:
            progress_callback(f"🔍 Đã lọc {original_count - len(grammar_list)} cấu trúc trùng deck")

    if progress_callback:
        msg2 = f"✅ {len(grammar_list)} cấu trúc ngữ pháp mới!"
        if comment:
            msg2 += f"\n💬 {comment[:100]}"
        if token_info:
            msg2 += f"\n{_format_token_report(token_info)}"
        progress_callback(msg2)

    # Lưu cache
    if grammar_list:
        _ai_cache_set(text, lang, custom_instruction, existing_hash, grammar_list, kind="grammar")

    return grammar_list


def extract_grammar_long_text(
    text: str,
    lang: str,
    custom_instruction: str = "",
    existing_patterns: Optional[List[str]] = None,
    chunk_size: Optional[int] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
) -> list:
    """Xử lý văn bản dài: chia đoạn, gọi AI trích ngữ pháp, loại trùng, tổng hợp token."""
    if chunk_size is None:
        chunk_size = get_api_config().get("chunk_size", 8000)
    if len(text) <= chunk_size:
        return extract_grammar_with_ai(
            text, lang, custom_instruction, existing_patterns,
            progress_callback, force_refresh,
        )

    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    if progress_callback:
        progress_callback(f"📦 {len(chunks)} đoạn, đang xử lý ngữ pháp...")

    all_grammar = []
    seen = set()
    existing_set = set(p.lower().strip() for p in (existing_patterns or []))
    # Dedup theo (pattern|meaning) → cho phép cùng pattern, khác nghĩa = thẻ riêng

    agg = {
        "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
        "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0,
    }

    def _acc(ti: dict):
        agg["prompt_tokens"] += ti.get("prompt_tokens", 0)
        agg["completion_tokens"] += ti.get("completion_tokens", 0)
        agg["total_tokens"] += ti.get("total_tokens", 0)
        agg["input_cost"] += ti.get("input_cost", 0)
        agg["output_cost"] += ti.get("output_cost", 0)
        agg["total_cost"] += ti.get("total_cost", 0)

    for idx, chunk in enumerate(chunks):
        if progress_callback:
            progress_callback(f"🔄 Đoạn {idx + 1}/{len(chunks)}...")

        try:
            grammar_chunk = extract_grammar_with_ai(
                chunk, lang, custom_instruction, existing_patterns,
                progress_callback=None, force_refresh=force_refresh,
                token_callback=_acc,
            )
            for item in grammar_chunk:
                if not isinstance(item, dict):
                    continue
                pat = (item.get("pattern") or "").strip().lower()
                mean = (item.get("meaning") or "").strip().lower()
                key = f"{pat}|{mean}"
                if pat and key not in seen and pat not in existing_set:
                    seen.add(key)
                    all_grammar.append(item)
        except Exception as e:
            if progress_callback:
                progress_callback(f"⚠️ Lỗi đoạn {idx + 1}: {e}")

    if progress_callback:
        if agg["total_tokens"] > 0:
            progress_callback(
                f"✅ Tổng: {len(all_grammar)} cấu trúc ngữ pháp mới | "
                f"🔢 {agg['total_tokens']:,} tokens (in {agg['prompt_tokens']:,} + out {agg['completion_tokens']:,}) | "
                f"💰 ${agg['total_cost']:.4f}"
            )
        else:
            progress_callback(f"✅ Tổng: {len(all_grammar)} cấu trúc ngữ pháp mới")

    return all_grammar


# ═══════════════════════════════════════════════════════════
#  IMPORT HISTORY — Lịch sử nhập JSON/tài liệu
#  Lưu cache từ vựng đã import để AI truy cập mà không cần
#  quét toàn bộ database Anki. Tiết kiệm token.
# ═══════════════════════════════════════════════════════════

_HISTORY_PATH = os.path.join(_CONFIG_DIR, "import_history.json")
_HISTORY_VERSION = 1
_HISTORY_SCAN_TTL = 24 * 3600  # TTL 24h cho full scan


def _load_history() -> dict:
    """Đọc file lịch sử import"""
    if os.path.exists(_HISTORY_PATH):
        try:
            with open(_HISTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("version") == _HISTORY_VERSION:
                return data
        except Exception:
            pass
    return {
        "version": _HISTORY_VERSION,
        "last_full_scan": None,
        "entries": {},       # {lang: {front_lower: {meaning, furigana/pinyin, level, deck, imported_at, source}}}
        "import_sessions": [],  # [{timestamp, count, deck, source, lang}]
    }


def _save_history(data: dict):
    """Ghi file lịch sử import"""
    try:
        with open(_HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning("Lỗi ghi import_history: %s", e)


def clear_import_history():
    """Xóa toàn bộ lịch sử import từ vựng"""
    if os.path.exists(_HISTORY_PATH):
        try:
            os.remove(_HISTORY_PATH)
            return True
        except Exception as e:
            logger.warning("Lỗi xóa import_history: %s", e)
            return False
    return True


def init_import_history(force_rescan: bool = False) -> dict:
    """
    Khởi tạo lịch sử import: quét toàn bộ deck Anki để thu thập
    từ vựng hiện có. Chỉ quét nếu:
    - File lịch sử chưa tồn tại
    - TTL đã hết (24h)
    - force_rescan = True

    Returns:
        dict lịch sử sau khi khởi tạo
    """
    data = _load_history()
    last_scan = data.get("last_full_scan")

    # Kiểm tra có cần rescan không
    need_scan = force_rescan
    if not need_scan and last_scan:
        try:
            if time.time() - last_scan > _HISTORY_SCAN_TTL:
                need_scan = True
        except Exception:
            need_scan = True
    if not need_scan and not last_scan:
        need_scan = True

    # Nếu đã có entries, chỉ rescan nếu cần
    if not need_scan and data.get("entries"):
        return data

    if need_scan:
        try:
            from aqt import mw
            from Language import LANG_CONFIG

            if not data.get("entries"):
                data["entries"] = {}

            total_scanned = 0
            for lang_key, cfg in LANG_CONFIG.items():
                model_name = cfg.get("model_name", "")
                front_field = cfg.get("front_field", "")

                if not model_name or not front_field:
                    continue

                if lang_key not in data["entries"]:
                    data["entries"][lang_key] = {}

                try:
                    note_ids = mw.col.find_notes(f'"note:{model_name}"')
                    if not note_ids:
                        continue

                    existing_keys = set(data["entries"][lang_key].keys())
                    # Lấy field index từ model (1 lần)
                    model = mw.col.models.by_name(model_name)
                    if not model:
                        continue
                    field_names = [f["name"] for f in model["flds"]]
                    front_idx = field_names.index(front_field) if front_field in field_names else 0
                    meaning_idx = field_names.index("Meaning") if "Meaning" in field_names else -1
                    furi_idx = field_names.index(cfg.get("furi_label", "")) if cfg.get("furi_label", "") in field_names else -1
                    level_idx = field_names.index(cfg.get("level_field", "")) if cfg.get("level_field", "") in field_names else -1

                    # Batch query: lấy flds trực tiếp từ SQL (tránh N+1 get_note)
                    batch_size = 200
                    for i in range(0, len(note_ids), batch_size):
                        batch = note_ids[i:i + batch_size]
                        try:
                            placeholders = ",".join("?" * len(batch))
                            rows = mw.col.db.all(
                                f"SELECT id, flds FROM notes WHERE id IN ({placeholders})", *batch
                            )
                        except Exception:
                            rows = []
                            for nid in batch:
                                try:
                                    note = mw.col.get_note(nid)
                                    rows.append((nid, "\x1f".join(str(note[f]) for f in field_names)))
                                except Exception:
                                    continue

                        for nid, flds_raw in rows:
                            try:
                                fields = flds_raw.split("\x1f")
                                if front_idx >= len(fields):
                                    continue
                                front = fields[front_idx].strip()
                                if not front:
                                    continue

                                front_lower = front.lower()
                                # Nếu đã có trong lịch sử, bỏ qua
                                if front_lower in existing_keys:
                                    continue

                                # Thu thập thông tin
                                entry = {
                                    "front": front,
                                    "front_lower": front_lower,
                                    "meaning": "",
                                    "level": "",
                                    "deck": "",
                                    "imported_at": time.time(),
                                    "source": "deck_scan",
                                }

                                # Lấy meaning
                                if meaning_idx >= 0 and meaning_idx < len(fields):
                                    entry["meaning"] = fields[meaning_idx].strip()

                                # Lấy furigana/pinyin
                                if furi_idx >= 0 and furi_idx < len(fields):
                                    val = fields[furi_idx].strip()
                                    if val:
                                        if lang_key == "japanese":
                                            entry["furigana"] = val
                                        else:
                                            entry["pinyin"] = val

                                # Lấy cấp độ
                                if level_idx >= 0 and level_idx < len(fields):
                                    entry["level"] = fields[level_idx].strip()

                                data["entries"][lang_key][front_lower] = entry
                                total_scanned += 1
                            except Exception:
                                continue
                except Exception as e:
                    logger.warning("Lỗi quét deck %s: %s", lang_key, e)

            data["last_full_scan"] = time.time()
            data["_scan_summary"] = {
                "total_words_scanned": total_scanned,
                "languages": list(data["entries"].keys()),
                "word_counts": {k: len(v) for k, v in data["entries"].items()},
            }
            _save_history(data)
            logger.info("Import history initialized: %s words scanned", total_scanned)
        except Exception as e:
            logger.warning("Lỗi init_import_history: %s", e)

    return data


def add_to_import_history(vocab_list: list, lang: str, deck_name: str = "", source: str = "manual"):
    """
    Ghi nhận từ vựng mới vào lịch sử sau mỗi lần import.

    Args:
        vocab_list: Danh sách dict từ vựng
        lang: "japanese" hoặc "chinese"
        deck_name: Tên deck được import vào
        source: Nguồn gốc ("manual", "ai_extract", "ai_chat", "file_import")
    """
    if not vocab_list:
        return

    data = _load_history()
    if not data.get("entries"):
        data["entries"] = {}
    if lang not in data["entries"]:
        data["entries"][lang] = {}

    now = time.time()
    added_count = 0

    for item in vocab_list:
        if not isinstance(item, dict):
            continue

        front = (item.get("front") or item.get("simplified") or "").strip()
        if not front:
            continue

        front_lower = front.lower()

        entry = {
            "front": front,
            "front_lower": front_lower,
            "meaning": str(item.get("meaning", "")).strip(),
            "level": str(item.get("jlptlevel") or item.get("hsk_level") or "").strip(),
            "deck": deck_name,
            "imported_at": now,
            "source": source,
        }

        # Furigana / Pinyin
        if lang == "japanese":
            entry["furigana"] = str(item.get("furigana", "")).strip()
        else:
            entry["pinyin"] = str(item.get("pinyin", "")).strip()
            entry["traditional"] = str(item.get("traditional", "")).strip()

        # Topic
        entry["topic"] = str(item.get("topic", "")).strip()

        data["entries"][lang][front_lower] = entry
        added_count += 1

    # Ghi phiên import
    if not data.get("import_sessions"):
        data["import_sessions"] = []
    data["import_sessions"].append({
        "timestamp": now,
        "count": added_count,
        "deck": deck_name,
        "source": source,
        "lang": lang,
    })
    # Giới hạn 100 phiên gần nhất
    if len(data["import_sessions"]) > 100:
        data["import_sessions"] = data["import_sessions"][-100:]

    _save_history(data)
    logger.info("Import history: +%s words (%s, %s)", added_count, lang, source)


def get_import_history(lang: str = None, limit: int = 2000) -> dict:
    """
    Lấy lịch sử từ vựng đã import để cung cấp cho AI.

    Args:
        lang: Lọc theo ngôn ngữ (None = tất cả)
        limit: Giới hạn số từ trả về (để tiết kiệm token)

    Returns:
        dict với keys: total_count, words (list), sessions, summary
    """
    data = _load_history()
    entries = data.get("entries", {})

    result = {
        "total_count": 0,
        "words": [],
        "sessions": data.get("import_sessions", [])[-20:],  # 20 phiên gần nhất
        "summary": {},
    }

    # Tổng hợp
    for l, words in entries.items():
        if lang and l != lang:
            continue
        result["summary"][l] = {
            "count": len(words),
            "levels": {},
            "topics": {},
        }
        result["total_count"] += len(words)

        # Thống kê cấp độ & chủ đề
        for w in words.values():
            lvl = w.get("level", "")
            if lvl:
                result["summary"][l]["levels"][lvl] = result["summary"][l]["levels"].get(lvl, 0) + 1
            topic = w.get("topic", "")
            if topic:
                result["summary"][l]["topics"][topic] = result["summary"][l]["topics"].get(topic, 0) + 1

    # Lấy danh sách từ (có giới hạn)
    all_words = []
    for l, words in entries.items():
        if lang and l != lang:
            continue
        for w in words.values():
            all_words.append({
                "front": w.get("front", ""),
                "meaning": w.get("meaning", ""),
                "level": w.get("level", ""),
                "deck": w.get("deck", ""),
                "lang": l,
                "imported_at": w.get("imported_at", 0),
            })

    # Sắp xếp theo thời gian import (mới nhất trước)
    all_words.sort(key=lambda x: x.get("imported_at", 0), reverse=True)
    result["words"] = all_words[:limit]

    return result


def search_import_history(query: str, lang: str = None, limit: int = 50) -> list:
    """
    Tìm kiếm trong lịch sử import.

    Args:
        query: Từ khóa tìm kiếm
        lang: Lọc theo ngôn ngữ
        limit: Giới hạn kết quả

    Returns:
        List các từ khớp
    """
    query_lower = query.lower().strip()
    if not query_lower:
        return []

    data = _load_history()
    entries = data.get("entries", {})
    results = []

    for l, words in entries.items():
        if lang and l != lang:
            continue
        for w in words.values():
            front = w.get("front", "").lower()
            meaning = w.get("meaning", "").lower()
            furi = w.get("furigana", "").lower()
            pinyin = w.get("pinyin", "").lower()

            if (query_lower in front or query_lower in meaning
                    or query_lower in furi or query_lower in pinyin):
                results.append({
                    "front": w.get("front", ""),
                    "meaning": w.get("meaning", ""),
                    "level": w.get("level", ""),
                    "deck": w.get("deck", ""),
                    "lang": l,
                })

        if len(results) >= limit:
            break

    return results[:limit]


def get_history_summary_text(lang: str = None, max_words_for_ai: int = 50) -> str:
    """
    Tạo text tóm tắt lịch sử để gửi cho AI (tiết kiệm token).
    Tách biệt rõ ràng Japanese và Chinese.

    Args:
        lang: Ngôn ngữ cần tóm tắt (None = cả hai)
        max_words_for_ai: Số từ tối đa gửi cho AI

    Returns:
        Text mô tả lịch sử
    """
    if lang:
        # Chỉ lấy 1 ngôn ngữ
        history = get_import_history(lang=lang, limit=max_words_for_ai)
        return _build_single_lang_summary(history, lang)
    else:
        # Lấy cả hai, tách biệt rõ ràng
        parts = []
        parts.append("📚 TỔNG QUAN LỊCH SỬ IMPORT (TÁCH BIỆT THEO NGÔN NGỮ)")
        parts.append("═" * 50)

        for l in ["japanese", "chinese"]:
            h = get_import_history(lang=l, limit=max_words_for_ai // 2)
            summary_text = _build_single_lang_summary(h, l)
            if summary_text:
                parts.append(summary_text)
                parts.append("")  # blank line between languages

        return "\n".join(parts)


def _build_single_lang_summary(history: dict, lang: str) -> str:
    """Xây dựng text tóm tắt cho MỘT ngôn ngữ"""
    parts = []

    if lang == "japanese":
        parts.append("🇯🇵 TIẾNG NHẬT (Japanese)")
    else:
        parts.append("🇨🇳 TIẾNG TRUNG (Chinese)")

    summary = history.get("summary", {}).get(lang, {})
    parts.append(f"   📊 Tổng: {summary.get('count', 0)} từ đã import")

    if summary.get("levels"):
        levels_str = ", ".join(f"{k}:{v}" for k, v in sorted(summary["levels"].items()))
        parts.append(f"   🎓 Cấp độ: {levels_str}")

    if summary.get("topics"):
        top_topics = sorted(summary["topics"].items(), key=lambda x: -x[1])[:5]
        topics_str = ", ".join(f"{k}({v})" for k, v in top_topics)
        parts.append(f"   🏷 Chủ đề: {topics_str}")

    # Từ gần đây
    words = history.get("words", [])
    if words:
        parts.append(f"   📝 {min(len(words), 30)} từ gần nhất:")
        for w in words[:30]:
            lvl = f" [{w.get('level', '')}]" if w.get("level") else ""
            parts.append(f"      • {w['front']} = {w['meaning']}{lvl}")

    return "\n".join(parts)