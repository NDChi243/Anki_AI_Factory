---
name: ui-layer
description: Lớp UI — ui/ (dialogs + theme) + i18n. Đọc khi sửa dialog, theme glassmorphism, chuỗi hiển thị.
---

# 🖥️ SKILL-06: UI LAYER

> PyQt5 (aqt.qt). Mọi chuỗi hiển thị phải qua `t()` i18n. Theme glassmorphism qua `ui/theme.py`.

## CÁC DIALOG

| Dialog | File:Dòng | Entry point | Ghi chú |
|--------|-----------|-------------|---------|
| `AiChatDialog` | `ui/ai_dialogs.py:15` | `from ui import AiChatDialog` | Hiển thị reply AI + vocab JSON; `_format_reply`:160 (bold/code/newline→HTML) |
| AI Settings | `ui/ai_settings.py:19` | `show_ai_settings_dialog(parent)` | Cấu hình API key/base/model/temp/chunk/reasoning; `_test_ai_connection`:204; nút "✏️ Sửa Prompt / Schema AI" mở Prompt Editor |
| Prompt Editor | `ui/prompt_editor.py:64` | `show_prompt_editor_dialog(parent)` | Sửa System Prompt (RAW chứa `{{JSON_TEMPLATE}}`) + JSON template + tab "🗂 Field Map" (map key→Field Anki + cột "Hiển thị" front/back/both, tự sinh từ template, tự thêm field + đồng bộ template thẻ khi Lưu qua `_sync_models_after_save`); validate JSON, preview prompt, Reset mặc định; lưu `utils/ai_prompts.json` qua `utils.prompt_config` |
| AI Preview | `ui/ai_preview.py:19` | `show_ai_preview_dialog(parent, vocab_list, lang, ...)` | Xem/sửa/xóa/tái tạo thẻ; hiểu chế độ grammar (cột Pattern) |
| Batch | `ui/batch_dialog.py:15` | `BatchWordListDialog(lang, existing_words, parent, grammar)` | Paste danh sách lớn + batch AI + tổ chức deck |
| Diff Meaning | `ui/verify_dialog.py:13` | `show_diff_meaning_dialog(parent, prepared_data, cfg)` | Báo cáo từ cùng mặt chữ khác nghĩa |
| Theme | `ui/theme.py` | `apply_theme(widget,cfg)`, `ThemeDialog`, `snap_left/right/maximize` | Glassmorphism; config `utils/ui_theme.json` |

## THEME (`ui/theme.py` — 463 dòng)

- Config file: `utils/ui_theme.json`, `THEME_FILE:23`, `DEFAULT_CONFIG:28` (`preset, accent, glass_alpha, font_size, radius`).
- `PRESETS:36` (glass_dark, glass_light, midnight...).
- API: `build_stylesheet(cfg)`, `apply_theme(widget, cfg)`, `load_config()`, `save_config(cfg)`, `ThemeDialog`, `snap_left/snap_right/snap_maximize`.
- Import trong `__init__.py:53-56`: `load_config as load_theme_config, apply_theme, ThemeDialog, snap_maximize`.

## I18N (`utils/i18n.py` — 376 dòng)

```python
from utils.i18n import t, set_language, get_language, SUPPORTED_LANGUAGES
t("key", lang=None, **kwargs)   # trả về chuỗi đã format; fallback vi; thiếu key → trả về chính key
set_language("vi"|"en")         # lưu vào utils/i18n_config.json
SUPPORTED_LANGUAGES = {"vi": ..., "en": ...}   # dòng 24
```

- **Bắt buộc**: UI mới dùng `t("new_key")` — không hardcode tiếng Việt.
- Thêm key: thêm vào `_TRANSLATIONS` (dòng 35) với cả `vi` + `en` (test `test_i18n.py` kiểm tra toàn bộ key có đủ 2 ngôn ngữ).
- Test: `python -m pytest tests/test_i18n.py -v`

## TRAPS

1. `aqt.qt` cấm import ở top-level trong các module không phải `__init__.py` khi test offline → tests dùng mock hoặc import nội bộ (trong hàm).
2. Dialog nên `setWindowFlags(... | Qt.WindowType.WindowMinMaxButtonsHint | WindowMaximizeButtonHint)` để cho phép phóng to (pattern có sẵn trong các dialog).
3. Giữ `_format_reply` logic: `**text**`→`<b>`, `` `code` ``→`<code>`, `\n`→`<br>`.
4. Không chặn UI thread — mọi AI/import qua worker (SKILL-05).

## VERIFY

```
python -m pytest tests/test_comprehensive.py tests/test_i18n.py -v
```
