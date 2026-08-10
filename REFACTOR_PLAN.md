# 🏗️ REFACTOR PLAN — Kế hoạch tái cấu trúc

> **Mục tiêu**: Tách monolithic `__init__.py` (2515 dòng) thành các module nhỏ, dễ bảo trì, dễ test, dễ vibe code.

---

## 📊 HIỆN TRẠNG

```
__init__.py (2515 dòng)
├── [L1-45]    Imports + path setup               (~45 dòng)
├── [L48-174]  ImportWorker + PreviewThread       (~127 dòng)
├── [L212-2198] AnkiSmartFactory (MAIN DIALOG)   (~1987 dòng)
├── [L2200-2279] AI Threads                       (~80 dòng)
├── [L2282-2457] AiChatDialog                     (~176 dòng)
├── [L2459-2499] Reviewer Hooks                   (~41 dòng)
└── [L2502-2515] Entry Point                      (~14 dòng)
```

---

## 🎯 MỤC TIÊU SAU REFACTOR

```
AnkiTool_Integrated/
├── __init__.py              ← ~50 dòng: imports + entry point + hook registration
├── config.py                ← ~30 dòng: addon metadata, version
├── workers/
│   ├── __init__.py
│   ├── import_worker.py     ← ImportWorker (~120 dòng)
│   └── ai_workers.py        ← PreviewThread + AiExtractThread + AiChatThread (~160 dòng)
├── ui/
│   ├── __init__.py
│   ├── main_dialog.py       ← AnkiSmartFactory (tách nhỏ hơn) (~600 dòng)
│   ├── ai_dialogs.py        ← AiChatDialog + AI settings dialog (~300 dòng)
│   ├── ai_preview.py        ← AI preview table + edit dialogs (~300 dòng)
│   ├── verify_dialog.py     ← Diff meaning report dialog (~200 dòng)
│   └── widgets.py           ← Shared widgets (voice selector, etc.) (~100 dòng)
├── hooks/
│   ├── __init__.py
│   └── reviewer.py          ← Reviewer hooks (~50 dòng)
├── audio/                   (giữ nguyên)
├── Language/                (giữ nguyên)
├── mode/                    (giữ nguyên)
├── utils/                   (thêm logger.py)
│   ├── logger.py            ← NEW: logging setup
│   └── i18n.py              ← NEW: translations
└── tests/
    ├── __init__.py
    ├── test_json_parser.py
    ├── test_audio_engine.py
    └── test_ai_extractor.py
```

---

## 🔨 CÁC BƯỚC THỰC HIỆN

### Phase 1: Tách workers (dễ nhất, ít rủi ro)

**Bước 1.1**: Tạo `workers/__init__.py` + `workers/import_worker.py`
- Di chuyển class `ImportWorker` (dòng 51-173)
- Thêm import cần thiết: `from audio import get_audio_multilang`, `from audio.engine import speed_to_edge_rate`
- Không thay đổi logic

**Bước 1.2**: Tạo `workers/ai_workers.py`
- Di chuyển `PreviewThread`, `AiExtractThread`, `AiChatThread`
- Giữ nguyên imports

**Bước 1.3**: Cập nhật `__init__.py`
- Import từ workers thay vì define tại chỗ
- Test: mở add-on, import vài thẻ, chạy AI extract

### Phase 2: Tách UI dialogs

**Bước 2.1**: Tạo `ui/__init__.py` + `ui/ai_dialogs.py`
- Di chuyển `AiChatDialog` class
- Tách `_show_ai_settings()` method thành module riêng hoặc giữ trong main dialog

**Bước 2.2**: Tạo `ui/ai_preview.py`
- Di chuyển `_show_ai_preview()` và các helper methods liên quan:
  - `_ai_delete_selected()`, `_ai_edit_selected_card()`
  - `_ai_regenerate_selected()`, `_ai_regenerate_all()`
  - `_get_current_vocab_from_table()`, `_finalize_ai_vocab()`

**Bước 2.3**: Tạo `ui/verify_dialog.py`
- Di chuyển `_show_diff_meaning_report()` (~200 dòng)

**Bước 2.4**: Tạo `ui/widgets.py`
- Shared widgets nếu có

### Phase 3: Tách hooks

**Bước 3.1**: Tạo `hooks/__init__.py` + `hooks/reviewer.py`
- Di chuyển `_on_reviewer_question()`, `_on_reviewer_answer()`
- Di chuyển `gui_hooks` registration

### Phase 4: Cleanup & cải thiện

**Bước 4.1**: Tạo `utils/logger.py`
- Thay thế tất cả `print()` bằng logging

**Bước 4.2**: Tạo `config.py`
- Version string, metadata

**Bước 4.3**: `__init__.py` cuối cùng chỉ còn:
```python
"""
AnkiTool Multi-Language V15.0
"""
import sys, os
_addon_root = os.path.dirname(os.path.abspath(__file__))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

from aqt import mw, gui_hooks
from aqt.qt import QAction, QKeySequence
from aqt.utils import qconnect

# Import after path setup
from ui.main_dialog import AnkiSmartFactory
from hooks.reviewer import register_hooks

# Register hooks
register_hooks()

# Menu entry
def start_smart_factory():
    mw.factory_dialog = AnkiSmartFactory(mw)
    mw.factory_dialog.show()

action = QAction("🌐 AnkiTool Multi-Lang V15", mw)
action.setShortcut(QKeySequence("Ctrl+Shift+I"))
qconnect(action.triggered, start_smart_factory)
mw.form.menuTools.addAction(action)
```

---

## ⚠️ LƯU Ý KHI REFACTOR

1. **Không refactor và thêm tính năng cùng lúc** — mỗi PR chỉ làm 1 việc.
2. **Test sau mỗi bước** trên Anki thật.
3. **Giữ nguyên function signatures** — không đổi tên hàm public.
4. **Thêm `__all__`** trong mỗi `__init__.py` để kiểm soát exports.
5. **Dùng `git`** để có thể revert nếu vỡ.

---

## 📈 LỢI ÍCH SAU REFACTOR

| Tiêu chí | Trước | Sau |
|----------|-------|-----|
| File lớn nhất | 2515 dòng | ~600 dòng |
| Số file Python | 11 | ~20 |
| Token để AI hiểu code | ~4000 | ~800 |
| Khả năng test | 0% | ~40% |
| Thời gian fix bug | 30-60 phút | 10-15 phút |
| Rủi ro merge conflict | Cao | Thấp |
