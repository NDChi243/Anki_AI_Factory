# 🚀 UPGRADE GUIDE — Hướng dẫn nâng cấp & bảo trì cho Vibe Coding

> **Mục tiêu**: Tiết kiệm token khi dùng AI (ChatGPT, Claude, Cursor) để sửa/nâng cấp add-on. Mỗi section là một "task card" có thể copy-paste cho AI.

---

## 📋 MỤC LỤC

1. [Quy tắc chung](#-quy-tắc-chung)
2. [Task Cards](#-task-cards)
3. [Checklist trước khi release](#-checklist-trước-khi-release)
4. [Debugging](#-debugging)

---

## 🧭 QUY TẮC CHUNG

### Prefix cho mọi vibe code session
```
[Context] Đây là Anki add-on Python (AnkiTool_Integrated V15.0).
Cấu trúc: xem CODE_MAP.md.
Global state: mw (Anki main window), mw.col (collection DB).
UI framework: PyQt5 (aqt.qt).
Không được import Anki modules ở top-level ngoài __init__.py.
Luôn dùng try/except khi gọi Anki API.
```

### Nguyên tắc vàng
1. **Không sửa `__init__.py` trừ khi bất khả kháng** — file này đã 2515 dòng, cần tách trước khi sửa thêm.
2. **Luôn kiểm tra `CODE_MAP.md`** trước khi hỏi AI sửa gì.
3. **Mỗi task sửa ĐÚNG 1 file** nếu có thể.
4. **Test trên Anki thật** trước khi commit.

---

## 📝 TASK CARDS

Copy-paste nguyên block dưới đây cho AI:

---

### 🔥 TASK-01: Xóa API Key bị lộ (KHẨN CẤP)

```
[Task] Xóa API key khỏi utils/ai_config.json.
Thay bằng chuỗi rỗng "". Không xóa file. 
Tạo file utils/ai_config.example.json với format giống hệt nhưng api_key để trống.
Thêm utils/ai_config.json vào .gitignore.
```

**File cần sửa**: `utils/ai_config.json`, `.gitignore`  
**File cần tạo**: `utils/ai_config.example.json`

---

### ⚡ TASK-02: Tách ImportWorker ra file riêng

```
[Task] Di chuyển class ImportWorker từ __init__.py (dòng 51-173) sang file mới workers/import_worker.py.
Giữ nguyên code, chỉ thay đổi import path.
Trong __init__.py, import lại từ workers/import_worker.py.
Tạo thư mục workers/ và file workers/__init__.py.
```

**File cần tạo**: `workers/__init__.py`, `workers/import_worker.py`  
**File cần sửa**: `__init__.py`

---

### ⚡ TASK-03: Tách PreviewThread & AI threads ra file riêng

```
[Task] Di chuyển các class sau sang file mới workers/ai_workers.py:
- PreviewThread (__init__.py:179-207)
- AiExtractThread (__init__.py:2203-2238)
- AiChatThread (__init__.py:2243-2279)
Giữ nguyên code. Import lại trong __init__.py.
```

**File cần tạo**: `workers/ai_workers.py`  
**File cần sửa**: `__init__.py`

---

### ⚡ TASK-04: Tách AI Dialogs ra file riêng

```
[Task] Di chuyển class AiChatDialog (__init__.py:2285-2457) sang ui/ai_dialogs.py.
Tạo thư mục ui/ và file ui/__init__.py.
Import lại trong __init__.py.
```

**File cần tạo**: `ui/__init__.py`, `ui/ai_dialogs.py`  
**File cần sửa**: `__init__.py`

---

### ⚡ TASK-05: Thêm logging system

```
[Task] Tạo module utils/logger.py với hàm setup_logging().
Thay thế TẤT CẢ print() statement trong project bằng logging.debug/info/warning/error.
Format log: "[AnkiTool] [LEVEL] message".
Log ra file trong thư mục addon (anki_tool.log) + console.
Thêm log rotation (giới hạn 5MB, giữ 3 file cũ).
```

**File cần tạo**: `utils/logger.py`  
**File cần sửa**: Tất cả file có `print()`

---

### ⚡ TASK-06: Sửa bare except

```
[Task] Trong TOÀN BỘ project, thay thế:
- "except:" → "except Exception:"
- "except:" + "pass" → "except Exception: logger.debug(...)"
KHÔNG thay các except cụ thể như "except ImportError:", "except json.JSONDecodeError:".
```

**File cần sửa**: Tất cả file .py

---

### 📋 TASK-07: Tách CSS shared

```
[Task] Trong mode/css.py, tách phần CSS chung giữa Japanese và Chinese thành biến _BASE_CSS.
css_japanese() = _BASE_CSS + _JA_FONT + _JA_EXTRA + _SHARED_UI_CSS
css_chinese() = _BASE_CSS + _ZH_FONT + _ZH_EXTRA + _SHARED_UI_CSS
Giảm trùng lặp code.
```

**File cần sửa**: `mode/css.py`

---

### 📋 TASK-08: Thêm type hints

```
[Task] Thêm type hints cho tất cả function signatures trong:
- audio/engine.py
- audio/tts.py
- utils/json_parser.py
- utils/ai_extractor.py (các hàm public)

Dùng typing module: Optional, List, Dict, Callable, Any.
Không thay đổi logic.
```

**File cần sửa**: `audio/engine.py`, `audio/tts.py`, `utils/json_parser.py`, `utils/ai_extractor.py`

---

### 📋 TASK-09: Thread-safe voice settings

```
[Task] Trong audio/engine.py, bọc _selected_voice và _default_speed dicts bằng threading.Lock().
Thêm context manager hoặc decorator để auto-acquire/release lock.
Sửa get_selected_voice, set_selected_voice, get_default_speed, set_default_speed để dùng lock.
```

**File cần sửa**: `audio/engine.py`

---

### 📋 TASK-10: Viết unit tests

```
[Task] Tạo thư mục tests/ với:
- tests/test_json_parser.py: test safe_parse_json với JSON hợp lệ, không hợp lệ, nested, unicode
- tests/test_audio_engine.py: test speed_to_edge_rate với các giá trị biên
- tests/test_ai_extractor.py: test _parse_ai_json_with_comment

Dùng pytest. Mock Anki dependencies (mw).
```

**File cần tạo**: `tests/__init__.py`, `tests/test_json_parser.py`, `tests/test_audio_engine.py`, `tests/test_ai_extractor.py`

---

### 🚀 TASK-11: Hỗ trợ tiếng Hàn

```
[Task] Thêm hỗ trợ tiếng Hàn vào add-on:
1. Tạo Language/korean.py với LANG_CONFIG (model, fields, level, templates)
2. Thêm "korean" vào Language/__init__.py
3. Tạo templates trong mode/templates.py (5 loại thẻ)
4. Thêm CSS trong mode/css.py
5. Thêm voice options KR trong audio/engine.py
6. Thêm system prompt trong utils/ai_extractor.py
7. Thêm WB_POOL trong mode/shared.py
```

**File cần tạo**: `Language/korean.py`  
**File cần sửa**: `Language/__init__.py`, `mode/templates.py`, `mode/css.py`, `audio/engine.py`, `utils/ai_extractor.py`, `mode/shared.py`

---

### 🚀 TASK-12: i18n / Đa ngôn ngữ UI

```
[Task] Tạo module utils/i18n.py quản lý string translations.
Tạo file utils/i18n/vi.json (Tiếng Việt - default), utils/i18n/en.json (English).
Thay thế tất cả hardcoded string tiếng Việt trong UI bằng _("string_key").
Hàm _() tự động detect ngôn ngữ từ Anki config hoặc fallback về tiếng Việt.
```

**File cần tạo**: `utils/i18n.py`, `utils/i18n/vi.json`, `utils/i18n/en.json`  
**File cần sửa**: `__init__.py` (UI strings)

---

## ✅ CHECKLIST TRƯỚC KHI RELEASE

- [ ] `ai_config.json` có trong `.gitignore` ✓
- [ ] Không còn API key trong code ✓
- [ ] Tất cả `except:` đã thay bằng `except Exception:` ✓
- [ ] `logging` thay thế `print()` ✓
- [ ] Test import trong Anki: Tools → AnkiTool Multi-Lang V15 ✓
- [ ] Test AI Extract với text mẫu ✓
- [ ] Test import JSON thủ công ✓
- [ ] Test audio generation ✓
- [ ] Test reviewer hooks (speed control hiện đúng) ✓
- [ ] `CHANGELOG.md` đã cập nhật ✓

---

## 🐛 DEBUGGING

### Bật logging
```python
# Trong Anki console (Ctrl+Shift+;)
from utils.logger import setup_logging
setup_logging(level="DEBUG")
```

### Xem log
```powershell
# File log nằm ở:
Get-Content "$env:APPDATA\Anki2\addons21\AnkiTool_Integrated\anki_tool.log" -Tail 50
```

### Test AI API
```python
from utils.ai_extractor import get_api_config, extract_vocabulary_with_ai
cfg = get_api_config()
print(cfg)  # Kiểm tra config
```

### Xóa cache
```python
from utils.ai_extractor import clear_cache, invalidate_deck_cache
clear_cache()           # Xóa cache AI
invalidate_deck_cache() # Xóa cache deck vocab
```

### Reset lịch sử import
```python
from utils.ai_extractor import clear_import_history, init_import_history
clear_import_history()
init_import_history(force_rescan=True)
```
