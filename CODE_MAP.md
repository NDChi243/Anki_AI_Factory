# 🗺️ CODE_MAP — Bản đồ code cho Vibe Coding

> **Mục đích**: File này giúp AI (và dev) hiểu nhanh cấu trúc codebase mà không cần đọc toàn bộ 3000+ dòng code. Dùng làm context prefix khi vibe coding.

---

## 📁 CẤU TRÚC THƯ MỤC

```
AnkiTool_Integrated/
├── __init__.py              ← 🔴 MONOLITH (2515 dòng) — Entry point + UI + Workers + Hooks
├── audio/
│   ├── __init__.py           ← Re-export get_audio_multilang
│   ├── engine.py             ← Voice selection, speed, TTS routing (109 dòng)
│   └── tts.py                ← Edge TTS, gTTS, VoiceVox providers (169 dòng)
├── Language/
│   ├── __init__.py           ← LANG_CONFIG registry + LANG_SELECTOR_INFO
│   ├── japanese.py           ← 🇯🇵 Japanese config (fields, json_map, templates) (49 dòng)
│   └── chinese.py            ← 🇨🇳 Chinese config (fields, json_map, templates) (59 dòng)
├── mode/
│   ├── __init__.py           ← Re-export templates, CSS, shared helpers
│   ├── css.py                ← CSS cho thẻ (Japanese + Chinese, ~177 dòng)
│   ├── shared.py             ← JS engines (word-building, handwriting, speed, letter-gap) (326 dòng)
│   └── templates.py          ← HTML templates cho 5 loại thẻ × 2 ngôn ngữ (399 dòng)
└── utils/
    ├── __init__.py           ← Re-export utilities
    ├── ai_config.json        ← 🚨 CHỨA API KEY THẬT — cần .gitignore
    ├── ai_extractor.py       ← 🤖 AI integration (1374 dòng) — Core AI logic
    ├── json_parser.py        ← Safe JSON parser với stack-based approach (65 dòng)
    ├── import_history.json   ← Lịch sử từ vựng đã import (cache)
    └── ai_cache/             ← Cache kết quả AI (7 ngày TTL)
```

---

## 🔗 DEPENDENCY GRAPH

```
__init__.py (Main Dialog)
├──→ Language/        (LANG_CONFIG, LANG_SELECTOR_INFO)
├──→ mode/            (LANG_TEMPLATES, LANG_CSS, shared JS)
├──→ audio/           (get_audio_multilang, voice/speed helpers)
├──→ utils/           (safe_parse_json, AI extractor, history)
└──→ aqt (Anki Qt)    (mw, gui_hooks, QThread, etc.)

audio/engine.py
└──→ audio/tts.py     (Edge TTS, gTTS providers)

utils/ai_extractor.py
├──→ utils/json_parser.py  (safe_parse_json fallback)
├──→ utils/ai_config.json  (API key, endpoint, model)
└──→ utils/ai_cache/       (Cache kết quả AI)

mode/templates.py → mode/shared.py (JS engines, character pools)
mode/css.py → mode/shared.py (_HW_CSS, _SHARED_UI_CSS)
```

---

## 📋 DANH SÁCH CLASSES & FUNCTIONS QUAN TRỌNG

### `__init__.py` (Entry Point)
| Symbol | Dòng | Mô tả | Phụ thuộc |
|--------|------|-------|-----------|
| `ImportWorker(QThread)` | 51 | Thread import hàng loạt (add/update + audio) | `audio.get_audio_multilang` |
| `PreviewThread(QThread)` | 179 | Thread preview giọng đọc | `audio.tts` |
| `AnkiSmartFactory(QDialog)` | 212 | **MAIN DIALOG** — toàn bộ UI + logic | Tất cả module |
| `_on_reviewer_question()` | 2462 | Hook khi hiện mặt trước thẻ | `mode._LG_JS_BODY` |
| `_on_reviewer_answer()` | 2471 | Hook khi hiện mặt sau thẻ (inject speed control) | `mode._SPEED_CTRL_JS` |
| `AiExtractThread(QThread)` | 2203 | Thread gọi AI trích xuất | `utils.ai_extractor` |
| `AiChatThread(QThread)` | 2243 | Thread AI chat | `utils.ai_extractor.chat_with_ai` |
| `AiChatDialog(QDialog)` | 2285 | Dialog hiển thị kết quả AI chat | — |

### `utils/ai_extractor.py` (AI Core)
| Symbol | Dòng | Mô tả |
|--------|------|-------|
| `get_api_config()` | 50 | Đọc config API (key, base, model, temp) |
| `save_api_config()` | 64 | Lưu config |
| `extract_vocabulary_with_ai()` | 361 | Gọi AI trích xuất từ vựng (có cache) |
| `extract_vocabulary_long_text()` | 898 | Chia đoạn văn bản dài → gọi AI |
| `chat_with_ai()` | 743 | AI Chat với context Anki |
| `query_anki_context()` | 584 | Thu thập ngữ cảnh Anki cho AI |
| `get_existing_vocab_from_deck()` | 124 | Lấy danh sách từ hiện có (cache 30ph) |
| `init_import_history()` | 998 | Khởi tạo/quét lịch sử import |
| `add_to_import_history()` | 1131 | Ghi từ vựng mới vào lịch sử |
| `get_history_summary_text()` | 1312 | Tóm tắt lịch sử cho AI context |

### `audio/engine.py` (Audio)
| Symbol | Dòng | Mô tả |
|--------|------|-------|
| `get_audio_multilang()` | 84 | Router chính: Edge → gTTS |
| `get_voice_options()` | 43 | Danh sách giọng theo ngôn ngữ |
| `speed_to_edge_rate()` | 104 | Convert speed (0.25-4.0) → rate string |

### `mode/templates.py` (Card Templates)
| Symbol | Dòng | Loại thẻ |
|--------|------|----------|
| `tmpl_ja_q/a` | 10-38 | 1. Nhật → Việt |
| `tmpl_ja_vn_q/a` | 40-71 | 2. Việt → Nhật |
| `tmpl_ja_wb_q/a` | 73-110 | 3. Ghép chữ (Word Building) |
| `tmpl_ja_pron_q/a` | 112-139 | 4. Furigana |
| `tmpl_ja_lg_q/a` | 145-181 | 5. Ẩn chữ cái (Letter Gap) |
| *(tương tự cho zh)* | 186-381 | |

---

## 🔄 DATA FLOW

### Import Flow
```
1. User dán JSON → _analyze_content() → safe_parse_json()
2. User bấm "Kiểm Định" → _verify_batch_impl()
   - Query Anki DB tìm từ trùng
   - Phân loại: add / update / dup / dup_diff
3. Hiển thị preview list
4. User bấm "Xuất Xưởng" → _process_import()
   - ImportWorker chạy trong QThread
   - Gọi get_audio_multilang() nếu chọn tạo audio
   - Ghi vào import_history
```

### AI Extract Flow
```
1. User dán text → bấm "AI Trích Xuất"
2. _ai_extract() → quét deck lấy existing_words (cache 30ph)
3. AiExtractThread → extract_vocabulary_long_text()
   - Check cache (7 ngày TTL)
   - Gọi API với system prompt + existing words
   - Parse JSON response
   - Lọc trùng lặp
4. Hiển thị dialog preview (_show_ai_preview)
5. User chỉnh sửa → đổ vào json_input → _analyze_content()
```

### AI Chat Flow
```
1. User gửi tin nhắn → _ai_chat()
2. AiChatThread → chat_with_ai()
   - query_anki_context() — thu thập deck stats
   - _build_anki_context_text() — tạo context text
   - Gửi system prompt "GIA SƯ NGÔN NGỮ" + context
3. Parse response: tách text + JSON vocab
4. Hiển thị AiChatDialog
```

---

## ⚠️ CRITICAL PATHS (không được phá vỡ)

| Path | Lý do |
|------|-------|
| `get_audio_multilang()` → `_install_edge_tts()` | Không có audio = mất tính năng chính |
| `safe_parse_json()` | Mọi input JSON đi qua đây |
| `extract_vocabulary_with_ai()` retry logic | API không ổn định, cần retry |
| `_verify_batch_impl()` query Anki | Nếu query sai → mất dữ liệu hoặc trùng lặp |
| `get_or_create_model()` | Tạo/cập nhật Note Type, nếu sai → hỏng template |

---

## 🏷️ GLOBAL STATE (cần cẩn thận khi sửa)

| State | Vị trí | Thread-safe? |
|-------|--------|-------------|
| `_selected_voice: dict` | `audio/engine.py:37` | ❌ Không |
| `_default_speed: dict` | `audio/engine.py:40` | ❌ Không |
| `_audio_query_cache: dict` | `audio/tts.py:24` | ❌ Không |
| `LANG_CONFIG` | `Language/__init__.py` | ✅ Read-only |
| `LANG_TEMPLATES` | `mode/templates.py:385` | ✅ Read-only |
| `mw.col` | Anki global | ⚠️ Cần cẩn thận khi multi-thread |

---

## 🧩 CÁCH THÊM NGÔN NGỮ MỚI

1. Tạo `Language/korean.py` với `LANG_CONFIG`
2. Thêm vào `Language/__init__.py`
3. Tạo templates trong `mode/templates.py`
4. Thêm CSS trong `mode/css.py`
5. Thêm voice options trong `audio/engine.py`
6. Thêm system prompt trong `utils/ai_extractor.py`
7. Thêm WB_POOL trong `mode/shared.py`

---

## 💾 TOKEN USAGE (cho Vibe Coding)

Khi vibe coding, chỉ cần đọc các file này (theo thứ tự ưu tiên):

| File | Token ước tính | Khi nào cần |
|------|---------------|-------------|
| `CODE_MAP.md` (file này) | ~500 | LUÔN LUÔN |
| `Language/{lang}.py` | ~200 | Sửa config ngôn ngữ |
| `audio/engine.py` | ~300 | Sửa audio/voice |
| `mode/shared.py` | ~400 | Sửa JS game engines |
| `mode/templates.py` | ~600 | Sửa card templates |
| `utils/json_parser.py` | ~150 | Sửa JSON parsing |
| `utils/ai_extractor.py` | ~2000 | Sửa AI logic |
| `__init__.py` | ~4000 | Sửa UI/workers (TRÁNH nếu có thể) |
