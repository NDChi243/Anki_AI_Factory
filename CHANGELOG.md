# 📋 CHANGELOG

## [V17.1] — 2026-08-12

### ✨ Added
- **🌐 Chế độ chuyển ngôn ngữ EN–VI (không hardcode)**: Hệ thống i18n `t()` phủ rộng lên UI/workers; vẫn còn vài chỗ hổng sẽ hoàn thiện dần (utils/i18n.py).
- **📜 LICENSE (MIT)** + **⚙️ GitHub Actions CI** (chạy pytest 3.11/3.12) + **🤝 CONTRIBUTING.md** — nâng mức sẵn sàng cộng đồng.
- **✏️ Sửa Prompt & Schema AI (không cần sửa code)**: Nút "✏️ Sửa Prompt / Schema AI" trong Cài Đặt AI mở dialog chỉnh System Prompt + mẫu JSON cho từng ngôn ngữ (Từ vựng & Ngữ pháp) — đổi luật trích xuất, schema, field_count ngay trên giao diện (ui/prompt_editor.py).
- **🗂 Field Map Editor (Mức 1 — đóng "schema lock-in" ở lớp thẻ)**: Tab "🗂 Field Map" trong dialog — bảng map key JSON (tự sinh từ template đã sửa) → Field Anki (chỉnh được, key mới tự suy tên field). Khi Lưu: **tự THÊM field mới vào Note Type** (6 model: 3 ngôn ngữ × từ vựng/ngữ pháp nếu đã tồn tại); mọi nơi dùng `self._cfg()` (kiểm định/merge/import/tạo model) đều nhận `json_field_map` + `all_fields` HIỆU LỰC (defaults + ghi đè). Lưu trong `utils/ai_prompts.json` (`field_map`).
- **🃏 Card Render tự động (Mức 2 — field mới TỰ HIỆN TRÊN THẺ)**: `mode/card_render.py` — sau khi thêm field mới, khối "extra fields" được APPEND vào cuối template thẻ (không phá template gốc), mỗi field bọc `{{#Field}}...{{/Field}}` (rỗng thì ẩn) + inline styles. Cột **"Hiển thị"** trong Field Map chọn vị trí: Chỉ mặt sau / Cả hai mặt / Chỉ mặt trước (`card_show` trong `ai_prompts.json`). `get_or_create_model`/`_force_rebuild_model`/editor save đều dùng builder → **Lưu xong là thẻ hiện field mới ngay**, không cần sửa template tay.
- **🎛️ Prompt Config ra ngoài**: Prompt + JSON template lưu trong `utils/ai_prompts.json` (gitignored) qua `utils/prompt_config.py`; `get_system_prompt()`/`get_json_template()` trả giá trị hiệu lực (defaults + ghi đè), có validate JSON, preview prompt đầy đủ, Reset mặc định.
- **⚡ Cache tự invalidate khi sửa prompt**: Cache key của AI giờ gồm `get_prompt_signature()` (md5 phần ghi đè prompt) → sửa prompt/schema → kết quả AI cũ tự bị bỏ, không dùng lại.

### 🔧 Changed
- **utils/batch_processor.py**: chuyển từ dùng `_SYSTEM_PROMPTS/_JSON_TEMPLATES/_GRAMMAR_*` (dict cứng) sang `get_system_prompt()`/`get_json_template()` (tôn trọng ghi đè).
- **utils/ai_extractor.py**: `_PROMPT_VERSION` 3 → 4 (đổi format cache key); `get_json_template()`/`get_grammar_json_template()` giờ đọc từ prompt_config.
- **__init__.py `_cfg()`**: bơm `apply_field_map_to_cfg()` → json_field_map/all_fields/card_show hiệu lực cho mọi flow (kiểm định, merge, import, tạo model).
- **__init__.py get_or_create_model/_force_rebuild_model**: dùng `mode.card_render.build_qfmt/build_afmt` → template thẻ tự append field tuỳ chỉnh.
- **Sửa lỗi gõ lặp** trong prompt Hàn: "(습니다/습니다/존댓말)" → "(습니다/존댓말)" (giúp prompt compact lại dưới 1400 ký tự).

## [V17.0] — 2026-08

### ✨ Added
- **🇰🇷 Ngôn ngữ Hàn Quốc (Korean)**: Ngôn ngữ thứ 3 — từ vựng & ngữ pháp tiếng Hàn với đầy đủ 5 chế độ học (Hàn→Việt, Việt→Hàn, Ghép chữ, Romanization, Ẩn chữ), Note Type riêng, AI prompt trích xuất (Hangul + Romanization chuẩn Revised Romanization), TTS giọng Hàn (ko-KR), bộ lọc cấp độ TOPIK I/II (Language/korean.py, mode/templates.py, mode/css.py, audio/engine.py, utils/ai_extractor.py)
- **🔤 Romanization cho tiếng Hàn**: Field Romanization + Example Romanization/Example2 Romanization hiển thị trên thẻ, đọc/ghi đầy đủ trong JSON (Language/korean.py, mode/templates.py)
- **🎓 Bộ lọc TOPIK Level**: level_choices TOPIK I/TOPIK II/1-6 trong bộ lọc cấp độ (Language/korean.py)
- **🧩 KO_WB_POOL**: Word-Building ghép chữ Hangul cho tiếng Hàn (mode/shared.py)
- **🎯 Chọn lọc & xuất xưởng theo lựa chọn**: Sau khi bấm Kiểm Định, "Thẻ chờ xuất xưởng" hỗ trợ tìm kiếm theo từ/nghĩa, lọc nhanh theo loại (✨ Mới / 🔄 Cập nhật / ⚠️ Trùng mờ / 🔍 Nghĩa khác), tích chọn từng thẻ hoặc chọn theo khoảng số "Từ-đến" — **đổi khoảng là TỰ ĐỘNG tích chọn** các thẻ trong khoảng đó (theo danh sách đang hiển thị), chọn deck đích qua deck_chooser để đẩy vào — sau khi xuất, danh sách tự cập nhật bỏ các thẻ đã xuất, cho phép đẩy tiếp nhóm còn lại sang deck khác (__init__.py)
- **💾 Giữ thẻ trong xưởng khi đóng cửa sổ**: Thẻ chờ xuất xưởng + kho hàng được lưu vào factory_state.json theo từng luồng (ngôn ngữ × từ vựng/ngữ pháp) và khôi phục khi mở lại Factory; thẻ chỉ bị xóa khi người dùng chủ động bấm "🧹 Hủy Hàng" — xóa toàn bộ hoặc xóa các thẻ đã chọn (__init__.py)
- **📚 Lịch Sử AI (xem lại & import lại)**: Nút "Lịch Sử AI" mở dialog liệt kê toàn bộ từ vựng đã lưu (AI trích xuất / import) — tìm theo từ/nghĩa, lọc theo ngôn ngữ, tích chọn nhiều từ rồi "📥 Đưa Vào Xưởng" để Kiểm Định & xuất xưởng lại, xem được ngay cả sau khi đóng Factory. `add_to_import_history` giờ lưu cả item gốc để tái dựng đầy đủ (ui/history_dialog.py, utils/ai_extractor.py: get_import_history_items)

### 🔧 Changed
- **Version bump**: Tất cả model names V16.0 → V17.0 (Language/japanese.py, Language/chinese.py)
- **old_model_names**: Thêm V16.0 vào danh sách migration cho Nhật & Trung
- **audio/engine.py**: `_MODEL_LANG_MAP` thêm V17.0 + Korean models (ko)
- **i18n**: Thêm `lang_korean`, cập nhật title/version sang V17.0 (utils/i18n.py)
- **manifest.json**: version 17.0.0, thêm `korean` vào languages/keywords
- **AI prompts**: `_PROMPT_VERSION` 2 → 3 (invalidate cache) do thêm Korean prompts (utils/ai_extractor.py)

### 🐛 Fixed
- N/A

## [V16.1] — 2026-08

### ✨ Added
- **🎯 Card gộp 5 chế độ (1 từ = 1 card)**: Thay vì 1 từ tạo 5 card riêng (Nhật→Việt, Việt→Nhật, Ghép chữ, Furigana, Ẩn chữ) giờ chỉ tạo **1 card duy nhất** → deck đếm đúng số từ vựng, hết tình trạng số thẻ học nhân 5. Trong card có **thanh chọn chế độ** chuyển đổi bằng JS (mode/), đồng bộ mode qua `pycmd('ai_factory_set_mode:...')`
- **🎛️ Nút chọn chế độ học ở màn hình Overview**: Patch `Overview._table` (wrap, không ghi đè Onigiri) → chèn bộ chọn mode + nút "Study now" cạnh nút của Onigiri; mode lưu vào `mw.col.conf` (hooks/overview_mode.py)
- **🔁 Migration tự động 5-card → 1-card**: Model cũ (5 template) khi tái tạo sẽ giữ card mode chính + lịch sử học, xóa 4 card thừa của từng note (__init__.py: `_drop_extra_combo_cards`)
- **⬇️ Dropdown chọn mode trong Factory**: Thêm chọn chế độ học mặc định trong add-on, đồng bộ với Study now (__init__.py)

### 🔧 Changed
- **LANG_TEMPLATES**: Mỗi ngôn ngữ chỉ còn 1 cặp template combo (trước đây 5 cặp)
- **template_names**: "1. Nhật → Việt" → "1. Tổng hợp (5 chế độ)" (Language/*.py)
- **manifest.json**: `template_count` 5 → 1, thêm `study_modes`
- **Type answer**: Mode chính (Nhật→Việt) dùng `{{type:Meaning}}` chuẩn Anki; Việt→Nhật & Furigana/Pinyin tự kiểm tra bằng JS (mode/shared.py `_COMBO_MODE_JS`)

## [V16.0] — 2026-08

### ✨ Added
- **💾 Lưu trạng thái 2 luồng × 2 ngôn ngữ**: Text + file kẹp của Từ vựng & Ngữ pháp (mỗi ngôn ngữ) được lưu riêng vào factory_state.json, khôi phục khi mở lại Factory — không lẫn nhau, đỡ phải gửi/gọi lại AI. "Xóa Text"/"Bỏ File" sẽ xóa luồng đó (__init__.py)
- **🔪 Cắt đoạn mịn hơn**: chunk mặc định 12k → **8k ký tự/lần** (config 3k-15k) → chất lượng ví dụ/ngữ pháp cao hơn, vẫn xử lý hết văn bản dài (utils/ai_extractor.py, ui/ai_settings.py)
- ** Ngữ pháp như giảng viên đọc giáo trình**: Prompt ngữ pháp mới — đọc toàn bộ văn bản để hiểu ngữ cảnh + từ vựng đi kèm, tạo ví dụ đa dạng; CÙNG PATTERN–KHÁC NGHĨA → nhiều thẻ riêng; ĐÁNH DẤU pattern trong ví dụ bằng `<b>…</b>` + CSS màu nổi bật (utils/ai_extractor.py, mode/css.py)
- **🐛 Fix "Đổ vào xưởng" ở chế độ ngữ pháp**: Dialog Xem Trước giờ hiểu chế độ ngữ pháp (cột Pattern/Usage/Explanation thay vì simplified/traditional), lọc đúng key pattern, tái tạo dùng prompt ngữ pháp; Kiểm Định coi "cùng pattern–khác nghĩa" là thẻ MỚI (ui/ai_preview.py, __init__.py)
- **📏 Mở rộng nội dung xử lý**: Văn bản dài 50k-100k+ được xử lý HẾT nhờ tự chia đoạn (chunk 8k mặc định, config 3k-15k) → không còn bị cắt. AI Chat cap đọc theo cài đặt (mặc định 45k) (utils/ai_extractor.py, __init__.py, ui/ai_settings.py)
- **🐛 Fix JSON bị cắt (tràn output)**: DeepSeek giới hạn output ~8192 token/response → chunk quá lớn khiến JSON đứt giữa chừng. Đã: chunk mặc định 8k + cap 15k, tự hạ config cũ (45k→15k) khi đọc, cảnh báo rõ khi output bị cắt, và thông báo lỗi gợi ý giảm độ dài (utils/ai_extractor.py, ui/ai_settings.py)
- **🧠 Mức độ suy nghĩ (reasoning_effort)**: Bộ chọn Thấp/Trung bình/Cao trong Cài Đặt AI → truyền `reasoning_effort` vào mọi request (trích xuất, ngữ pháp, batch, chat). DeepSeek: chat = nhanh/rẻ, reasoner = sâu/đắt (utils/ai_extractor.py, utils/batch_processor.py, ui/ai_settings.py)
- **⚡ Tối ưu Token & chất lượng AI**: Chỉ gửi từ vựng/ngữ pháp trùng với nội dung vào prompt (thay vì toàn bộ deck → giảm mạnh input); nén system prompt giữ nguyên chất lượng; hướng dẫn output gọn (explanation ≤2 câu, ví dụ 5-12 từ); tổng hợp token/chi phí theo toàn bộ chunk; tránh trích trùng qua biên giới đoạn (utils/ai_extractor.py, utils/batch_processor.py)
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
