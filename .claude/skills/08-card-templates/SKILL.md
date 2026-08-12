---
name: card-templates
description: Giao diện thẻ — mode/ (templates.py HTML, css.py CSS, shared.py JS games). Đọc khi sửa template thẻ, CSS, mini-game JS.
---

# 🃏 SKILL-08: CARD TEMPLATES (`mode/`)

> 3 file: `templates.py` (573) HTML, `css.py` (173) CSS, `shared.py` JS engines + CSS dùng chung. Registry tại `mode/__init__.py`.

## REGISTRY (`mode/__init__.py`)

```python
from .css import LANG_CSS, LANG_GRAMMAR_CSS
from .templates import LANG_TEMPLATES, LANG_GRAMMAR_TEMPLATES
from .shared import _HW_CSS, _WB_JS_BODY, _HW_JS_BODY, WB_POOLS, _SHARED_UI_CSS, _SPEED_CTRL_JS, _LG_JS_BODY
```

## TEMPLATES (`mode/templates.py`)

- **V16.1: COMBO MODE** — mỗi từ = **1 card duy nhất** (1 từ = 1 card, deck đếm đúng số từ).
  - `LANG_TEMPLATES` mỗi ngôn ngữ chỉ còn 1 cặp combo: `tmpl_{lang}_combo_q/a` (thay cho 5 cặp cũ).
  - Card combo chứa **thanh chọn mode** (`#combo-mode-bar`) + 5 panel (`#mode-panel-qa/vn/wb/pron/lg`).
  - Mode qa (Ngôn ngữ→Việt) dùng `{{type:Meaning}}` chuẩn Anki; vn/pron tự kiểm tra bằng JS.
  - JS chuyển mode: `_COMBO_MODE_JS` (`mode/shared.py`) — đọc `window._aiFactoryMode` (reviewer hook) hoặc `localStorage`.
  - Mode đồng bộ: `mw.col.conf["ai_factory_study_mode"]` qua `pycmd('ai_factory_set_mode:...')`.
- Các hàm template cũ (`tmpl_ja_q/a`, `tmpl_ja_vn_*`, `tmpl_ja_wb_*`, `tmpl_ja_pron_*`, `tmpl_ja_lg_*`) vẫn giữ làm tham chiếu.
- `LANG_GRAMMAR_TEMPLATES` = `{"japanese": (ja_g_q,a, ja_g_rev_q,a), ...}` — 2 chiều (Cấu trúc→Nghĩa, Nghĩa→Cấu trúc).

**QUY ƯỚC**:
- Template dùng Mustache `{{Field}}` / `{{#Field}}...{{/Field}}` (Anki syntax).
- Class CSS tương ứng: `.cw`, `.ch`, `.vb`, `.ir`, `.es`, `.blank`, `.fill-word`, `.wb-*`, `.lg-*`.
- Letter Gap: HTML phải chứa `id="lg-display"` để reviewer hook inject JS (xem hooks/reviewer.py:15).
- Grammar: đánh dấu pattern trong ví dụ bằng `<b>…</b>` (prompt yêu cầu).

## 🃏 CARD RENDER TUỲ CHỈNH (`mode/card_render.py`) — Mức 2

- **Vai trò**: khi người dùng thêm field mới qua Field Map Editor (Mức 1), module này tự
  APPEND khối "extra fields" vào cuối qfmt/afmt → field mới TỰ HIỆN trên thẻ mà KHÔNG sửa template gốc.
- `base_template_fields(tmpls)` — tập field template gốc tham chiếu (để biết field nào là "mới").
- `get_extra_fields(cfg, base_fields)` — field tuỳ chỉnh cần render: trong `json_field_map` + `all_fields`,
  ngoài template gốc, side theo `cfg["card_show"]` (mặc định "back").
- `extra_fields_block(cfg, base_fields, side)` — HTML: `{{#Field}}...{{/Field}}` (rỗng thì ẩn) + inline styles (không cần CSS file).
- `build_qfmt(cfg, tmpls, i)` / `build_afmt(cfg, tmpls, i)` — template gốc + block. **Dùng ở `__init__.py`
  get_or_create_model/_force_rebuild_model và `ui/prompt_editor.py:_sync_models_after_save`.**
- **QUY ƯỚC**: KHÔNG phá template combo hiện có — chỉ append; mỗi field bọc `{{#Field}}`; thứ tự theo `all_fields`.

## CSS (`mode/css.py`)

```python
css_japanese()            # :101 = _JA_THEME + _BASE_CSS + _JA_SPECIFIC + _JA_EXTRA + _SHARED_UI_CSS
css_chinese()             # :136 = _ZH_THEME + _BASE_CSS + _ZH_SPECIFIC + _ZH_EXTRA + _SHARED_UI_CSS
css_korean()              # :16x = _KO_THEME + _BASE_CSS + _KO_SPECIFIC + _KO_EXTRA + _SHARED_UI_CSS
css_japanese_grammar()    # :160 (thêm _GRAMMAR_EXTRA)
css_chinese_grammar()     # :164
css_korean_grammar()      # :16x
```
- `_BASE_CSS` dùng chung (nightMode, body, .cw, .vb, .ir, .es...) — giảm 80% trùng lặp.
- Thêm style ngôn ngữ: thêm vào `_JA_SPECIFIC`/`_ZH_SPECIFIC` — không sửa `_BASE_CSS` trừ khi ảnh hưởng cả 2.

## SHARED JS/CSS (`mode/shared.py`)

| Symbol | Vai trò |
|--------|---------|
| `_HW_CSS` | CSS handwriting |
| `_WB_JS_BODY` | JS Word Building (drag & drop) |
| `_HW_JS_BODY` | JS Handwriting |
| `WB_POOLS` | Bộ chữ cái theo ngôn ngữ (`{"japanese": JA_WB_POOL, "chinese": ZH_WB_POOL, "korean": KO_WB_POOL, ...}`) |
| `_SHARED_UI_CSS` | CSS speed bar overlay |
| `_SPEED_CTRL_JS` | Speed control (0.25-4.0×) — dùng `window._ankiDefaultSpeed` set bởi reviewer hook |
| `_LG_JS_BODY` | Letter Gap JS |
| `_COMBO_MODE_JS` | JS card gộp: chuyển mode qa/vn/wb/pron/lg, đọc `window._aiFactoryMode`/localStorage, self-check vn/pron, gọi `pycmd('ai_factory_set_mode:...')` |

## LUỒNG INJECT (reviewer)

```
hooks/reviewer.py:11 _on_reviewer_question → nếu card.q() chứa 'id="lg-display"' → web.eval(_LG_JS_BODY)
hooks/reviewer.py:21 _on_reviewer_answer → detect lang → get_default_speed → web.eval("window._ankiDefaultSpeed="+spd+_SPEED_CTRL_JS)
```

## THÊM 1 LOẠI THẺ MỚI (checklist)

1. Thêm 2 hàm `tmpl_{lang}_{type}_q/a` trong `templates.py`
2. Thêm vào `LANG_TEMPLATES` registry (`templates.py:546`) cho CẢ 2 ngôn ngữ (hoặc grammar registry)
3. Thêm CSS class vào `css.py` (vào phần `_SHARED`/specific)
4. Nếu có JS game → thêm vào `shared.py` + export ở `mode/__init__.py`
5. Cập nhật `template_names` trong `Language/{lang}.py` nếu đổi tên loại thẻ

## TRAPS

1. **HTML là Mustache string** — dùng `'...'` nối chuỗi; tránh đổi nhầm thành f-string (đã có `{{...}}`).
2. Thêm CSS class → phải tồn tại trong CSS của CẢ nightMode (`.card.nightMode .xxx`).
3. `id="lg-display"` là điều kiện kích hoạt JS letter gap — không đổi tên id.
4. `_SPEED_CTRL_JS` phụ thuộc `window._ankiDefaultSpeed` — JS không được tự set cứng speed.

## VERIFY

```
python -m pytest tests/test_grammar.py tests/test_comprehensive.py -v
# + kiểm tra mắt trên Anki: thẻ 5 loại × 2 ngôn ngữ hiển thị đúng
```
