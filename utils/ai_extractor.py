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
# SSL context không verify (cho localhost/Ollama)
_SSL_CONTEXT = ssl.create_default_context()
_SSL_CONTEXT.check_hostname = False
_SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# Connection pool cache: host → (HTTPSConnection | HTTPConnection)
_CONN_POOL = {}


def _http_post_json(url: str, payload: dict, headers: dict,
                    timeout: int = 300,
                    progress_callback: Optional[Callable[[str], None]] = None,
                    should_abort: Optional[Callable[[], bool]] = None) -> str:
    """Gửi POST request với JSON body, trả về response body dạng string.

    Dùng http.client thay vì urllib.request để:
    - Connection reuse (HTTP/1.1 keep-alive)
    - Đọc response theo chunk → progress callback
    - Timeout thực sự hoạt động
    """
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path + ("?" + parsed.query if parsed.query else "")
    use_ssl = parsed.scheme == "https"

    # Lấy hoặc tạo connection từ pool
    pool_key = f"{host}:{port}"
    conn = _CONN_POOL.get(pool_key)
    if conn is None:
        if use_ssl:
            conn = http.client.HTTPSConnection(host, port, timeout=timeout, context=_SSL_CONTEXT)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=timeout)
        _CONN_POOL[pool_key] = conn

    body_bytes = json.dumps(payload).encode("utf-8")
    headers["Content-Length"] = str(len(body_bytes))

    last_error = None
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                # Tạo connection mới nếu retry
                if use_ssl:
                    conn = http.client.HTTPSConnection(host, port, timeout=timeout, context=_SSL_CONTEXT)
                else:
                    conn = http.client.HTTPConnection(host, port, timeout=timeout)
                _CONN_POOL[pool_key] = conn

            conn.request("POST", path, body=body_bytes, headers=headers)
            resp = conn.getresponse()

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
    if not os.path.exists(_CACHE_DIR):
        os.makedirs(_CACHE_DIR)


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
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def get_api_config() -> dict:
    defaults = {
        "api_key": "",
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "max_tokens": 8192,
    }
    cfg = _load_config()
    for k, v in defaults.items():
        cfg.setdefault(k, v)
    # Decrypt API key nếu đã được encrypt
    if cfg.get("api_key") and not cfg["api_key"].startswith("sk-"):
        cfg["api_key"] = _decrypt_api_key(cfg["api_key"])
    return cfg


def save_api_config(api_key: str, api_base: str, model: str, temperature: float = 0.3):
    # Sanitize input
    api_base = api_base.strip().rstrip("/")
    if api_base and not api_base.startswith(("http://", "https://")):
        api_base = "https://" + api_base
    model = model.strip()
    temperature = max(0.0, min(2.0, temperature))

    cfg = {
        "api_key": _encrypt_api_key(api_key.strip()) if api_key.strip() else "",
        "api_base": api_base,
        "model": model,
        "temperature": temperature,
        "max_tokens": 8192,
    }
    _save_config(cfg)


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
def _ai_cache_key(text: str, lang: str, instruction: str, existing_hash: str, kind: str = "vocab") -> str:
    raw = f"{kind}|{lang}|{instruction}|{existing_hash}|{text}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _ai_cache_get(text: str, lang: str, instruction: str, existing_hash: str, kind: str = "vocab") -> Optional[list]:
    _ensure_cache_dir()
    key = _ai_cache_key(text, lang, instruction, existing_hash, kind=kind)
    cache_file = os.path.join(_CACHE_DIR, f"ai_{key}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if time.time() - data.get("_cached_at", 0) < 7 * 24 * 3600:
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

_CHINESE_SYSTEM_PROMPT = f"""Bạn là chuyên gia tiếng Trung, trích xuất TẤT CẢ từ vựng từ văn bản và xuất JSON chính xác.

{_CHINESE_JSON_TEMPLATE}

YÊU CẦU BẮT BUỘC:
1. JSON đủ 13 trường. Trường nào không có dữ liệu thì để "" — NGOẠI TRỪ example_pinyin và example_2_pinyin: 2 trường này LUÔN LUÔN phải có giá trị, viết pinyin chuẩn có dấu thanh. Nếu thiếu → từ đó KHÔNG hợp lệ.

2. VÍ DỤ PHẢI CÓ HỒN + ĐÚNG CẤP ĐỘ (quan trọng nhất):
   - Example 1: KHẨU NGỮ tự nhiên, gắn tình huống đời thực (cà phê, nhắn tin, than thở, mạng xã hội, cãi nhau nhẹ...). Phải có cảm xúc thật (vui, bực, tiếc, mỉa mai, ngại ngùng).
   - Example 2: TRANG TRỌNG, lịch sự, phù hợp ngữ cảnh formal (công việc, hội họp, thư từ).
   - CẤP ĐỘ TỪ VỰNG & NGỮ PHÁP TRONG VÍ DỤ PHẢI KHỚP VỚI HSK CỦA TỪ: HSK1 → câu cực ngắn, chỉ dùng từ HSK1-2. HSK2-3 → câu đơn giản. HSK4 → câu trung bình. HSK5-6 → câu phức tạp, có thành ngữ. TUYỆT ĐỐI KHÔNG nhồi từ khó/ngữ pháp cao cấp vào ví dụ của từ HSK thấp — người học sẽ không hiểu được.
   - TUYỆT ĐỐI TRÁNH câu sách giáo khoa vô hồn kiểu "我是学生" / "你好吗？我很好" — không ai nói vậy ngoài đời.
   - Nếu từ có nhiều nghĩa/cách dùng → thể hiện nghĩa khác nhau trong 2 ví dụ.
   - Độ dài vừa phải, tự nhiên, đúng trọng tâm ngữ cảnh của từ.

3. CHỐNG TRÙNG: Không xuất từ đã có trong danh sách "TỪ ĐÃ CÓ" (cả mặt chữ lẫn nghĩa).

4. CHÍNH XÁC: Pinyin, ngữ pháp, từ vựng chuẩn tuyệt đối.

5. CHỦ ĐỀ (topic): Nhất quán, đúng cấp độ HSK của từ.

6. TỰ ĐỀ XUẤT: Thêm từ liên quan trong bài nếu thấy thiếu.

7. THỨ TỰ: Xuất theo đúng thứ tự xuất hiện trong văn bản gốc.

ĐẦU RA: Mảng JSON thuần [{{...}}]. Không markdown. Cuối cùng: {{"_comment":"lời bình"}}"""

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

_JAPANESE_SYSTEM_PROMPT = f"""Bạn là chuyên gia tiếng Nhật, trích xuất TẤT CẢ từ vựng từ văn bản và xuất JSON chính xác.

{_JAPANESE_JSON_TEMPLATE}

YÊU CẦU BẮT BUỘC:
1. JSON đủ 10 trường, thiếu dữ liệu → "".

2. VÍ DỤ PHẢI CÓ HỒN + ĐÚNG CẤP ĐỘ (quan trọng nhất):
   - Example 1: KHẨU NGỮ tự nhiên (普通体), gắn tình huống đời thực (quán cà phê, LINE, than thở, mạng xã hội, cãi nhau nhẹ...). Có cảm xúc thật (vui, bực, tiếc, mỉa mai, ngại ngùng). Dùng trợ từ cuối câu tự nhiên (よ、ね、よね、じゃん...).
   - Example 2: TRANG TRỌNG, lịch sự (です・ます体 hoặc 敬語 nếu phù hợp).
   - CẤP ĐỘ TỪ VỰNG & NGỮ PHÁP TRONG VÍ DỤ PHẢI KHỚP VỚI JLPT CỦA TỪ: N5 → câu cực ngắn, chỉ dùng từ/ngữ pháp N5. N4 → câu đơn giản. N3 → câu trung bình. N2-N1 → câu phức tạp, thành ngữ. TUYỆT ĐỐI KHÔNG nhồi từ khó/ngữ pháp cao cấp vào ví dụ của từ JLPT thấp — người học sẽ không hiểu được.
   - TUYỆT ĐỐI TRÁNH câu sách giáo khoa vô hồn — không ai nói vậy ngoài đời.
   - Nếu từ có nhiều nghĩa/cách dùng → thể hiện nghĩa khác nhau trong 2 ví dụ.
   - Độ dài vừa phải, tự nhiên, đúng trọng tâm ngữ cảnh của từ.

3. CHỐNG TRÙNG: Không xuất từ đã có trong danh sách "TỪ ĐÃ CÓ" (cả mặt chữ lẫn nghĩa).

4. CHÍNH XÁC: Furigana, ngữ pháp, từ vựng chuẩn tuyệt đối.

5. CHỦ ĐỀ (topic): Nhất quán, đúng cấp độ JLPT của từ.

6. TỰ ĐỀ XUẤT: Thêm từ liên quan trong bài nếu thấy thiếu.

7. THỨ TỰ: Xuất theo đúng thứ tự xuất hiện trong văn bản gốc.

ĐẦU RA: Mảng JSON thuần [{{...}}]. Không markdown. Cuối cùng: {{"_comment":"lời bình"}}"""

_SYSTEM_PROMPTS = {
    "japanese": _JAPANESE_SYSTEM_PROMPT,
    "chinese": _CHINESE_SYSTEM_PROMPT,
}

_JSON_TEMPLATES = {
    "japanese": _JAPANESE_JSON_TEMPLATE,
    "chinese": _CHINESE_JSON_TEMPLATE,
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

_JAPANESE_GRAMMAR_SYSTEM_PROMPT = f"""Bạn là chuyên gia NGỮ PHÁP tiếng Nhật (文法), trích xuất TẤT CẢ cấu trúc ngữ pháp từ văn bản và xuất JSON chính xác.

MẪU JSON:
{_JAPANESE_GRAMMAR_JSON_TEMPLATE}

YÊU CẦU BẮT BUỘC:
1. JSON đủ 11 trường. Trường nào không có dữ liệu → "".
2. pattern: cấu trúc ngữ pháp CHÍNH (VD: 〜てもいい, 〜そうです, 〜ことにする, 〜ばいい). Ghi rõ chỗ điền bằng "〜" hoặc ký hiệu loại từ (V/イA/ナA/N) để người học biết cách ghép.
3. reading: cách đọc của pattern nếu là từ/trợ từ cụ thể (VD: てもいい). Bỏ trống nếu là cấu trúc có biến tố.
4. usage: CÔNG THỨC ghép cụ thể, dễ nhớ (VD: "Vて + もいいです", "Aい + そうです").
5. explanation: giải thích NGẮN GỌN cách dùng + sắc thái (thân mật/lịch sự) + lỗi người Việt hay mắc + cấu trúc đồng nghĩa/trái nghĩa. 1-3 câu, súc tích.
6. VÍ DỤ PHẢI CÓ HỒN + ĐÚNG CẤP ĐỘ:
   - Example 1: KHẨU NGỮ tự nhiên (普通体), tình huống đời thực (quán cà phê, LINE, than thở...). Có cảm xúc thật, trợ từ cuối câu tự nhiên (よ、ね、よね).
   - Example 2: TRANG TRỌNG, lịch sự (です・ます体 hoặc 敬語 nếu phù hợp).
   - CẤP ĐỘ TỪ VỰNG & NGỮ PHÁP TRONG VÍ DỤ PHẢI KHỚP JLPT CỦA PATTERN. TUYỆT ĐỐI KHÔNG nhồi từ khó.
7. CHÍNH XÁC: ngữ pháp, cách dùng, từ vựng chuẩn tuyệt đối.
8. CHỦ ĐỀ (topic): ngắn gọn, đúng trọng tâm (VD: "Cho phép / Xin phép", "Điều kiện", "Nguyện vọng", "Suy đoán"...).

ĐẦU RA: Mảng JSON thuần [{{...}}]. Không markdown. Cuối cùng: {{"_comment":"lời bình"}}"""

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

_CHINESE_GRAMMAR_SYSTEM_PROMPT = f"""Bạn là chuyên gia NGỮ PHÁP tiếng Trung (语法), trích xuất TẤT CẢ cấu trúc ngữ pháp từ văn bản và xuất JSON chính xác.

MẪU JSON:
{_CHINESE_GRAMMAR_JSON_TEMPLATE}

YÊU CẦU BẮT BUỘC:
1. JSON đủ 13 trường. Trường nào không có dữ liệu → "" — NGOẠI TRỪ example_pinyin và example_2_pinyin: 2 trường này LUÔN LUÔN phải có giá trị, pinyin chuẩn có dấu thanh.
2. pattern: cấu trúc ngữ pháp CHÍNH (VD: 把字句, 是...的, 越来越..., 不但...而且...). Ghi rõ chỗ điền bằng ký hiệu loại từ (N/V/Adj) để biết cách ghép.
3. pinyin: phiên âm của pattern (chỉ phần cấu trúc).
4. usage: CÔNG THỨC ghép cụ thể, dễ nhớ (VD: "Chủ ngữ + 把 + 宾语 + V + 结果").
5. explanation: giải thích NGẮN GỌN cách dùng + sắc thái + lỗi người Việt hay mắc + cấu trúc đồng nghĩa. 1-3 câu.
6. VÍ DỤ PHẢI CÓ HỒN + ĐÚNG CẤP ĐỘ:
   - Example 1: KHẨU NGỮ tự nhiên, tình huống đời thực (quán cà phê, nhắn tin, mạng xã hội). Có cảm xúc thật.
   - Example 2: TRANG TRỌNG, lịch sự, phù hợp ngữ cảnh formal.
   - CẤP ĐỘ TỪ VỰNG & NGỮ PHÁP TRONG VÍ DỤ PHẢI KHỚP HSK CỦA PATTERN. TUYỆT ĐỐI KHÔNG nhồi từ khó.
   - MỌI ví dụ PHẢI kèm pinyin đầy đủ, có dấu thanh.
7. CHÍNH XÁC: ngữ pháp, pinyin, cách dùng chuẩn tuyệt đối.
8. CHỦ ĐỀ (topic): ngắn gọn, đúng trọng tâm (VD: "Cấu trúc câu", "So sánh", "Điều kiện", "Liên từ"...).

ĐẦU RA: Mảng JSON thuần [{{...}}]. Không markdown. Cuối cùng: {{"_comment":"lời bình"}}"""

_GRAMMAR_SYSTEM_PROMPTS = {
    "japanese": _JAPANESE_GRAMMAR_SYSTEM_PROMPT,
    "chinese": _CHINESE_GRAMMAR_SYSTEM_PROMPT,
}

_GRAMMAR_JSON_TEMPLATES = {
    "japanese": _JAPANESE_GRAMMAR_JSON_TEMPLATE,
    "chinese": _CHINESE_GRAMMAR_JSON_TEMPLATE,
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

def extract_vocabulary_with_ai(
    text: str,
    lang: str,
    custom_instruction: str = "",
    existing_words: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
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

    # Giới hạn text
    max_chars = 12000
    if len(text) > max_chars:
        if progress_callback:
            progress_callback(f"📝 Văn bản {len(text)} ký tự → cắt còn {max_chars}")
        text = text[:max_chars]

    if progress_callback:
        progress_callback(f"🤖 Đang gọi {cfg['model']}...")

    # User message: text + existing words list
    user_msg = f"Hãy trích xuất tất cả từ vựng từ văn bản sau:\n\n{text}"

    if existing_words and len(existing_words) > 0:
        # Giới hạn số lượng từ hiện có để tiết kiệm token (tối đa 2000 từ)
        shown_words = existing_words[:2000]
        words_str = ", ".join(shown_words)
        user_msg += (
            f"\n\n⚠️ DANH SÁCH TỪ ĐÃ CÓ TRONG DECK (TUYỆT ĐỐI KHÔNG XUẤT RA):\n"
            f"{words_str}\n"
        )
        if len(existing_words) > 2000:
            user_msg += f"\n(Còn {len(existing_words) - 2000} từ khác — tổng {len(existing_words)} từ đã có)"

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

    raise RuntimeError(f"⚠️ Không parse được JSON.\n{content[:500]}")


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

ANKI INTEGRATION:
- Dùng dữ liệu ngữ cảnh bên dưới để phân tích và đề xuất.
- Khi đề xuất từ vựng mới: CHỈ từ chưa có, kèm JSON block (```json...```) ở cuối để import 1-click.
- Format JSON đúng mẫu: Japanese {front,furigana,meaning,sino-vietnamese,jlptlevel,topic,example,example_vn,example_2,example_2_vn} | Chinese {simplified,traditional,pinyin,meaning,sino_vietnamese,hsk_level,topic,example,example_pinyin,example_vn,example_2,example_2_pinyin,example_2_vn}.
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
    chunk_size: int = 10000,
    progress_callback: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
) -> list:
    """Xử lý văn bản dài: chia đoạn, gọi AI, loại trùng"""
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

    for idx, chunk in enumerate(chunks):
        if progress_callback:
            progress_callback(f"🔄 Đoạn {idx + 1}/{len(chunks)}...")

        try:
            vocab_chunk = extract_vocabulary_with_ai(
                chunk, lang, custom_instruction, existing_words,
                progress_callback=None, force_refresh=force_refresh,
            )
            for item in vocab_chunk:
                if not isinstance(item, dict):
                    continue
                key = (item.get("front") or item.get("simplified") or "").strip().lower()
                if key and key not in seen and key not in existing_set:
                    seen.add(key)
                    all_vocab.append(item)
        except Exception as e:
            if progress_callback:
                progress_callback(f"⚠️ Lỗi đoạn {idx + 1}: {e}")

    if progress_callback:
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

    # Giới hạn text
    max_chars = 12000
    if len(text) > max_chars:
        if progress_callback:
            progress_callback(f"📝 Văn bản {len(text)} ký tự → cắt còn {max_chars}")
        text = text[:max_chars]

    if progress_callback:
        progress_callback(f"🤖 Đang gọi {cfg['model']}...")

    # User message: text + existing patterns list
    user_msg = f"Hãy trích xuất tất cả cấu trúc ngữ pháp từ văn bản sau:\n\n{text}"

    if existing_patterns and len(existing_patterns) > 0:
        shown_patterns = existing_patterns[:2000]
        patterns_str = ", ".join(shown_patterns)
        user_msg += (
            f"\n\n⚠️ CẤU TRÚC NGỮ PHÁP ĐÃ CÓ TRONG DECK (TUYỆT ĐỐI KHÔNG XUẤT RA):\n"
            f"{patterns_str}\n"
        )
        if len(existing_patterns) > 2000:
            user_msg += f"\n(Còn {len(existing_patterns) - 2000} pattern khác — tổng {len(existing_patterns)} đã có)"

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
    chunk_size: int = 10000,
    progress_callback: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
) -> list:
    """Xử lý văn bản dài: chia đoạn, gọi AI trích ngữ pháp, loại trùng"""
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

    for idx, chunk in enumerate(chunks):
        if progress_callback:
            progress_callback(f"🔄 Đoạn {idx + 1}/{len(chunks)}...")

        try:
            grammar_chunk = extract_grammar_with_ai(
                chunk, lang, custom_instruction, existing_patterns,
                progress_callback=None, force_refresh=force_refresh,
            )
            for item in grammar_chunk:
                if not isinstance(item, dict):
                    continue
                key = (item.get("pattern") or "").strip().lower()
                if key and key not in seen and key not in existing_set:
                    seen.add(key)
                    all_grammar.append(item)
        except Exception as e:
            if progress_callback:
                progress_callback(f"⚠️ Lỗi đoạn {idx + 1}: {e}")

    if progress_callback:
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
                    batch_size = 200
                    for i in range(0, len(note_ids), batch_size):
                        for nid in note_ids[i:i + batch_size]:
                            try:
                                note = mw.col.get_note(nid)
                                front = str(note.get(front_field, "")).strip()
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
                                for meaning_field in ["Meaning", "meaning"]:
                                    try:
                                        val = str(note.get(meaning_field, "")).strip()
                                        if val:
                                            entry["meaning"] = val
                                            break
                                    except Exception:
                                        pass

                                # Lấy furigana/pinyin
                                furi_field = cfg.get("furi_label", "")
                                if furi_field:
                                    try:
                                        val = str(note.get(furi_field, "")).strip()
                                        if val:
                                            if lang_key == "japanese":
                                                entry["furigana"] = val
                                            else:
                                                entry["pinyin"] = val
                                    except Exception:
                                        pass

                                # Lấy cấp độ
                                level_field = cfg.get("level_field", "")
                                if level_field:
                                    try:
                                        val = str(note.get(level_field, "")).strip()
                                        if val:
                                            entry["level"] = val
                                    except Exception:
                                        pass

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
