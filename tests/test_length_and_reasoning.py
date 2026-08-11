"""
Unit tests cho:
- Mở rộng giới hạn nội dung (max_chars 45k, chunk_size 20k, config được)
- reasoning_effort truyền vào payload API
- AI Chat cap 30k
"""

import os
import sys
from unittest.mock import patch

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)


class TestApiConfigExtras:
    def test_defaults(self):
        """Default config khi CHƯA có file ai_config.json (mock để không phụ thuộc file thật)."""
        from utils.ai_extractor import get_api_config
        with patch("utils.ai_extractor._load_config", return_value={}):
            cfg = get_api_config()
            assert cfg.get("max_chars") == 45000
            assert cfg.get("chunk_size") == 8000
            assert cfg.get("reasoning_effort") == ""

    def test_sanitizes_old_large_chunk(self):
        """Config cũ lưu chunk 45k → tự hạ xuống 15k khi đọc (tránh cắt output)."""
        from utils.ai_extractor import get_api_config
        with patch("utils.ai_extractor._load_config", return_value={
            "api_key": "", "chunk_size": 45000, "max_chars": 45000,
        }):
            cfg = get_api_config()
            assert cfg["chunk_size"] == 15000
            assert cfg["max_chars"] == 45000

    def test_save_roundtrip(self):
        """max_chars có SÀN 10000 theo chủ ý thiết kế (khớp với sàn dùng
        trong get_api_config() dòng ~244) — input 8000 sẽ bị nâng lên
        10000, không giữ nguyên. chunk_size sàn 3000 nên 8000 giữ nguyên."""
        from utils.ai_extractor import save_api_config
        with patch("utils.ai_extractor._save_config") as m:
            save_api_config("k", "https://x/v1", "deepseek-chat", 0.3,
                            max_chars=8000, chunk_size=8000, reasoning_effort="medium")
            saved = m.call_args[0][0]
            assert saved["chunk_size"] == 8000
            assert saved["max_chars"] == 10000  # clamp lên sàn, không phải 8000
            assert saved["reasoning_effort"] == "medium"

    def test_save_clamps(self):
        from utils.ai_extractor import save_api_config
        with patch("utils.ai_extractor._save_config") as m:
            save_api_config("k", "https://x/v1", "deepseek-chat", 0.3,
                            max_chars=100, chunk_size=999999, reasoning_effort="weird")
            saved = m.call_args[0][0]
            assert saved["max_chars"] == 10000
            assert saved["chunk_size"] == 15000      # chunk bị cap 15k để tránh tràn output
            assert saved["reasoning_effort"] == ""


class TestReasoningEffort:
    def test_adds_when_set(self):
        from utils.ai_extractor import _apply_reasoning_effort
        p = {}
        _apply_reasoning_effort(p, {"reasoning_effort": "low"})
        assert p.get("reasoning_effort") == "low"

    def test_normalizes_case(self):
        from utils.ai_extractor import _apply_reasoning_effort
        p = {}
        _apply_reasoning_effort(p, {"reasoning_effort": "HIGH"})
        assert p.get("reasoning_effort") == "high"

    def test_not_added_when_empty(self):
        from utils.ai_extractor import _apply_reasoning_effort
        p = {}
        _apply_reasoning_effort(p, {"reasoning_effort": ""})
        assert "reasoning_effort" not in p


class TestLongTextChunkConfig:
    def test_chunk_size_optional(self):
        import inspect
        from utils.ai_extractor import extract_vocabulary_long_text, extract_grammar_long_text
        assert inspect.signature(extract_vocabulary_long_text).parameters["chunk_size"].default is None
        assert inspect.signature(extract_grammar_long_text).parameters["chunk_size"].default is None

    def test_single_call_uses_cfg_max_chars(self):
        import inspect
        from utils.ai_extractor import extract_vocabulary_with_ai
        src = inspect.getsource(extract_vocabulary_with_ai)
        assert 'cfg.get("max_chars", 45000)' in src


class TestChatCap:
    def test_chat_cap_reads_from_config(self):
        with open(os.path.join(_addon_root, "__init__.py"), "r", encoding="utf-8") as f:
            src = f.read()
        # Cap chat phải đọc max_chars từ config (không cứng 30k)
        assert 'get("max_chars", 45000)' in src
        assert "_MAX_CHAT_CHARS = 30000" not in src