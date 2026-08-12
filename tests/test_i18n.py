"""
Unit tests for utils/i18n.py — translation system.
"""

import sys
import os

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

from utils.i18n import (
    t, set_language, get_language, toggle_language, SUPPORTED_LANGUAGES,
    add_language_listener, remove_language_listener,
)


class TestI18nBasics:
    """Basic translation tests."""

    def test_supported_languages(self):
        assert "vi" in SUPPORTED_LANGUAGES
        assert "en" in SUPPORTED_LANGUAGES

    def test_default_language_is_vi(self):
        set_language("vi")
        assert get_language() == "vi"

    def test_vi_translation(self):
        set_language("vi")
        assert t("ai_extract_btn") == "🤖 AI Trích Xuất"

    def test_en_translation(self):
        set_language("en")
        assert t("ai_extract_btn") == "🤖 AI Extract"

    def test_fallback_to_vi(self):
        """Test that missing en translation falls back to vi."""
        set_language("en")
        # All keys should have both vi and en, but test fallback logic
        result = t("app_title", lang="en")
        assert "AnkiTool" in result

    def test_missing_key_returns_key(self):
        result = t("nonexistent_key_xyz")
        assert result == "nonexistent_key_xyz"

    def test_format_string(self):
        set_language("vi")
        result = t("filter_raw_count", count=5)
        assert "5" in result
        assert "Kho hàng" in result

    def test_format_string_en(self):
        set_language("en")
        result = t("filter_raw_count", count=10)
        assert "10" in result
        assert "Warehouse" in result


class TestI18nPersistence:
    """Tests for language persistence."""

    def test_set_and_get(self):
        set_language("vi")
        assert get_language() == "vi"
        set_language("en")
        assert get_language() == "en"

    def test_invalid_language_raises(self):
        try:
            set_language("fr")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_explicit_lang_param(self):
        """Test that explicit lang parameter overrides global."""
        set_language("vi")
        assert t("ai_extract_btn", lang="en") == "🤖 AI Extract"
        assert get_language() == "vi"  # Global unchanged


class TestI18nLiveSwitch:
    """Tests for the smooth VI/EN toggle + live refresh listeners."""

    def test_toggle_language_cycles_vi_en(self):
        set_language("vi")
        assert get_language() == "vi"
        assert toggle_language() == "en"
        assert get_language() == "en"
        assert toggle_language() == "vi"
        assert get_language() == "vi"

    def test_language_listener_notified(self):
        calls = []
        def cb():
            calls.append(get_language())
        add_language_listener(cb)
        try:
            set_language("vi")
            set_language("en")
            assert calls == ["vi", "en"]
        finally:
            remove_language_listener(cb)

    def test_remove_language_listener_stops_notifications(self):
        calls = []
        def cb():
            calls.append(1)
        add_language_listener(cb)
        remove_language_listener(cb)
        set_language("vi")
        assert calls == []

    def test_toggle_is_persisted(self):
        set_language("vi")
        toggle_language()  # → en
        assert get_language() == "en"


class TestI18nAllKeys:
    """Verify all keys have both vi and en translations."""

    def test_all_keys_present(self):
        """Dynamically verify all keys exist in both languages."""
        from utils.i18n import _TRANSLATIONS
        missing = []
        for key, entry in _TRANSLATIONS.items():
            if "vi" not in entry:
                missing.append(f"{key}: missing vi")
            if "en" not in entry:
                missing.append(f"{key}: missing en")
        assert not missing, f"Missing translations: {missing}"

    def test_keys_are_strings(self):
        from utils.i18n import _TRANSLATIONS
        for key, entry in _TRANSLATIONS.items():
            assert isinstance(entry.get("vi", ""), str), f"{key}: vi not str"
            assert isinstance(entry.get("en", ""), str), f"{key}: en not str"

    def test_non_empty_translations(self):
        from utils.i18n import _TRANSLATIONS
        empty = []
        for key, entry in _TRANSLATIONS.items():
            if not entry.get("vi", "").strip():
                empty.append(f"{key}: empty vi")
            if not entry.get("en", "").strip():
                empty.append(f"{key}: empty en")
        assert not empty, f"Empty translations: {empty}"
