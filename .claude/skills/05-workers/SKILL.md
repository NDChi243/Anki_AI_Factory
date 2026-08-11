---
name: workers
description: Các background thread — workers/ (7 thread). Signal, run() flow, giao tiếp UI↔thread. Đọc khi sửa bất kỳ tác vụ nền nào.
---

# ⚙️ SKILL-05: WORKERS (Background Threads)

> Tất cả đều là `QThread` từ `aqt.qt`. Re-export qua `workers/__init__.py`. UI kết nối signal trong `__init__.py`.

## DANH SÁCH THREAD

| Class | File:Dòng | Signals | Chức năng |
|-------|-----------|---------|-----------|
| `ImportWorker` | `workers/import_worker.py:23` | — (dùng callbacks) | Import add/update + audio song song (thread pool `_generate_audio_safe`:183), report `{added,updated,audio_gen,errors}` |
| `PreviewThread` | `workers/ai_workers.py:20` | `done(str)` | Preview giọng Edge TTS → filepath |
| `AiExtractThread` | `workers/ai_workers.py:52` | `progress(str)`, `finished(list)`, `error(str)` | Gọi `extract_vocabulary_long_text`/`extract_grammar_long_text` |
| `AiChatThread` | `workers/ai_workers.py:104` | `progress(str)`, `finished(dict)`, `error(str)` | Gọi `chat_with_ai` với history |
| `DeckScanWorker` | `workers/deck_scan_worker.py:14` | `progress(str)`, `finished(list)`, `error(str)` | Quét deck lấy existing words (dùng `get_existing_vocab_from_deck`) |
| `BatchProcessThread` | `workers/batch_workers.py:18` | `progress(str)`, `batch_progress(int,int)`, `finished(list)`, `error(str)` | `process_large_word_list`; báo ước tính cost trước |
| `DeckOrganizerThread` | `workers/batch_workers.py:88` | `progress`, `finished(dict)`, `decks_created(dict)`, `error` | `organize_decks_with_ai` + tùy chọn `create_decks_from_organization` |

## PATTERN CHUẨN (tạo thread mới phải theo)

```python
class MyThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)   # hoặc dict
    error = pyqtSignal(str)

    def __init__(self, ...):
        super().__init__()
        self._is_running = True

    def run(self):
        try:
            # ... gọi hàm xử lý; emit progress qua lambda
            self.progress.emit("...")
            self.finished.emit(result)
        except Exception as e:
            logger.warning("...: %s", e)
            self.error.emit(str(e))

    def stop(self):
        self._is_running = False   # dùng với should_abort callback
```

## CÁCH KẾT NỐI TỪ UI (`__init__.py`)

```python
self._ai_thread = AiExtractThread(text, lang, custom_instruction, existing_words, grammar)
self._ai_thread.progress.connect(self._on_ai_progress)     # :1518
self._ai_thread.finished.connect(self._on_ai_finished)     # :1523
self._ai_thread.error.connect(self._on_ai_error)           # :1541
self._ai_thread.start()
# Hủy: self._ai_thread.stop() + wait() (xem _cancel_ai_chat:1773)
```

## QUY TẮC

1. **Không chạm UI widget trực tiếp trong thread** — chỉ emit signal; UI slot mới cập nhật widget.
2. **Không gọi Anki API (mw.col) không an toàn trong thread** — DeckScan/ImportWorker có ngoại lệ được bọc try/except.
3. Luôn có `_is_running` để `stop()`/`should_abort` hoạt động.
4. Mọi exception trong `run()` → `error.emit`, không để crash Anki.
5. Giữ reference thread trong self (vd `self.import_worker`) để tránh bị GC giữa chừng.

## VERIFY

```
python -m pytest tests/test_comprehensive.py tests/test_integration.py -v
```
