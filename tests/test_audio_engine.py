"""
Unit tests for audio engine utilities.

Tests pure functions directly (no Anki dependency needed).
"""

# === Copy of speed_to_edge_rate from audio/engine.py (pure function) ===
def speed_to_edge_rate(speed: float) -> str:
    """Chuyen toc do (0.25-4.0) sang edge-tts rate string (-50% -> +100%)"""
    pct = (speed - 1.0) * 100
    pct = max(-50, min(100, int(round(pct))))
    return f"{'+' if pct >= 0 else ''}{pct}%"


# === Copy of VOICE_OPTIONS and get_voice_options ===
VOICE_OPTIONS = {
    "ja": [
        {"id": "ja-JP-NanamiNeural", "name": "Nanami (Nu)",  "gender": "female"},
        {"id": "ja-JP-KeitaNeural",  "name": "Keita (Nam)",  "gender": "male"},
    ],
    "zh": [
        {"id": "zh-CN-XiaoxiaoNeural",  "name": "Xiaoxiao (Nu, CN)",      "gender": "female"},
        {"id": "zh-CN-XiaoyiNeural",    "name": "Xiaoyi (Nu, CN)",        "gender": "female"},
        {"id": "zh-CN-YunxiNeural",     "name": "Yunxi (Nam, CN)",        "gender": "male"},
        {"id": "zh-CN-YunyangNeural",   "name": "Yunyang (Nam, CN)",      "gender": "male"},
        {"id": "zh-TW-HsiaoChenNeural", "name": "HsiaoChen (Nu, TW)",    "gender": "female"},
        {"id": "zh-TW-HsiaoYuNeural",   "name": "HsiaoYu (Nu, TW)",      "gender": "female"},
        {"id": "zh-HK-HiuGaaiNeural",   "name": "HiuGaai (Nu, HK)",      "gender": "female"},
        {"id": "zh-HK-WanLungNeural",   "name": "WanLung (Nam, HK)",     "gender": "male"},
    ],
}


def get_voice_options(lang: str) -> list:
    """Tra ve danh sach giong co san cho ngon ngu"""
    return VOICE_OPTIONS.get(lang, [])


# === Copy of _strip_html from audio/tts.py (pure function) ===
import re as _re
import html as _html

_HTML_TAG_RE = _re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Loai bo the HTML (vd <b>...</b> dung de highlight pattern) truoc khi TTS."""
    if not text:
        return text
    cleaned = _HTML_TAG_RE.sub("", text)
    cleaned = _html.unescape(cleaned)
    return cleaned.strip()


# === TESTS ===

class TestSpeedToEdgeRate:
    """Tests for speed_to_edge_rate conversion."""

    def test_normal_speed(self):
        assert speed_to_edge_rate(1.0) == "+0%"

    def test_half_speed(self):
        assert speed_to_edge_rate(0.5) == "-50%"

    def test_double_speed(self):
        assert speed_to_edge_rate(2.0) == "+100%"

    def test_quarter_speed_clamped(self):
        """0.25 should be clamped to -50%"""
        assert speed_to_edge_rate(0.25) == "-50%"

    def test_max_speed_clamped(self):
        """4.0 should be clamped to +100%"""
        assert speed_to_edge_rate(4.0) == "+100%"

    def test_min_boundary(self):
        assert speed_to_edge_rate(0.0) == "-50%"

    def test_1_5_speed(self):
        assert speed_to_edge_rate(1.5) == "+50%"

    def test_0_75_speed(self):
        assert speed_to_edge_rate(0.75) == "-25%"

    def test_1_25_speed(self):
        assert speed_to_edge_rate(1.25) == "+25%"

    def test_rounding(self):
        assert speed_to_edge_rate(1.33) == "+33%"
        assert speed_to_edge_rate(0.67) == "-33%"


class TestVoiceOptions:
    """Tests for voice option retrieval."""

    def test_japanese_voices(self):
        voices = get_voice_options("ja")
        assert len(voices) >= 2
        for v in voices:
            assert "id" in v
            assert "name" in v
            assert "gender" in v

    def test_chinese_voices(self):
        voices = get_voice_options("zh")
        assert len(voices) >= 4
        for v in voices:
            assert "id" in v
            assert "name" in v
            assert "gender" in v

    def test_unknown_language(self):
        assert get_voice_options("fr") == []
        assert get_voice_options("") == []


class TestStripHtml:
    """Tests for HTML tag stripping before TTS (fix "pi" voice bug)."""

    def test_removes_bold_tags(self):
        assert _strip_html("ここで写真を撮<b>ってもいい</b>ですか。") == "ここで写真を撮ってもいいですか。"

    def test_removes_tags_keeps_content(self):
        assert _strip_html("他<b>把</b>作业做完了。") == "他把作业做完了。"

    def test_decodes_entities(self):
        assert _strip_html("a \u0026lt;test\u0026gt; b") == "a <test> b"

    def test_empty_string(self):
        assert _strip_html("") == ""
        assert _strip_html(None) is None

    def test_no_html_unchanged(self):
        assert _strip_html("毎日ご飯を食べる。") == "毎日ご飯を食べる。"

    def test_strips_whitespace(self):
        assert _strip_html("  text  ") == "text"
