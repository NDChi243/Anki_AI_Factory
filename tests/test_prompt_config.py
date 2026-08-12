"""
Unit tests cho utils/prompt_config.py — Đề xuất #1: Prompt & Schema AI có thể
ghi đè ngoài (utils/ai_prompts.json) mà không sửa code.

Kiểm tra:
- get_system_prompt()/get_json_template() mặc định khớp 100% với ai_extractor
  (round-trip placeholder → interpolate là lossless).
- fields/field_count sinh từ json_template.
- validate_json_template đúng/sai.
- save_config → ghi đè có hiệu lực; reset_config → về mặc định.
- get_signature() ổn định khi không đổi, đổi khi ghi đè, khôi phục khi reset.
- Sửa riêng json_template → prompt tự cập nhật (cơ chế {{JSON_TEMPLATE}}).
"""

import json
import os
import sys

import pytest

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

from utils import prompt_config as pc


@pytest.fixture(autouse=True)
def _force_vi_lang():
    """Buộc ngôn ngữ UI về vi — các test assert prompt mặc định TIẾNG VIỆT."""
    from utils.i18n import set_language
    set_language("vi")
    yield


LANGS = ("japanese", "chinese", "korean")
KINDS = ("vocab", "grammar")


@pytest.fixture
def clean_config(tmp_path, monkeypatch):
    """Trỏ CONFIG_PATH vào file tạm + reset cache để không đụng config thật."""
    monkeypatch.setattr(pc, "CONFIG_PATH", str(tmp_path / "ai_prompts.json"))
    pc._overrides_cache = None
    pc._overrides_mtime = None
    yield
    pc._overrides_cache = None
    pc._overrides_mtime = None


class TestUILanguagePromptSelection:
    """Khi UI = EN → AI dùng prompt sinh nghĩa/dịch TIẾNG ANH; khi VI → tiếng Việt."""

    def test_en_ui_uses_english_prompt(self, clean_config):
        from utils.i18n import set_language
        set_language("en")
        sp = pc.get_system_prompt("japanese", "vocab")
        assert "You are a Japanese language expert" in sp
        assert "MẪU:" not in sp
        tpl = pc.get_json_template("japanese", "vocab")
        assert "to eat" in tpl
        gsp = pc.get_system_prompt("chinese", "grammar")
        assert "Chinese GRAMMAR expert" in gsp

    def test_vi_ui_uses_vietnamese_prompt(self, clean_config):
        from utils.i18n import set_language
        set_language("vi")
        sp = pc.get_system_prompt("japanese", "vocab")
        assert "Bạn là chuyên gia tiếng Nhật" in sp
        assert "OUTPUT:" not in sp
        tpl = pc.get_json_template("japanese", "vocab")
        assert "ăn" in tpl


def _default_tpl(lang, kind):
    from utils import ai_extractor
    if kind == "grammar":
        return ai_extractor._GRAMMAR_JSON_TEMPLATES.get(lang, ai_extractor._JAPANESE_GRAMMAR_JSON_TEMPLATE)
    return ai_extractor._JSON_TEMPLATES.get(lang, ai_extractor._JAPANESE_JSON_TEMPLATE)


def _default_sp(lang, kind):
    from utils import ai_extractor
    if kind == "grammar":
        return ai_extractor._GRAMMAR_SYSTEM_PROMPTS.get(lang, ai_extractor._GRAMMAR_SYSTEM_PROMPTS["japanese"])
    return ai_extractor._SYSTEM_PROMPTS.get(lang, ai_extractor._JAPANESE_SYSTEM_PROMPT)


class TestDefaults:
    def test_json_template_matches_defaults(self, clean_config):
        for lang in LANGS:
            for kind in KINDS:
                assert pc.get_json_template(lang, kind) == _default_tpl(lang, kind)

    def test_system_prompt_matches_defaults_roundtrip(self, clean_config):
        """Prompt mặc định qua RAW→placeholder→interpolate phải khớp 100%."""
        for lang in LANGS:
            for kind in KINDS:
                assert pc.get_system_prompt(lang, kind) == _default_sp(lang, kind)

    def test_prompt_has_essential_sections(self, clean_config):
        for lang in LANGS:
            for kind in KINDS:
                sp = pc.get_system_prompt(lang, kind)
                assert "MẪU:" in sp
                assert "ĐẦU RA" in sp
                assert "MẪU:" in sp.replace(pc.get_json_template(lang, kind), "", 1)  # mẫu được chèn

    def test_fields_from_template(self, clean_config):
        for lang in LANGS:
            for kind in KINDS:
                tpl = pc.get_json_template(lang, kind)
                expected = list(json.loads(tpl).keys())
                assert pc.get_fields(lang, kind) == expected
                assert pc.get_field_count(lang, kind) == len(expected)


class TestValidate:
    def test_valid_object(self):
        ok, err, fields = pc.validate_json_template('{"front":"a","meaning":"b"}')
        assert ok is True
        assert err is None
        assert fields == ["front", "meaning"]

    def test_invalid_json(self):
        ok, err, fields = pc.validate_json_template("{front: a")
        assert ok is False
        assert err
        assert fields == []

    def test_array_not_allowed(self):
        ok, err, fields = pc.validate_json_template('[{"a":1}]')
        assert ok is False
        assert "object" in err

    def test_empty(self):
        ok, err, fields = pc.validate_json_template("   ")
        assert ok is False


class TestOverrideLifecycle:
    def test_save_override_and_reset(self, clean_config):
        custom_tpl = '{"front":"X","meaning":"Y","extra":"Z"}'
        custom_sp = "Bạn là chuyên gia tùy chỉnh.\n\nMẪU:\n{{JSON_TEMPLATE}}\n\nĐẦU RA: JSON."
        pc.save_config({
            "vocab": {
                "japanese": {"json_template": custom_tpl, "system_prompt": custom_sp},
            }
        })
        # Ghi đè có hiệu lực
        assert pc.get_json_template("japanese", "vocab") == custom_tpl
        assert "tùy chỉnh" in pc.get_system_prompt("japanese", "vocab")
        # Ngôn ngữ khác không bị ảnh hưởng
        assert pc.get_json_template("korean", "vocab") == _default_tpl("korean", "vocab")
        # Reset → về mặc định
        pc.reset_config()
        assert pc.get_json_template("japanese", "vocab") == _default_tpl("japanese", "vocab")
        assert pc.get_system_prompt("japanese", "vocab") == _default_sp("japanese", "vocab")

    def test_template_edit_reflects_in_prompt(self, clean_config):
        """Chỉ sửa json_template (giữ prompt RAW mặc định) → prompt tự cập nhật."""
        custom_tpl = '{"front":"ABC","meaning":"XYZ"}'
        pc.save_config({
            "vocab": {"japanese": {"json_template": custom_tpl}},
        })
        sp = pc.get_system_prompt("japanese", "vocab")
        assert "ABC" in sp
        assert "XYZ" in sp
        # Phần còn lại của prompt vẫn nguyên bản
        assert "Bạn là chuyên gia tiếng Nhật" in sp

    def test_grammar_override(self, clean_config):
        custom_tpl = '{"pattern":"P","meaning":"M"}'
        pc.save_config({
            "grammar": {"chinese": {"json_template": custom_tpl}},
        })
        assert pc.get_json_template("chinese", "grammar") == custom_tpl
        assert "P" in pc.get_system_prompt("chinese", "grammar")
        pc.reset_config()
        assert pc.get_json_template("chinese", "grammar") == _default_tpl("chinese", "grammar")

    def test_invalid_override_falls_back_to_default(self, clean_config):
        """json_template lưu không hợp lệ (rỗng) → bỏ qua, dùng mặc định."""
        pc.save_config({
            "vocab": {"japanese": {"json_template": "   "}},
        })
        assert pc.get_json_template("japanese", "vocab") == _default_tpl("japanese", "vocab")
        pc.reset_config()

    def test_effective_config_shape(self, clean_config):
        eff = pc.get_effective_config()
        assert eff["version"] == pc.PROMPT_CONFIG_VERSION
        for kind in KINDS:
            for lang in LANGS:
                e = eff[kind][lang]
                assert set(e.keys()) >= {"json_template", "system_prompt", "system_prompt_raw",
                                         "fields", "field_count", "modified"}
                assert isinstance(e["system_prompt_raw"], str)
                assert e["field_count"] == len(e["fields"])
                assert e["modified"] is False


class TestSignature:
    def test_signature_stable(self, clean_config):
        s1 = pc.get_signature()
        s2 = pc.get_signature()
        assert s1 == s2
        assert len(s1) == 32  # md5 hex

    def test_signature_changes_on_override_and_restores(self, clean_config):
        base = pc.get_signature()
        pc.save_config({
            "vocab": {"korean": {"system_prompt": "khác đi"}},
        })
        changed = pc.get_signature()
        assert changed != base
        pc.reset_config()
        assert pc.get_signature() == base


def _lang_base(lang, kind):
    from Language import LANG_CONFIG, LANG_GRAMMAR_CONFIG
    return (LANG_GRAMMAR_CONFIG if kind == "grammar" else LANG_CONFIG)[lang]


class TestFieldMap:
    def test_get_field_map_defaults(self, clean_config):
        base = _lang_base("japanese", "vocab")
        fm = pc.get_field_map("japanese", "vocab", base["json_field_map"])
        assert fm["front"] == "Front"
        assert fm["meaning"] == "Meaning"
        assert fm["jlptlevel"] == "JLPT Level"

    def test_override_changes_field_map(self, clean_config):
        pc.save_config({}, field_map={
            "vocab": {"japanese": {"front": "Mặt chữ", "english_meaning": "Nghĩa Anh"}},
        })
        base = _lang_base("japanese", "vocab")
        fm = pc.get_field_map("japanese", "vocab", base["json_field_map"])
        assert fm["front"] == "Mặt chữ"
        assert fm["english_meaning"] == "Nghĩa Anh"
        # Key không bị ghi đè vẫn giữ default
        assert fm["meaning"] == "Meaning"
        pc.reset_config()
        fm2 = pc.get_field_map("japanese", "vocab", base["json_field_map"])
        assert fm2["front"] == "Front"

    def test_apply_field_map_to_cfg_extends_all_fields(self, clean_config):
        cfg = {"json_field_map": {"front": "Front"}, "all_fields": ["Front", "Meaning"]}
        # Không có override → giữ nguyên
        eff = pc.apply_field_map_to_cfg(cfg, "japanese", "vocab")
        assert eff["json_field_map"]["front"] == "Front"
        assert eff["all_fields"] == ["Front", "Meaning"]
        # Có override thêm field mới → all_fields mở rộng
        pc.save_config({}, field_map={
            "vocab": {"japanese": {"english_meaning": "English Meaning"}},
        })
        eff2 = pc.apply_field_map_to_cfg(cfg, "japanese", "vocab")
        assert "English Meaning" in eff2["all_fields"]
        assert eff2["json_field_map"]["english_meaning"] == "English Meaning"
        pc.reset_config()

    def test_save_and_reset_field_map(self, clean_config):
        base = _lang_base("korean", "vocab")
        pc.save_config({}, field_map={"vocab": {"korean": {"front": "Hangul"}}})
        fm = pc.get_field_map("korean", "vocab", base["json_field_map"])
        assert fm["front"] == "Hangul"
        pc.reset_config()
        fm2 = pc.get_field_map("korean", "vocab", base["json_field_map"])
        assert fm2["front"] == base["json_field_map"]["front"]

    def test_effective_config_includes_field_map(self, clean_config):
        eff = pc.get_effective_config()
        for kind in KINDS:
            for lang in LANGS:
                e = eff[kind][lang]
                assert "field_map" in e and "default_field_map" in e and "all_fields" in e
                for k, v in e["default_field_map"].items():
                    assert e["field_map"][k] == v  # mặc định là superset

    def test_auto_field_name(self):
        assert pc.auto_field_name("english_meaning") == "English Meaning"
        assert pc.auto_field_name("example_pinyin") == "Example Pinyin"
        assert pc.auto_field_name("") == ""
        assert pc.auto_field_name("front") == "Front"

    def test_field_map_affects_signature(self, clean_config):
        base = pc.get_signature()
        pc.save_config({}, field_map={"vocab": {"japanese": {"front": "X"}}})
        assert pc.get_signature() != base
        pc.reset_config()
        assert pc.get_signature() == base


class TestCardShow:
    def test_default_empty(self, clean_config):
        assert pc.get_card_show("japanese", "vocab") == {}
        assert pc.get_card_show("korean", "grammar") == {}

    def test_save_and_reset(self, clean_config):
        pc.save_config({}, card_show={"vocab": {"japanese": {"English Meaning": "front"}}})
        assert pc.get_card_show("japanese", "vocab") == {"English Meaning": "front"}
        # Ngôn ngữ khác không bị ảnh hưởng
        assert pc.get_card_show("korean", "vocab") == {}
        pc.reset_config()
        assert pc.get_card_show("japanese", "vocab") == {}

    def test_invalid_side_ignored(self, clean_config):
        pc.save_config({}, card_show={"vocab": {"japanese": {"F": "weird", "G": "both"}}})
        assert pc.get_card_show("japanese", "vocab") == {"G": "both"}
        pc.reset_config()

    def test_apply_field_map_to_cfg_includes_card_show(self, clean_config):
        pc.save_config({}, card_show={"vocab": {"japanese": {"English Meaning": "both"}}})
        eff = pc.apply_field_map_to_cfg({"json_field_map": {}, "all_fields": []}, "japanese", "vocab")
        assert eff["card_show"] == {"English Meaning": "both"}
        pc.reset_config()

    def test_effective_config_includes_card_show(self, clean_config):
        eff = pc.get_effective_config()
        for kind in KINDS:
            for lang in LANGS:
                assert "card_show" in eff[kind][lang]
