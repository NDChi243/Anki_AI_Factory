"""
Unit tests for GRAMMAR support (Note Type ngữ pháp riêng).

Tests:
- LANG_GRAMMAR_CONFIG (Japanese & Chinese)
- LANG_GRAMMAR_TEMPLATES + HTML template content
- LANG_GRAMMAR_CSS
- GRAMMAR AI prompts (ai_extractor)
- Batch prompt grammar mode
- parse_word_list with "pattern" JSON
- audio engine model → lang map for grammar models
"""

import json
import os
import sys
import types

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)


# ═══════════════════════════════════════════════════════════
#  LANGUAGE GRAMMAR CONFIGS
# ═══════════════════════════════════════════════════════════

class TestGrammarConfigs:
    def test_japanese_grammar_config_fields(self):
        from Language import LANG_GRAMMAR_CONFIG
        cfg = LANG_GRAMMAR_CONFIG["japanese"]
        assert cfg["model_name"] == "AnkiTool Japanese Grammar V16.0 (Add-on)"
        assert cfg["front_field"] == "Pattern"
        assert cfg["detect_key"] == "pattern"
        assert cfg["lang_code"] == "ja"
        assert "Pattern" in cfg["all_fields"]
        assert "Reading" in cfg["all_fields"]
        assert "Usage" in cfg["all_fields"]
        assert "Explanation" in cfg["all_fields"]
        assert "Example in Vietnamese" in cfg["all_fields"]
        # json_field_map đầy đủ cho các key ngữ pháp
        assert cfg["json_field_map"]["pattern"] == "Pattern"
        assert cfg["json_field_map"]["usage"] == "Usage"
        assert cfg["json_field_map"]["explanation"] == "Explanation"
        assert len(cfg["template_names"]) == 2

    def test_chinese_grammar_config_fields(self):
        from Language import LANG_GRAMMAR_CONFIG
        cfg = LANG_GRAMMAR_CONFIG["chinese"]
        assert cfg["model_name"] == "AnkiTool Chinese Grammar V16.0 (Add-on)"
        assert cfg["front_field"] == "Pattern"
        assert cfg["detect_key"] == "pattern"
        assert cfg["lang_code"] == "zh"
        assert "Pinyin" in cfg["all_fields"]
        assert "Example Pinyin" in cfg["all_fields"]
        assert "Example2 Pinyin" in cfg["all_fields"]
        assert cfg["json_field_map"]["example_pinyin"] == "Example Pinyin"

    def test_lang_grammar_config_registry(self):
        from Language import LANG_GRAMMAR_CONFIG
        assert set(LANG_GRAMMAR_CONFIG.keys()) == {"japanese", "chinese"}


# ═══════════════════════════════════════════════════════════
#  GRAMMAR TEMPLATES
# ═══════════════════════════════════════════════════════════

class TestGrammarTemplates:
    def test_registry_has_both_langs(self):
        from mode import LANG_GRAMMAR_TEMPLATES
        assert set(LANG_GRAMMAR_TEMPLATES.keys()) == {"japanese", "chinese"}
        assert len(LANG_GRAMMAR_TEMPLATES["japanese"]) == 4  # 2 cặp Q/A
        assert len(LANG_GRAMMAR_TEMPLATES["chinese"]) == 4

    def test_japanese_question_html(self):
        from mode.templates import tmpl_ja_g_q
        html = tmpl_ja_g_q()
        assert "{{Pattern}}" in html
        assert "{{type:Meaning}}" in html
        assert "Ngữ pháp" in html

    def test_japanese_answer_html(self):
        from mode.templates import tmpl_ja_g_a
        html = tmpl_ja_g_a()
        assert "{{Pattern}}" in html
        assert "{{Meaning}}" in html
        assert "{{Usage}}" in html
        assert "{{Explanation}}" in html
        assert "{{Example in Vietnamese}}" in html

    def test_japanese_reverse_answer_html(self):
        from mode.templates import tmpl_ja_g_rev_a
        html = tmpl_ja_g_rev_a()
        assert "Đáp án" in html
        assert "{{Pattern}}" in html
        assert "{{Reading}}" in html

    def test_chinese_answer_html(self):
        from mode.templates import tmpl_zh_g_a
        html = tmpl_zh_g_a()
        assert "{{Pattern}}" in html
        assert "{{Pinyin}}" in html
        assert "{{Example Pinyin}}" in html
        assert "{{Explanation}}" in html

    def test_chinese_reverse_question_html(self):
        from mode.templates import tmpl_zh_g_rev_q
        html = tmpl_zh_g_rev_q()
        assert "{{type:Pattern}}" in html
        assert "{{Meaning}}" in html


# ═══════════════════════════════════════════════════════════
#  GRAMMAR CSS
# ═══════════════════════════════════════════════════════════

class TestGrammarCss:
    def test_css_registry(self):
        from mode import LANG_GRAMMAR_CSS
        assert set(LANG_GRAMMAR_CSS.keys()) == {"japanese", "chinese"}

    def test_japanese_grammar_css_content(self):
        from mode.css import css_japanese_grammar
        css = css_japanese_grammar()
        assert isinstance(css, str)
        assert ".kanji" in css
        assert ".cw" in css

    def test_chinese_grammar_css_content(self):
        from mode.css import css_chinese_grammar
        css = css_chinese_grammar()
        assert isinstance(css, str)
        assert ".hanzi" in css
        assert ".cw" in css


# ═══════════════════════════════════════════════════════════
#  GRAMMAR AI PROMPTS
# ═══════════════════════════════════════════════════════════

class TestGrammarAiPrompts:
    def test_prompt_registries(self):
        from utils.ai_extractor import (
            _GRAMMAR_SYSTEM_PROMPTS, _GRAMMAR_JSON_TEMPLATES,
        )
        assert set(_GRAMMAR_SYSTEM_PROMPTS.keys()) == {"japanese", "chinese"}
        assert set(_GRAMMAR_JSON_TEMPLATES.keys()) == {"japanese", "chinese"}

    def test_get_grammar_json_template_japanese(self):
        from utils.ai_extractor import get_grammar_json_template
        tpl = get_grammar_json_template("japanese")
        data = json.loads(tpl)
        assert isinstance(data, dict)
        assert "pattern" in data
        assert "usage" in data
        assert "explanation" in data
        assert "example" in data

    def test_get_grammar_json_template_chinese(self):
        from utils.ai_extractor import get_grammar_json_template
        tpl = get_grammar_json_template("chinese")
        data = json.loads(tpl)
        assert "pattern" in data
        assert "example_pinyin" in data

    def test_grammar_system_prompt_content(self):
        from utils.ai_extractor import _GRAMMAR_SYSTEM_PROMPTS
        jp = _GRAMMAR_SYSTEM_PROMPTS["japanese"]
        assert "NGỮ PHÁP" in jp or "文法" in jp
        zh = _GRAMMAR_SYSTEM_PROMPTS["chinese"]
        assert "NGỮ PHÁP" in zh or "语法" in zh

    def test_extract_grammar_with_ai_signature(self):
        """Hàm extract ngữ pháp tồn tại và nhận existing_patterns."""
        from utils.ai_extractor import extract_grammar_with_ai, extract_grammar_long_text
        import inspect
        sig = inspect.signature(extract_grammar_with_ai)
        assert "existing_patterns" in sig.parameters
        sig2 = inspect.signature(extract_grammar_long_text)
        assert "existing_patterns" in sig2.parameters


# ═══════════════════════════════════════════════════════════
#  BATCH PROCESSOR — grammar mode
# ═══════════════════════════════════════════════════════════

class TestBatchProcessorGrammar:
    def test_build_batch_user_prompt_grammar(self):
        from utils.batch_processor import _build_batch_user_prompt
        words = [{"front": "〜てもいい", "meaning": "được phép", "level": "N5"}]
        prompt = _build_batch_user_prompt(
            words, "japanese", [], custom_instruction="",
            batch_num=1, total_batches=1, grammar=True,
        )
        assert "NGỮ PHÁP" in prompt
        assert "pattern" in prompt
        # Không dùng JSON template từ vựng
        assert '"front": "食べる"' not in prompt

    def test_build_batch_user_prompt_vocab_still_works(self):
        from utils.batch_processor import _build_batch_user_prompt
        words = [{"front": "食べる", "meaning": "ăn", "level": "N5"}]
        prompt = _build_batch_user_prompt(
            words, "japanese", [], custom_instruction="",
            batch_num=1, total_batches=1, grammar=False,
        )
        assert "TỪ VỰNG" in prompt

    def test_parse_word_list_pattern_json(self):
        from utils.batch_processor import parse_word_list
        raw = '[{"pattern":"〜てもいい","meaning":"được phép","jlptlevel":"N5"}]'
        result = parse_word_list(raw, "japanese")
        assert len(result) == 1
        assert result[0]["front"] == "〜てもいい"
        assert result[0]["level"] == "N5"


# ═══════════════════════════════════════════════════════════
#  AUDIO ENGINE — model → lang map cho thẻ ngữ pháp
# ═══════════════════════════════════════════════════════════

# Load audio/engine.py vào module mock (không cần Anki/edge-tts)
_tts_mock = types.ModuleType("audio.tts")
_tts_mock._install_edge_tts = lambda: False
_tts_mock._install_gtts = lambda: False
_tts_mock.get_audio_edge_tts = lambda *a, **kw: ""
_tts_mock.get_audio_gtts = lambda *a, **kw: ""
sys.modules.setdefault("audio", types.ModuleType("audio"))
sys.modules["audio"].tts = _tts_mock
sys.modules["audio.tts"] = _tts_mock

_engine_mock = types.ModuleType("audio.engine")
_engine_path = os.path.join(_addon_root, "audio", "engine.py")
with open(_engine_path, "r", encoding="utf-8") as _f:
    exec(compile(_f.read(), _engine_path, "exec"), _engine_mock.__dict__)


class TestAudioEngineGrammarMap:
    def test_detect_japanese_grammar_model(self):
        assert _engine_mock.detect_lang_from_model("AnkiTool Japanese Grammar V16.0 (Add-on)") == "ja"

    def test_detect_chinese_grammar_model(self):
        assert _engine_mock.detect_lang_from_model("AnkiTool Chinese Grammar V16.0 (Add-on)") == "zh"

    def test_detect_unknown_model(self):
        assert _engine_mock.detect_lang_from_model("Unknown Model") == ""
