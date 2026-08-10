"""
🎤 Japanese Text-to-Speech Providers — Các engine TTS

Hỗ trợ:
- edge-tts (Microsoft Edge TTS, online, chất lượng cao)
- gTTS (Google TTS, online, fallback)
- VoiceVox (local Japanese TTS)
"""

import os
import hashlib
import urllib.request
import urllib.parse
import subprocess
import sys
from typing import Optional

from aqt import mw
from utils.logger import get_logger

logger = get_logger()


# ═══════════════════════════════════════════════════════════
#  Cache cho audio query (VoiceVox)
# ═══════════════════════════════════════════════════════════
_audio_query_cache = {}


# ═══════════════════════════════════════════════════════════
#  Tự động cài đặt
# ═══════════════════════════════════════════════════════════
def _install_edge_tts():
    """Tự động cài đặt edge-tts nếu chưa có"""
    try:
        import edge_tts
        return True
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"])
            return True
        except Exception:
            logger.debug("Failed to install edge-tts")
            return False


def _install_gtts():
    """Tự động cài đặt gTTS nếu chưa có"""
    try:
        from gtts import gTTS
        return True
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "gtts"])
            return True
        except Exception:
            logger.debug("Failed to install gtts")
            return False


# ═══════════════════════════════════════════════════════════
#  Edge TTS Provider
# ═══════════════════════════════════════════════════════════
def get_audio_edge_tts(text: str, voice: str, lang: str = "ja", rate: str = None) -> Optional[str]:
    """Tạo audio sử dụng Edge TTS. rate: edge-tts rate string như '+0%', '-50%', '+100%'"""
    if not text or not text.strip():
        return ""

    rate_suffix = f"_{rate}" if rate else ""
    filename = f"anki_edge_{hashlib.md5(f'{voice}_{lang}_{text}{rate_suffix}'.encode('utf-8')).hexdigest()}.mp3"
    filepath = os.path.join(mw.col.media.dir(), filename)

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

        # Chạy async trong thread riêng
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate())
        loop.close()

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

    filename = f"anki_gtts_{hashlib.md5(f'{lang}_{text}'.encode('utf-8')).hexdigest()}.mp3"
    filepath = os.path.join(mw.col.media.dir(), filename)

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

    cache_key = f"{text}_{speaker_id}"
    filename = f"anki_vv_{hashlib.md5(cache_key.encode('utf-8')).hexdigest()}.wav"
    filepath = os.path.join(mw.col.media.dir(), filename)

    if os.path.exists(filepath):
        return f"[sound:{filename}]"

    try:
        host = "http://127.0.0.1:50021"

        # Kiểm tra cache query
        if cache_key in _audio_query_cache:
            query_data = _audio_query_cache[cache_key]
        else:
            query_url = f"{host}/audio_query?text={urllib.parse.quote(text)}&speaker={speaker_id}"
            req_query = urllib.request.Request(query_url, method='POST')
            with urllib.request.urlopen(req_query) as resp:
                query_data = resp.read()
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
