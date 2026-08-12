"""
Unit tests for AI token optimization.

Kiểm tra:
- _format_existing_context: chỉ gửi từ trùng với văn bản (tiết kiệm input)
- _build_batch_user_prompt: chỉ gửi từ trùng với batch
- System prompt được nén nhưng vẫn đủ MẪU + ĐẦU RA
- Cache version được bump khi đổi prompt
"""

import os
import sys

import pytest

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)


@pytest.fixture(autouse=True)
def _force_vi_lang():
    """Buộc ngôn ngữ UI về vi — các test assert chuỗi prompt TIẾNG VIỆT."""
    from utils.i18n import set_language
    set_language("vi")
    yield


class TestFormatExistingContext:
    def test_overlap_only(self):
        from utils.ai_extractor import _format_existing_context
        existing = ["食べる", "飲む", "学校", "食べる"]
        text = "毎日ご飯を食べる。学校へ行く。"
        ctx = _format_existing_context(existing, text, label="TỪ")
        assert "食べる" in ctx
        assert "学校" in ctx
        assert "飲む" not in ctx          # không trùng văn bản → không gửi
        assert ctx.count("食べる") == 1    # đã dedup

    def test_no_overlap_reports_total(self):
        from utils.ai_extractor import _format_existing_context
        ctx = _format_existing_context(["あいうえお", "かきくけこ"], "食べる学校", label="TỪ")
        assert "ĐÃ CÓ 2" in ctx
        assert "あいうえお" not in ctx

    def test_empty_existing(self):
        from utils.ai_extractor import _format_existing_context
        assert _format_existing_context([], "text", label="TỪ") == ""

    def test_cap_limits_length(self):
        from utils.ai_extractor import _format_existing_context, _MAX_EXISTING_SHOWN
        big = [f"w{i}日本" for i in range(2000)]
        text = " ".join(f"w{i}日本" for i in range(50))
        ctx = _format_existing_context(big, text, label="TỪ")
        assert len(ctx) < 5000
        assert _MAX_EXISTING_SHOWN <= 400


class TestBatchPromptExistingContext:
    def test_only_overlapping_sent(self):
        from utils.batch_processor import _build_batch_user_prompt
        words = [
            {"front": "食べる", "meaning": "ăn", "level": "N5"},
            {"front": "飲む", "meaning": "uống", "level": "N5"},
        ]
        existing = ["食べる", "学校", "会社", "飲む"] * 100
        prompt = _build_batch_user_prompt(
            words, "japanese", existing, batch_num=1, total_batches=1, grammar=False,
        )
        assert "食べる" in prompt
        assert "飲む" in prompt
        assert "学校" not in prompt
        assert "会社" not in prompt

    def test_no_overlap(self):
        from utils.batch_processor import _build_batch_user_prompt
        words = [{"front": "食べる", "meaning": "ăn", "level": "N5"}]
        prompt = _build_batch_user_prompt(
            words, "japanese", ["学校", "会社"], batch_num=1, total_batches=1, grammar=False,
        )
        assert "không trùng batch" in prompt


class TestSystemPromptCompactness:
    def test_vocab_prompts_compact(self):
        from utils.ai_extractor import _SYSTEM_PROMPTS
        for lang in ("japanese", "chinese", "korean"):
            sp = _SYSTEM_PROMPTS[lang]
            assert "MẪU:" in sp
            assert "ĐẦU RA" in sp
            assert len(sp) < 1400

    def test_grammar_prompts_compact(self):
        from utils.ai_extractor import _GRAMMAR_SYSTEM_PROMPTS
        for lang in ("japanese", "chinese", "korean"):
            sp = _GRAMMAR_SYSTEM_PROMPTS[lang]
            assert "MẪU:" in sp
            assert "ĐẦU RA" in sp
            assert len(sp) < 2400

    def test_output_conciseness_rule(self):
        from utils.ai_extractor import _GRAMMAR_SYSTEM_PROMPTS
        for lang in ("japanese", "chinese", "korean"):
            assert "TỐI ĐA 2 câu" in _GRAMMAR_SYSTEM_PROMPTS[lang]


class TestCacheVersion:
    def test_version_bumped(self):
        from utils.ai_extractor import _PROMPT_VERSION, _ai_cache_key
        assert _PROMPT_VERSION >= 3
        k1 = _ai_cache_key("text", "japanese", "", "h", kind="vocab")
        assert isinstance(k1, str) and len(k1) == 32
