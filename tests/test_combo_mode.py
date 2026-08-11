"""
Tests cho COMBO MODE (card gộp 5 chế độ → 1 card).

Kiểm tra:
- LANG_TEMPLATES mỗi ngôn ngữ chỉ còn 1 cặp template combo (1 từ = 1 card)
- Template combo chứa thanh chọn mode (combo-mode-bar) + 5 panel (qa/vn/wb/pron/lg)
- CSS chứa style mode-btn / combo-check / combo-res
- Language config template_names chỉ còn 1 tên combo
- _COMBO_MODE_JS tồn tại trong mode/shared.py
- hooks/overview_mode: build selector HTML, inject vào overview, set/get study mode
"""

import os
import sys
import types
from unittest.mock import MagicMock

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)


# ── Mock Anki (aqt) — chỉ cần gui_hooks + mw cho overview_mode ──────────────
aqt_mock = types.ModuleType("aqt")
aqt_mock.mw = MagicMock()
aqt_mock.mw.col = MagicMock()
aqt_mock.mw.col.conf = MagicMock()
aqt_mock.mw.col.conf.get = MagicMock(return_value="qa")
aqt_mock.mw.col.setMod = MagicMock()
aqt_mock.gui_hooks = MagicMock()
sys.modules["aqt"] = aqt_mock
sys.modules["aqt.mw"] = aqt_mock.mw


class TestComboTemplates:
    def test_lang_templates_only_one_pair(self):
        from mode import LANG_TEMPLATES
        # Mỗi ngôn ngữ chỉ 1 cặp (q, a) → 1 template duy nhất = 1 card/từ
        assert len(LANG_TEMPLATES["japanese"]) == 2
        assert len(LANG_TEMPLATES["chinese"]) == 2
        assert len(LANG_TEMPLATES["korean"]) == 2

    def test_japanese_combo_question_has_mode_bar(self):
        from mode.templates import tmpl_ja_combo_q
        html = tmpl_ja_combo_q()
        assert 'id="combo-mode-bar"' in html
        assert 'id="mode-panel-qa"' in html
        assert 'id="mode-panel-vn"' in html
        assert 'id="mode-panel-wb"' in html
        assert 'id="mode-panel-pron"' in html
        assert 'id="mode-panel-lg"' in html
        assert "{{type:Meaning}}" in html
        assert "{{Front}}" in html
        assert "{{Meaning}}" in html

    def test_japanese_combo_answer_has_answer(self):
        from mode.templates import tmpl_ja_combo_a
        html = tmpl_ja_combo_a()
        assert 'id="combo-mode-bar"' in html
        assert "{{Furigana}}" in html
        assert "{{Meaning}}" in html

    def test_chinese_combo_question_has_mode_bar(self):
        from mode.templates import tmpl_zh_combo_q
        html = tmpl_zh_combo_q()
        assert 'id="combo-mode-bar"' in html
        assert 'id="mode-panel-qa"' in html
        assert "{{type:Meaning}}" in html
        assert "{{Pinyin}}" in html

    def test_chinese_combo_answer(self):
        from mode.templates import tmpl_zh_combo_a
        html = tmpl_zh_combo_a()
        assert 'id="combo-mode-bar"' in html
        assert "{{Pinyin}}" in html
        assert "{{Meaning}}" in html

    def test_korean_combo_question_has_mode_bar(self):
        from mode.templates import tmpl_ko_combo_q
        html = tmpl_ko_combo_q()
        assert 'id="combo-mode-bar"' in html
        assert 'id="mode-panel-qa"' in html
        assert 'id="mode-panel-vn"' in html
        assert 'id="mode-panel-wb"' in html
        assert 'id="mode-panel-pron"' in html
        assert 'id="mode-panel-lg"' in html
        assert "{{type:Meaning}}" in html
        assert "{{Romanization}}" in html
        assert "{{Front}}" in html
        assert "{{Meaning}}" in html

    def test_korean_combo_answer(self):
        from mode.templates import tmpl_ko_combo_a
        html = tmpl_ko_combo_a()
        assert 'id="combo-mode-bar"' in html
        assert "{{Romanization}}" in html
        assert "{{Meaning}}" in html


class TestComboCss:
    def test_css_has_mode_styles(self):
        from mode.css import css_japanese, css_chinese
        for css in (css_japanese(), css_chinese()):
            assert ".mode-bar" in css
            assert ".mode-btn" in css
            assert ".combo-check" in css
            assert ".combo-res" in css


class TestComboJs:
    def test_combo_mode_js_exists(self):
        from mode.shared import _COMBO_MODE_JS
        assert "ai_factory_set_mode" in _COMBO_MODE_JS
        assert "localStorage" in _COMBO_MODE_JS
        assert "mode-panel-qa" in _COMBO_MODE_JS


class TestComboConfig:
    def test_template_names_single(self):
        from Language import LANG_CONFIG
        assert len(LANG_CONFIG["japanese"]["template_names"]) == 1
        assert len(LANG_CONFIG["chinese"]["template_names"]) == 1
        assert len(LANG_CONFIG["korean"]["template_names"]) == 1
        assert "Tổng hợp" in LANG_CONFIG["japanese"]["template_names"][0]
        assert "Tổng hợp" in LANG_CONFIG["chinese"]["template_names"][0]
        assert "Tổng hợp" in LANG_CONFIG["korean"]["template_names"][0]


class TestOverviewModeSelector:
    def test_build_selector_html(self):
        from hooks.overview_mode import _build_selector_html, MODES
        html = _build_selector_html()
        assert "ai-factory-mode-selector" in html
        assert "ai-factory-study" in html
        assert "ai_factory_set_mode" in html
        for m in MODES:
            assert f'value="{m}"' in html

    def test_inject_selector_before_study(self):
        from hooks.overview_mode import _inject_selector
        base = '<div class="stats"></div><button id="study">Study now</button>'
        out = _inject_selector(base)
        # Selector nằm trước nút study
        assert out.index("ai-factory-mode-selector") < out.index('id="study"')
        assert 'id="study"' in out

    def test_inject_selector_fallback(self):
        from hooks.overview_mode import _inject_selector
        base = "<div>no study button</div>"
        out = _inject_selector(base)
        assert "ai-factory-mode-selector" in out

    def test_set_and_get_study_mode(self):
        from unittest.mock import patch
        from hooks.overview_mode import get_study_mode, set_study_mode, CONF_KEY, MODES
        conf = MagicMock()
        mw_mock = MagicMock()
        mw_mock.col.conf = conf
        # set_study_mode với mode hợp lệ
        with patch("aqt.mw", mw_mock):
            assert set_study_mode("vn") is True
            # set với mode không hợp lệ → fallback qa
            conf.get = MagicMock(return_value="bad_mode")
            assert get_study_mode() == "qa"
            conf.get = MagicMock(return_value="pron")
            assert get_study_mode() == "pron"
        # set_study_mode với mode không hợp lệ → fallback qa + vẫn lưu
        with patch("aqt.mw", mw_mock):
            assert set_study_mode("unknown_mode") is True
            conf.get = MagicMock(return_value="unknown_mode")
            assert get_study_mode() == "qa"
        assert CONF_KEY == "ai_factory_study_mode"
        assert set(MODES) == {"qa", "vn", "wb", "pron", "lg"}

    def test_on_js_message_handles_mode(self):
        from unittest.mock import patch
        from hooks.overview_mode import _on_js_message
        with patch("hooks.overview_mode.set_study_mode") as set_mock:
            handled = _on_js_message((False, None), "ai_factory_set_mode:wb", None)
            set_mock.assert_called_once_with("wb")
            assert handled == (True, None)
        # message không phải của add-on → giữ nguyên handled
        result = _on_js_message((False, None), "onigiri_study", None)
        assert result == (False, None)

    def test_patch_overview_wraps_not_overwrites(self):
        """Patch Overview._table phải WRAP hàm hiện tại, không ghi đè (bảo toàn Onigiri)."""
        from unittest.mock import patch
        import types as _types
        import sys as _sys
        # Fake module aqt.overview
        fake_overview_mod = _types.ModuleType("aqt.overview")
        calls = []
        class FakeOverview:
            pass
        def orig_table(self):
            calls.append("orig")
            return '<div><button id="study">Study now</button></div>'
        FakeOverview._table = staticmethod(orig_table)
        fake_overview_mod.Overview = FakeOverview
        _sys.modules["aqt.overview"] = fake_overview_mod
        try:
            from hooks.overview_mode import _patch_overview
            _patch_overview()
            wrapped = FakeOverview._table
            # hàm hiện tại đã bị wrap
            html = wrapped(FakeOverview())
            assert calls == ["orig"]  # vẫn gọi hàm gốc
            assert "ai-factory-mode-selector" in html
            assert 'id="study"' in html
            assert FakeOverview._ai_factory_mode_patched is True
        finally:
            _sys.modules.pop("aqt.overview", None)


