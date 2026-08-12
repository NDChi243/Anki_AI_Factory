# 🐞 COMMON BUGS — Catalogue Lỗi Thường Gặp (AnkiTool)

> Tra theo **triệu chứng** → tìm root cause → `file:line`. Mỗi lỗi mới tìm được → THÊM vào đây để lần sau 0 token.
> Cột "Verify" = test cần chạy sau khi sửa (xem SKILL-10).

## A. AI EXTRACTION (`utils/ai_extractor.py` — SKILL-02)

| # | Triệu chứng | Root cause (kiểm tra theo thứ tự) | Sửa | Verify |
|---|-------------|-----------------------------------|-----|--------|
| A1 | AI trả JSON bị **cắt giữa chừng** | Output vượt max token; chunk quá lớn | Kiểm tra `_check_truncated_output:324`; giảm chunk ≤15k; tăng max_tokens | test_token_optimization, test_length_and_reasoning |
| A2 | Reasoner model trả **content rỗng** | Nội dung nằm trong `reasoning_content` | Giữ fallback `:1055/:1407` — không bỏ | test_comprehensive |
| A3 | **API key lỗi / 401 / sai base** | Key mã hóa sai; `get_api_config:253` không decrypt được | Kiểm tra round-trip `_encrypt_api_key:59`/`_decrypt_api_key:77`; test encryption | test_comprehensive |
| A4 | **SSL error** khi dùng local (Ollama/LM Studio) | Verify cert | `_pick_ssl_context:114` local = no-verify | test_comprehensive |
| A5 | Trả **cache cũ/sai** sau khi sửa prompt | Quên bump `_PROMPT_VERSION:385` (sửa code) HOẶC `prompt_config` chưa tự invalidate | Bump version / check `get_prompt_signature()` | test_token_optimization::TestCacheVersion |
| A6 | **JSON template/field map không áp dụng** | Override `ai_prompts.json` thắng defaults; field map sai | Kiểm tra `get_field_map`/`get_card_show`; xóa override test | test_grammar |
| A7 | API chậm/retry liên tục | Timeout ngắn; network | `_http_post_json:125` retry; model reasoner timeout 600s | test_length_and_reasoning |

## B. BATCH PROCESSING (`utils/batch_processor.py` — SKILL-03)

| # | Triệu chứng | Root cause | Sửa | Verify |
|---|-------------|-----------|-----|--------|
| B1 | **Dừng giữa chừng** sau vài batch | ≥3 lỗi liên tiếp → `RuntimeError` | Đọc log tìm lỗi AI; tăng retry? kiểm tra `MAX_RETRIES=40` | test_batch_processor |
| B2 | **Rate limit / 429** | Gửi quá nhanh | `MIN_DELAY_BETWEEN_BATCHES:39` = 1.5s; không giảm | test_batch_processor |
| B3 | Deck organization **crash** | AI trả sai format | `_fallback_deck_organization:773` phải giữ — không để crash | test_batch_processor |
| B4 | **Gửi quá 100 từ/request** | Batch size lớn | `MAX_WORDS_PER_REQUEST:38`; giảm batch | test_batch_processor |
| B5 | Batch trả **cache cũ** | Sửa prompt batch quên bump version | `_PROMPT_VERSION` chung (SKILL-02) | test_batch_processor |
| B6 | **Parse word list sai delimiter** | Input không match regex | `parse_word_list` giữ nhánh JSON (`startswith("[")`) | test_batch_processor |

## C. AUDIO / TTS (`audio/` — SKILL-04)

| # | Triệu chứng | Root cause | Sửa | Verify |
|---|-------------|-----------|-----|--------|
| C1 | **Không có audio** | Voice bị Microsoft loại bỏ (AoiNeural/DaichiNeural); gTTS fallback lỗi | Kiểm tra `VOICE_OPTIONS:12` chỉ giọng còn sống; `get_audio_multilang:97` fallback | test_audio_engine |
| C2 | **Sai giọng khi review** | Model name không map lang | `_MODEL_LANG_MAP:81`/`detect_lang_from_model:92` | test_audio_engine |
| C3 | **Tốc độ sai** | rate string sai | `speed_to_edge_rate:117` (0.25-4.0 → "-50%".."+100%") | test_audio_engine |
| C4 | **Race condition** (giọng/tốc độ nhảy lung tung) | Đọc/ghi state không có lock | Mọi access `_selected_voice:40`/`_default_speed:44` trong `with _lock:` | test_audio_engine |
| C5 | **Audio sinh trên UI thread → đơ** | Gọi audio sync | Audio chỉ sinh trong thread (SKILL-05) | test_integration |

## D. WORKERS / THREAD (`workers/` — SKILL-05)

| # | Triệu chứng | Root cause | Sửa | Verify |
|---|-------------|-----------|-----|--------|
| D1 | **UI đơ / không phản hồi** | Chạm widget từ thread; signal không connect | Thread chỉ emit signal; UI slot cập nhật | test_comprehensive |
| D2 | **Thread chết giữa chừng, không báo lỗi** | Exception trong `run()` không emit `error` | Bọc try/except → `error.emit(str(e))` | test_comprehensive |
| D3 | **Hủy không dừng** | `_is_running` không kiểm tra trong loop | `stop()` + `should_abort` callback | test_comprehensive |
| D4 | **Crash Anki** khi review | Hook lỗi | `hooks/reviewer.py:45` register_hooks; model name hợp lệ | test_integration |
| D5 | **Signal disconnect / GC thread** | Mất reference thread | Giữ `self.import_worker`/`self._ai_thread` trong self | test_integration |

## E. UI / i18n / THEME (`ui/`, `utils/i18n.py` — SKILL-06)

| # | Triệu chứng | Root cause | Sửa | Verify |
|---|-------------|-----------|-----|--------|
| E1 | **Text hiển thị là key** (vd `"settings.title"`) | Thiếu key trong `_TRANSLATIONS` | Thêm đủ `vi` + `en` | test_i18n |
| E2 | **Đổi ngôn ngữ không cập nhật dialog** | Dialog đọc `t()` lúc dựng; thiếu listener | `_retranslate_ui()` (`__init__.py`) cho cửa sổ chính; dialog mở lại | test_i18n |
| E3 | **Theme không áp dụng / crash** | Config sai; `utils/ui_theme.json` hỏng | `load_config()` default; `build_stylesheet` | test_comprehensive |
| E4 | **Không phóng to được dialog** | Thiếu window flags | `Qt.WindowType.WindowMinMaxButtonsHint | WindowMaximizeButtonHint` | — |
| E5 | **Import aqt crash khi test** | Import top-level không phải `__init__.py` | Import nội bộ trong hàm (mock) | test_comprehensive |

## F. UTILS (`utils/` — SKILL-09)

| # | Triệu chứng | Root cause | Sửa | Verify |
|---|-------------|-----------|-----|--------|
| F1 | **safe_parse_json trả rỗng** | Input rác; hành vi cố ý | KHÔNG đổi logic (20+ test bảo vệ) | test_json_parser |
| F2 | **Deck cache trả từ cũ (thiếu từ mới)** | Không invalidate sau khi thêm note | Gọi `invalidate_deck_cache()` sau khi thay đổi deck | test_comprehensive |
| F3 | **Circular import** | Import `utils` top-level trong `ai_extractor`/`batch_processor` | Import `.logger` trực tiếp; không import `utils/__init__` | — |
| F4 | **Log không ra file** | `setup_logging` gọi nhiều lần?; thư mục readonly | Singleton (`setup_logging:28`); check quyền ghi | — |

## G. CARD TEMPLATES (`mode/` — SKILL-08)

| # | Triệu chứng | Root cause | Sửa | Verify |
|---|-------------|-----------|-----|--------|
| G1 | **Field mới không hiện trên thẻ** | Template cũ; thiếu đồng bộ | `mode/card_render.py` append extra fields; `_sync_models_after_save` | test_card_render |
| G2 | **Combo mode không chuyển** | JS body lỗi; model name không khớp | `_COMBO_MODE_JS`; `hooks/overview_mode.py` | test_combo_mode |
| G3 | **CSS hỏng layout** | Style chồng lấn | `mode/css.py` — sửa CSS của đúng ngôn ngữ | test_card_render |

## H. IMPORT HISTORY / STATE (`utils/ai_extractor.py`, `utils/factory_state`)

| # | Triệu chứng | Root cause | Sửa | Verify |
|---|-------------|-----------|-----|--------|
| H1 | **Lịch sử import mất/không lưu** | `add_to_import_history:1963` lỗi; file `utils/import_history.json` hỏng | Kiểm tra init/save; xóa file hỏng | test_factory_state |
| H2 | **State khôi phục sai ngôn ngữ** | Key thiếu ngôn ngữ | test_factory_state (2 luồng × 2 ngôn ngữ) | test_factory_state |

---

## THÊM LỖI MỚI (khi debug xong)

Khi tìm được root cause của một bug mới:
1. Thêm 1 dòng vào bảng đúng vùng (A-H) với: triệu chứng → root cause → cách sửa → verify.
2. Nếu có `file:line` mới hoặc line number cũ sai → CẬP NHẬT skill vùng tương ứng.
3. Nếu bug đáng có test bảo vệ → viết test (SKILL-10) để không tái phát.
