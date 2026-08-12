"""
Unit tests cho mode/card_render.py — Mức 2: tự HIỂN THỊ field tuỳ chỉnh lên thẻ.

Kiểm tra (thuần, không cần Anki/aqt):
- base_template_fields() đọc đúng {{Field}}, {{#Field}}, {{type:Field}}.
- get_extra_fields(): chỉ chọn field TUỲ CHỈNH (trong json_field_map, ngoài template gốc),
  đúng side (front/back/both, mặc định back).
- extra_fields_block(): sinh HTML đúng side, bọc {{#Field}}...{{/Field}}.
- build_qfmt/build_afmt: append block vào template gốc; không đổi khi không có field mới.
"""

import os
import sys

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

from mode.card_render import (
    base_template_fields,
    get_extra_fields,
    extra_fields_block,
    build_qfmt,
    build_afmt,
)


def _cfg(**over):
    """cfg mô phỏng cấu hình HIỆU LỰC (như apply_field_map_to_cfg trả về)."""
    base = {
        "json_field_map": {"front": "Front", "meaning": "Meaning", "english_meaning": "English Meaning"},
        "all_fields": ["Front", "Meaning", "English Meaning"],
        "card_show": {},
    }
    base.update(over)
    return base


def _tmpls():
    """2 hàm template mô phỏng qfmt/afmt: front có {{Front}}, back có {{Meaning}}."""
    return [
        lambda: '<div class="f">{{Front}}</div>',
        lambda: '<div class="a">{{Meaning}}</div>',
    ]


class TestBaseTemplateFields:
    def test_detects_various_syntax(self):
        tmpls = [
            lambda: '{{Front}} {{#Front}}{{/Front}} {{^Meaning}} {{type:Meaning}} {{Tags}} {{FrontSide}}',
        ]
        fields = base_template_fields(tmpls)
        assert "Front" in fields
        assert "Meaning" in fields
        assert "Tags" not in fields
        assert "FrontSide" not in fields


class TestGetExtraFields:
    def test_picks_custom_fields_only(self):
        # "English Meaning" nằm trong json_field_map nhưng KHÔNG trong template gốc
        cfg = _cfg()
        extra = get_extra_fields(cfg, base_fields={"Front", "Meaning"})
        assert extra == [("English Meaning", "back")]

    def test_default_side_is_back(self):
        extra = get_extra_fields(_cfg(), base_fields={"Front", "Meaning"})
        assert extra[0][1] == "back"

    def test_respects_card_show(self):
        cfg = _cfg(card_show={"English Meaning": "front"})
        extra = get_extra_fields(cfg, base_fields={"Front", "Meaning"})
        assert extra[0][1] == "front"

    def test_invalid_side_falls_back_to_back(self):
        cfg = _cfg(card_show={"English Meaning": "weird"})
        extra = get_extra_fields(cfg, base_fields={"Front", "Meaning"})
        assert extra[0][1] == "back"

    def test_ignores_base_fields(self):
        # Field nằm trong template gốc → không render lại dù có trong json_field_map
        cfg = {"json_field_map": {"front": "Front", "meaning": "Meaning"},
               "all_fields": ["Front", "Meaning"],
               "card_show": {"Meaning": "both"}}
        extra = get_extra_fields(cfg, base_fields={"Front", "Meaning"})
        assert extra == []

    def test_no_custom_fields(self):
        cfg = {"json_field_map": {"front": "Front"}, "all_fields": ["Front"], "card_show": {}}
        assert get_extra_fields(cfg, base_fields={"Front"}) == []


class TestExtraFieldsBlock:
    def test_back_block_includes_field(self):
        block = extra_fields_block(_cfg(), base_fields={"Front", "Meaning"}, side="back")
        assert "English Meaning" in block
        assert "{{#English Meaning}}" in block
        assert "{{/English Meaning}}" in block
        assert "class=\"ef\"" in block

    def test_front_block_empty_by_default(self):
        block = extra_fields_block(_cfg(), base_fields={"Front", "Meaning"}, side="front")
        assert block == ""

    def test_front_block_when_side_front(self):
        cfg = _cfg(card_show={"English Meaning": "front"})
        block = extra_fields_block(cfg, base_fields={"Front", "Meaning"}, side="front")
        assert "English Meaning" in block

    def test_both_sides(self):
        cfg = _cfg(card_show={"English Meaning": "both"})
        assert "English Meaning" in extra_fields_block(cfg, base_fields={"Front", "Meaning"}, side="front")
        assert "English Meaning" in extra_fields_block(cfg, base_fields={"Front", "Meaning"}, side="back")

    def test_invalid_side_returns_empty(self):
        assert extra_fields_block(_cfg(), base_fields={"Front", "Meaning"}, side="xyz") == ""


class TestBuildQfmtAfmt:
    def test_append_to_back_by_default(self):
        q = build_qfmt(_cfg(), _tmpls(), 0)
        a = build_afmt(_cfg(), _tmpls(), 1)
        assert "English Meaning" not in q   # mặc định chỉ mặt sau
        assert "English Meaning" in a
        assert "{{Meaning}}" in a           # template gốc giữ nguyên

    def test_append_to_front_when_configured(self):
        cfg = _cfg(card_show={"English Meaning": "front"})
        q = build_qfmt(cfg, _tmpls(), 0)
        assert "English Meaning" in q
        assert "{{Front}}" in q

    def test_no_change_when_no_custom_fields(self):
        cfg = {"json_field_map": {"front": "Front"}, "all_fields": ["Front", "Meaning"],
               "card_show": {}, "template_names": ["T"]}
        q = build_qfmt(cfg, _tmpls(), 0)
        a = build_afmt(cfg, _tmpls(), 1)
        assert q == '<div class="f">{{Front}}</div>'
        assert a == '<div class="a">{{Meaning}}</div>'

    def test_accepts_string_templates(self):
        tmpls = ['<div>{{Front}}</div>', '<div>{{Meaning}}</div>']
        a = build_afmt(_cfg(), tmpls, 1)
        assert "English Meaning" in a
