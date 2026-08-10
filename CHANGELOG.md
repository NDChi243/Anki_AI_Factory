# 📋 CHANGELOG

## [V16.0] — 2026-08

### ✨ Added
- **📎 Kẹp file tài liệu tham khảo**: Đính kèm TXT/MD/CSV/PDF/DOCX/XLSX → AI đọc nội dung file làm tài liệu để trích xuất từ vựng/ngữ pháp. Auto-cài python-docx/openpyxl khi thiếu (utils/ai_extractor.py, __init__.py)
- **📘 Ngữ pháp (Grammar Note Type)**: Chế độ thẻ ngữ pháp riêng cho tiếng Nhật & Trung — Note Type riêng + template 2 chiều (Cấu trúc→Nghĩa, Nghĩa→Cấu trúc) + AI prompt trích xuất pattern/cách dùng/công thức (Language/*.py, mode/templates.py, mode/css.py, utils/ai_extractor.py)
- **Batch AI Processing**: Xử lý danh sách hàng trăm/nghìn từ qua AI (ui/batch_dialog.py, utils/batch_processor.py, workers/batch_workers.py)
- **Two-Pass AI Architecture**: Pass 1 làm giàu từ vựng, Pass 2 AI tổ chức Parent/Sub Deck
- **i18n**: Hỗ trợ tiếng Việt + English (utils/i18n.py, 70+ translation keys)
- **AES-GCM Encryption**: Mã hóa API key at rest với Fernet/PBKDF2
- **Incremental Deck Cache**: Cache thông minh, chỉ query notes mới (utils/deck_cache.py)
- **Pre-commit Hooks**: black, ruff, security scanning (.pre-commit-config.yaml)
- **Kiến trúc module hóa**: Tách deck_cache, i18n, workers, UI dialogs, hooks
- **56 automated tests**: Unit + integration + batch processor tests

### 🔧 Changed
- **Version bump**: Tất cả model names V15.0 → V16.0
- **old_model_names**: Thêm V15.0 vào danh sách migration
- **Logging system**: Thay thế toàn bộ print() bằng logging module
- **CSS refactored**: Shared base CSS, giảm 80% trùng lặp
- **Thread safety**: threading.Lock cho voice/speed settings
- **Background Deck Scan**: Không chặn UI khi quét deck lớn
- **API key**: Xóa khỏi source code, thêm .gitignore + example file

### 🐛 Fixed
- 36 bare `except:` → `except Exception:`
- 18 `print()` → logging
- `AudioEngine` thread safety (Lock cho shared state)
- Deck scan chặn UI → DeckScanWorker background thread

---

## [V15.0] — 2024-07

### ✨ Added
- AI Chat với system prompt "GIA SƯ NGÔN NGỮ" có context Anki
- Lịch sử import từ vựng (import_history.json) — AI biết từ nào đã có
- Dialog "Nghĩa Khác" — phát hiện từ cùng mặt chữ nhưng khác nghĩa
- Tốc độ phát audio tùy chỉnh (0.25×–4.0×), lưu riêng từng ngôn ngữ
- Speed Control overlay khi review thẻ
- Nút dừng AI (chat + extract)
- Đồng hồ đếm thời gian AI đang chạy
- Retry logic cho API calls (2 lần, timeout thông minh)
- Fallback reasoning_content cho DeepSeek Reasoner
- Hỗ trợ OpenRouter, LM Studio presets
- Nút "Tái Tạo Model" cập nhật template/CSS

### 🔧 Changed
- Voice JA: chỉ còn Nanami & Keita (AoiNeural, DaichiNeural đã bị Microsoft loại bỏ)
- Cache AI: TTL 7 ngày (từ permanent)
- System prompt AI: yêu cầu ví dụ "có hồn", khẩu ngữ tự nhiên
- Import history: tách biệt Japanese/Chinese rõ ràng
- UI: thêm preset buttons cho API settings

### 🐛 Fixed
- DeepSeek Reasoner trả về content rỗng → fallback reasoning_content
- Timeout khi gọi model reasoning → timeout 600s
- Lỗi font tiếng Trung trên một số system

---

## [V14.0] — 2024-06

### ✨ Added
- Hỗ trợ tiếng Trung (Chinese)
- Multi-language architecture (Language/ package)
- AI trích xuất từ vựng (OpenAI/DeepSeek/Ollama)
- Preview & chỉnh sửa thẻ sau AI extract
- TTS đa engine: Edge TTS, gTTS, VoiceVox
- 5 loại thẻ: Nhật→Việt, Việt→Nhật, Ghép chữ, Furigana, Ẩn chữ cái
- Word Building game (drag & drop tiles)
- Handwriting practice canvas
- Letter Gap game (điền chữ cái bị ẩn)
- Kiểm định lô hàng (verify batch) với phát hiện trùng lặp
- Import từ JSON/TXT file

---

## [V13.0 và trước] — 2024-05

- Chỉ hỗ trợ tiếng Nhật
- Import JSON thủ công
- Template cơ bản
- Audio với Google TTS
