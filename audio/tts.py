"""
🎤 Japanese Text-to-Speech Providers — Các engine TTS

Hỗ trợ:
- edge-tts (Microsoft Edge TTS, online, chất lượng cao)
- gTTS (Google TTS, online, fallback)
- VoiceVox (local Japanese TTS)
"""

import os
import re
import html
import hashlib
import threading
import urllib.request
import urllib.parse
import subprocess
import sys
from typing import Optional

from utils.logger import get_logger

logger = get_logger()


# ═══════════════════════════════════════════════════════════
#  Cache kết quả cài đặt package (tránh gọi subprocess nhiều lần)
# ═══════════════════════════════════════════════════════════
_install_cache = {}
_install_cache_lock = threading.Lock()


def _check_library_available(name: str):
    """Kiểm tra thư viện đã có chưa — cache kết quả để tránh import/subprocess nhiều lần."""
    with _install_cache_lock:
        if name in _install_cache:
            return _install_cache[name]
        try:
            __import__(name)
            _install_cache[name] = True
            return True
        except ImportError:
            _install_cache[name] = False
            return False


# ═══════════════════════════════════════════════════════════
#  Cache cho audio query (VoiceVox + Edge TTS loop)
# ═══════════════════════════════════════════════════════════
_audio_query_cache = {}
_audio_query_cache_lock = threading.Lock()

# Event loop cho Edge TTS — mỗi thread có loop riêng (thread-safe cho ThreadPoolExecutor)
_edge_loop_local = threading.local()


def _get_edge_loop():
    """Lấy event loop cho thread hiện tại (mỗi thread có loop riêng, lazy singleton)."""
    import asyncio
    loop = getattr(_edge_loop_local, "loop", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _edge_loop_local.loop = loop
    return loop


# ═══════════════════════════════════════════════════════════
#  Tự động cài đặt
# ═══════════════════════════════════════════════════════════
def _install_edge_tts():
    """Tự động cài đặt edge-tts nếu chưa có (cache kết quả)."""
    if _check_library_available("edge_tts"):
        return True
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"])
        _install_cache["edge_tts"] = True
        return True
    except Exception:
        logger.debug("Failed to install edge-tts")
        _install_cache["edge_tts"] = False
        return False


def _install_gtts():
    """Tự động cài đặt gTTS nếu chưa có (cache kết quả)."""
    if _check_library_available("gtts"):
        return True
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gtts"])
        _install_cache["gtts"] = True
        return True
    except Exception:
        logger.debug("Failed to install gtts")
        _install_cache["gtts"] = False
        return False


def _get_media_dir() -> str:
    """Lấy thư mục media của Anki — import aqt lazy để tránh lỗi khi test."""
    from aqt import mw
    return mw.col.media.dir()


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Loại bỏ thẻ HTML (vd <b>…</b> dùng để highlight pattern) trước khi TTS.

    Giữ nguyên nội dung bên trong thẻ — chỉ bỏ tag + decode entity HTML
    (< & ...) để giọng đọc không phát âm "b"/"pi" ở cuối câu ví dụ.
    """
    if not text:
        return text
    cleaned = _HTML_TAG_RE.sub("", text)
    cleaned = html.unescape(cleaned)
    return cleaned.strip()


# ═══════════════════════════════════════════════════════════
#  Edge TTS Provider
# ═══════════════════════════════════════════════════════════
def get_audio_edge_tts(text: str, voice: str, lang: str = "ja", rate: str = None) -> Optional[str]:
    """Tạo audio sử dụng Edge TTS. rate: edge-tts rate string như '+0%', '-50%', '+100%'"""
    if not text or not text.strip():
        return ""

    text = _strip_html(text)
    if not text:
        return ""

    rate_suffix = f"_{rate}" if rate else ""
    filename = f"anki_edge_{hashlib.md5(f'{voice}_{lang}_{text}{rate_suffix}'.encode('utf-8')).hexdigest()}.mp3"
    try:
        media_dir = _get_media_dir()
    except Exception:
        return ""
    filepath = os.path.join(media_dir, filename)

    if os.path.exists(filepath):
        return f"[sound:{filename}]"

    try:
        import edge_tts
        import asyncio

        async def _generate():
            if rate:
                communicate = edge_tts.Communicate(text, voice, rate=rate)
            else:
                communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filepath)

        # Tái sử dụng event loop (không tạo mới mỗi lần → nhanh hơn)
        loop = _get_edge_loop()
        if loop.is_running():
            # Thread không phải main → tạo loop riêng
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(_generate())
            finally:
                loop.close()
        else:
            loop.run_until_complete(_generate())

        if os.path.exists(filepath):
            return f"[sound:{filename}]"
    except Exception as e:
        logger.warning("Edge TTS error: %s — falling back to gTTS", e)
        # Fallback to gTTS
        return get_audio_gtts(text, lang)

    return ""


# ═══════════════════════════════════════════════════════════
#  Google TTS Provider
# ═══════════════════════════════════════════════════════════
def get_audio_gtts(text: str, lang: str = "ja") -> Optional[str]:
    """Tạo audio sử dụng Google TTS"""
    if not text or not text.strip():
        return ""

    text = _strip_html(text)
    if not text:
        return ""

    filename = f"anki_gtts_{hashlib.md5(f'{lang}_{text}'.encode('utf-8')).hexdigest()}.mp3"
    try:
        media_dir = _get_media_dir()
    except Exception:
        return ""
    filepath = os.path.join(media_dir, filename)

    if os.path.exists(filepath):
        return f"[sound:{filename}]"

    try:
        from gtts import gTTS

        lang_map = {"ja": "ja", "zh": "zh-CN"}
        tts_lang = lang_map.get(lang, lang)

        tts = gTTS(text=text, lang=tts_lang, slow=False)
        tts.save(filepath)

        if os.path.exists(filepath):
            return f"[sound:{filename}]"
    except Exception as e:
        logger.warning("gTTS error: %s", e)

    return ""


# ═══════════════════════════════════════════════════════════
#  VoiceVox Provider (Japanese)
# ═══════════════════════════════════════════════════════════
def get_audio_voicevox(text: str, speaker_id: int = 3) -> Optional[str]:
    """Tạo audio tiếng Nhật sử dụng VoiceVox (local API)"""
    if not text or not text.strip():
        return ""

    text = _strip_html(text)
    if not text:
        return ""

    cache_key = f"{text}_{speaker_id}"
    filename = f"anki_vv_{hashlib.md5(cache_key.encode('utf-8')).hexdigest()}.wav"
    try:
        media_dir = _get_media_dir()
    except Exception:
        return ""
    filepath = os.path.join(media_dir, filename)

    if os.path.exists(filepath):
        return f"[sound:{filename}]"

    try:
        host = "http://127.0.0.1:50021"

        # Kiểm tra cache query (thread-safe)
        with _audio_query_cache_lock:
            query_data = _audio_query_cache.get(cache_key)
        if query_data is None:
            query_url = f"{host}/audio_query?text={urllib.parse.quote(text)}&speaker={speaker_id}"
            req_query = urllib.request.Request(query_url, method='POST')
            with urllib.request.urlopen(req_query) as resp:
                query_data = resp.read()
                with _audio_query_cache_lock:
                    _audio_query_cache[cache_key] = query_data

        synth_url = f"{host}/synthesis?speaker={speaker_id}"
        req_synth = urllib.request.Request(synth_url, data=query_data, method='POST')
        req_synth.add_header('Content-Type', 'application/json')

        with urllib.request.urlopen(req_synth) as resp, open(filepath, 'wb') as f:
            f.write(resp.read())

        return f"[sound:{filename}]"
    except Exception as e:
        logger.debug("VoiceVox error: %s", e)

    return ""