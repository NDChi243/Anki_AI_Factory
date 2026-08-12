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

## I18N (`utils/i18n.py` — 1600+ dòng)

```python
from utils.i18n import t, set_language, get_language, toggle_language, SUPPORTED_LANGUAGES
from utils.i18n import add_language_listener, remove_language_listener
t("key", lang=None, **kwargs)   # trả về chuỗi đã format; fallback vi; thiếu key → trả về chính key
set_language("vi"|"en")         # đổi + lưu utils/i18n_config.json + thông báo listener
toggle_language()               # chuyển vi ⇄ en (nút 🌐 trong cửa sổ chính)
add_language_listener(cb)       # đăng ký callback refresh UI mượt mà khi đổi ngôn ngữ
SUPPORTED_LANGUAGES = {"vi": ..., "en": ...}
```

- **Bắt buộc**: UI dùng `t("new_key")` — không hardcode tiếng Việt.
- **Prompt AI song ngữ (VI/EN)**: khi UI = `en`, AI sinh nghĩa + dịch ví dụ BẰNG TIẾNG ANH.
  Nằm trong `utils/ai_extractor.py` (`_SYSTEM_PROMPTS_EN`/`_JSON_TEMPLATES_EN`/`_GRAMMAR_*_EN`)
  + `utils/prompt_config.py` (`_ui_is_english()`, `_default_system_prompt` chọn theo `get_language()`).
  Bump `_PROMPT_VERSION`/`PROMPT_CONFIG_VERSION` khi sửa prompt.
  Lưu ý: nếu `utils/ai_prompts.json` có override của người dùng → override thắng (bỏ qua ngôn ngữ UI).
- **Nhãn Mode (1. Japanese→English)**: dùng `study_mode_labels(lang)` trong `utils/i18n.py`
  (cả dropdown Mode `__init__.py:_sync_study_mode_combo` lẫn selector Overview `hooks/overview_mode.py`).
- **Nút toggle VI/EN**: thanh toolbar cửa sổ chính (`__init__.py` — `self.btn_lang_toggle` → `_toggle_ui_language`). `set_language()` gọi `_notify_language_listeners()` → `AnkiSmartFactory._retranslate_ui()` cập nhật toàn bộ chuỗi tĩnh (label/button/tooltip/placeholder/counts) + `_rebuild_preview()` hậu tố thẻ.
- **Cửa sổ chính** có `_retranslate_ui()` (`__init__.py`) — nơi duy nhất set text cho mọi widget `self.*`. Dialog khác đọc `t()` tại thời điểm dựng → mở lại sau khi đổi ngôn ngữ là hiển thị ngôn ngữ mới.
- Thêm key: thêm vào `_TRANSLATIONS` với cả `vi` + `en` (test `test_i18n.py` kiểm tra toàn bộ key có đủ 2 ngôn ngữ).
- Test: `python -m pytest tests/ -q`

## TRAPS

1. `aqt.qt` cấm import ở top-level trong các module không phải `__init__.py` khi test offline → tests dùng mock hoặc import nội bộ (trong hàm).
2. Dialog nên `setWindowFlags(... | Qt.WindowType.WindowMinMaxButtonsHint | WindowMaximizeButtonHint)` để cho phép phóng to (pattern có sẵn trong các dialog).
3. Giữ `_format_reply` logic: `**text**`→`<b>`, `` `code` ``→`<code>`, `\n`→`<br>`.
4. Không chặn UI thread — mọi AI/import qua worker (SKILL-05).

## VERIFY

```
python -m pytest tests/test_comprehensive.py tests/test_i18n.py -v
```
