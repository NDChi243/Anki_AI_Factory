# 🌐 AnkiTool Multi-Language V15.0

> **Vocabulary Factory cho Anki** — Tạo thẻ từ vựng tiếng Nhật & tiếng Trung với AI, TTS, và interactive templates.

[![Version](https://img.shields.io/badge/version-16.0.0-blue)](manifest.json)
[![Anki](https://img.shields.io/badge/anki-%3E%3D2.1.50-green)](manifest.json)
[![Python](https://img.shields.io/badge/python-%3E%3D3.9-yellow)](manifest.json)

---

## ✨ Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| 📎 **Kẹp File Tham Khảo** | Đính kèm TXT/MD/CSV/PDF/DOCX/XLSX làm tài liệu → AI đọc nội dung để trích xuất từ vựng/ngữ pháp. (DeepSeek chỉ nhận text → add-on tự trích text tại máy.) |
| 📘 **Ngữ pháp** | Note Type ngữ pháp riêng (Nhật & Trung): thẻ 2 chiều "Cấu trúc→Nghĩa" & "Nghĩa→Cấu trúc", AI trích xuất pattern + công thức + cách dùng + ví dụ. |
| 🤖 **AI Trích Xuất** | Dùng OpenAI/DeepSeek/Ollama để trích xuất từ vựng từ văn bản. Tự động tránh từ đã có trong deck. |
| 💬 **AI Chat** | Trợ lý học tập thông minh, hiểu ngữ cảnh Anki của bạn. |
| 🎤 **TTS Đa Engine** | Edge TTS (chất lượng cao) → gTTS (fallback) → VoiceVox (local JP). |
| 📝 **5 Loại Thẻ** | Nhật→Việt, Việt→Nhật, Ghép chữ, Furigana/Pinyin, Ẩn chữ cái. |
| 🎮 **Interactive Games** | Word Building (drag & drop), Handwriting practice, Letter Gap. |
| 🔍 **Kiểm Định Thông Minh** | Phát hiện từ mới, cập nhật, trùng lặp, và từ cùng mặt chữ khác nghĩa. |
| ⚡ **Speed Control** | Tùy chỉnh tốc độ audio 0.25×–4.0× ngay trên thẻ review. |

---

## 📦 Cài đặt

### Yêu cầu
- Anki >= 2.1.50
- Python >= 3.9
- `edge-tts` (tự động cài qua pip khi dùng lần đầu)
- `gtts` (optional, fallback)

### Cài đặt thủ công
```bash
# 1. Vào thư mục addons của Anki
cd %APPDATA%/Anki2/addons21/

# 2. Clone repo
git clone https://github.com/your-username/AnkiTool_Integrated.git

# 3. Khởi động lại Anki
```

### Cấu hình AI
1. Mở Anki → Tools → **AnkiTool Multi-Lang V15** (Ctrl+Shift+I)
2. Bấm **⚙️ Cài Đặt API**
3. Nhập API Key từ [DeepSeek](https://platform.deepseek.com/api_keys) hoặc OpenAI
4. Chọn preset hoặc nhập thủ công Base URL + Model
5. Bấm **🧪 Test Kết Nối** → **💾 Lưu**

### Hỗ trợ AI Providers
- **DeepSeek** (`deepseek-chat`, `deepseek-reasoner`)
- **OpenAI** (`gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`)
- **Ollama** (local, miễn phí)
- **LM Studio** (local, miễn phí)
- **OpenRouter** (multi-model gateway)

---

## 🚀 Sử dụng nhanh

### Cách 1: Import JSON thủ công
```json
[
  {
    "front": "食べる",
    "furigana": "たべる",
    "meaning": "ăn",
    "jlptlevel": "N5",
    "topic": "Động từ",
    "example": "毎日ご飯を食べるよ。",
    "example_vn": "Hàng ngày tớ ăn cơm đó."
  }
]
```
1. Dán JSON vào khung bên trái
2. Chọn Deck đích
3. Bấm **🌪️ Kiểm Định** → kiểm tra kết quả
4. Bấm **🚀 XUẤT XƯỞNG**

### Cách 2: AI Trích Xuất
1. Dán văn bản tiếng Nhật/Trung vào ô "📝 Dán văn bản..."
2. (Optional) Thêm lời nhắn: "Chỉ lấy từ N3+, chủ đề ẩm thực"
3. Bấm **🤖 AI Trích Xuất**
4. Xem trước, chỉnh sửa, xóa nếu cần
5. Bấm **✅ CHẤP NHẬN & ĐỔ VÀO XƯỞNG**

### Cách 3: AI Chat
1. Viết câu hỏi/yêu cầu vào ô text
2. Bấm **💬 Gửi**
3. AI sẽ phân tích hệ thống Anki và trả lời
4. Nếu AI đề xuất từ vựng → bấm **✅ Đổ Vào Xưởng**

---

## 🏗️ Cấu trúc dự án

```
AnkiTool_Integrated/
├── __init__.py           # Entry point + Main Dialog
├── audio/                # TTS engines (Edge, gTTS, VoiceVox)
├── Language/             # Language configs (Japanese, Chinese)
├── mode/                 # Card templates, CSS, JS games
├── ui/                   # UI dialogs (AiChatDialog)
├── workers/              # Background threads (import, AI, preview)
├── utils/                # AI extractor, JSON parser, logging, history
├── tests/                # Unit tests
├── README.md             # ← File này
├── CODE_MAP.md           # Bản đồ code cho AI/Vibe coding
├── UPGRADE_GUIDE.md      # Hướng dẫn nâng cấp & bảo trì
├── REFACTOR_PLAN.md      # Kế hoạch tái cấu trúc
└── CHANGELOG.md          # Lịch sử phiên bản
```

---

## 🧪 Chạy tests

```bash
# Cài pytest
pip install pytest

# Chạy tất cả tests
cd AnkiTool_Integrated
python -m pytest tests/ -v

# Chạy test cụ thể
python -m pytest tests/test_json_parser.py -v
python -m pytest tests/test_audio_engine.py -v
```

---

## 🤝 Đóng góp

1. Fork repo
2. Tạo branch: `git checkout -b feature/tinh-nang-moi`
3. Commit: `git commit -m "Thêm tính năng X"`
4. Push: `git push origin feature/tinh-nang-moi`
5. Tạo Pull Request

**Trước khi PR, vui lòng:**
- [ ] Chạy `python -m pytest tests/ -v`
- [ ] Test trên Anki thật
- [ ] Cập nhật `CHANGELOG.md`
- [ ] Đảm bảo không có API key trong code

---

## 📄 License

MIT License — Xem file `LICENSE`

---

## ⚠️ Bảo mật

- **Không commit `utils/ai_config.json`** — file này đã được thêm vào `.gitignore`
- Dùng `utils/ai_config.example.json` làm mẫu
- Nếu lỡ commit API key, **revoke key ngay** trên dashboard của provider

---

## 🙏 Credits

- [Anki](https://apps.ankiweb.net/) — Nền tảng flashcard mã nguồn mở
- [edge-tts](https://github.com/rany2/edge-tts) — Microsoft Edge TTS Python wrapper
- [DeepSeek](https://deepseek.com/) — AI API giá rẻ cho tiếng Á Đông
