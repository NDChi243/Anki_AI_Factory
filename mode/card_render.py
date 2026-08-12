"""
🃏 Card Render — Mức 2: tự HIỂN THỊ field tuỳ chỉnh (custom fields) lên thẻ.

Khi người dùng thêm field mới qua Field Map Editor (Mức 1), field đó được thêm
vào Note Type + lưu dữ liệu. Module này sinh phần HTML chèn vào template thẻ để
field mới TỰ HIỆN THỊ (mặt sau mặc định; có thể chọn mặt trước/cả hai qua
`card_show` trong ai_prompts.json).

Thiết kế:
- KHÔNG phá template gốc: chỉ APPEND một khối "extra fields" vào cuối qfmt/afmt.
- Mỗi field bọc trong {{#Field}}...{{/Field}} → rỗng thì không hiện (Anki tự ẩn).
- Inline styles (tự chứa, không phụ thuộc CSS file của từng ngôn ngữ).
- Module THUẦN (không import aqt) → test được offline.
"""

import re

# Danh sách field đặc biệt của Anki — không coi là field nội dung
_SKIP_FIELDS = {"FrontSide", "Tags", "Deck", "Subdeck", "Card", "Type"}


def base_template_fields(tmpls) -> set:
    """Tập field name mà template GỐC tham chiếu ({{Field}}, {{#Field}}, {{type:Field}}...).

    tmpls: list các hàm (hoặc chuỗi) HTML template (qfmt/afmt xen kẽ).
    """
    fields = set()
    for fn in tmpls:
        html = fn() if callable(fn) else fn
        if not isinstance(html, str):
            continue
        for m in re.finditer(r"\{\{([#^/]?)([^{}\n]+?)\}\}", html):
            raw = m.group(2).strip()
            if raw.startswith("type:"):
                raw = raw.split(":", 1)[1].strip()
            if raw and raw not in _SKIP_FIELDS:
                fields.add(raw)
    return fields


def get_extra_fields(cfg: dict, base_fields=None) -> list:
    """Danh sách (field_name, side) là field TUỲ CHỈNH cần render tự động.

    Điều kiện:
    - field nằm trong json_field_map (AI sinh ra) + có trong all_fields,
    - KHÔNG nằm trong template gốc (base_fields),
    - side lấy từ cfg["card_show"] (mặc định "back").

    cfg: cấu hình HIỆU LỰC (từ apply_field_map_to_cfg) chứa json_field_map,
         all_fields, card_show.
    """
    base_fields = base_fields if base_fields is not None else set()
    mapped_values = {str(v) for v in (cfg.get("json_field_map") or {}).values()}
    card_show = cfg.get("card_show") or {}
    extra = []
    for f in (cfg.get("all_fields") or []):
        if not f or f in base_fields:
            continue
        if f not in mapped_values:
            continue
        side = card_show.get(f, "back")
        if side not in ("front", "back", "both"):
            side = "back"
        extra.append((f, side))
    return extra


def extra_fields_block(cfg: dict, base_fields=None, side: str = "back") -> str:
    """HTML khối field tuỳ chỉnh cho một mặt (front/back). Rỗng nếu không có field."""
    if side not in ("front", "back"):
        return ""
    parts = []
    for f, s in get_extra_fields(cfg, base_fields):
        if side == "front" and s not in ("front", "both"):
            continue
        if side == "back" and s not in ("back", "both"):
            continue
        parts.append(
            '{{#%s}}'
            '<div class="ef" style="margin-top:12px;padding-top:8px;'
            'border-top:1px dashed rgba(127,140,141,.35);">'
            '<div class="ef-label" style="font-size:10px;font-weight:700;color:#95a5a6;'
            'letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">%s</div>'
            '<div class="ef-value" style="font-size:15px;line-height:1.6;color:inherit;">%s</div>'
            '</div>'
            '{{/%s}}' % (f, f, f, f)
        )
    return "\n".join(parts)


def build_qfmt(cfg: dict, tmpls, index_q: int = 0) -> str:
    """qfmt (mặt trước) = template gốc + khối field tuỳ chỉnh mặt trước."""
    front = tmpls[index_q]() if callable(tmpls[index_q]) else tmpls[index_q]
    block = extra_fields_block(cfg, base_template_fields(tmpls), "front")
    return front + ("\n" + block if block else "")


def build_afmt(cfg: dict, tmpls, index_a: int = 1) -> str:
    """afmt (mặt sau) = template gốc + khối field tuỳ chỉnh mặt sau."""
    back = tmpls[index_a]() if callable(tmpls[index_a]) else tmpls[index_a]
    block = extra_fields_block(cfg, base_template_fields(tmpls), "back")
    return back + ("\n" + block if block else "")
