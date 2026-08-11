# 🤖 CLAUDE.md — AnkiTool Multi-Language V17.0

> Add-on Anki (Python/PyQt5) tạo thẻ từ vựng Nhật, Trung & Hàn với AI + TTS + interactive templates.

## 🎯 CÁCH DÙNG HỆ THỐNG NÀY (TIẾT KIỆM TOKEN)

Nguyên tắc **progressive disclosure**: KHÔNG đọc toàn bộ source. Chỉ đọc 1 skill liên quan + nhảy thẳng tới dòng cần sửa (line number trong skill).

```
Bước 1: Đọc file này (~1.5k token)
Bước 2: Chọn ĐÚNG 1 skill dưới đây theo việc cần làm
Bước 3: Trong skill, dùng "file:line" để đọc ĐÚNG đoạn code cần (read_file offset/limit)
Bước 4: Chạy tests liên quan (xem skill 10)
```

## 🧩 INDEX SKILLS

| # | Skill | Dùng khi | Token |
|---|-------|----------|-------|
| 01 | project-map | Mới vào dự án, cần hiểu cấu trúc/dependency | ~1.2k |
| 02 | ai-extraction | Sửa AI extract/chat/prompt/cache/cost | ~1.5k |
| 03 | batch-processing | Sửa batch/xử lý danh sách lớn/tổ chức deck | ~1.2k |
| 04 | audio-tts | Sửa giọng đọc/audio/speed | ~1.0k |
| 05 | workers | Sửa thread/signal/tương tác nền | ~1.0k |
| 06 | ui-layer | Sửa dialog/theme/i18n UI | ~1.2k |
| 07 | language-config | Thêm/sửa ngôn ngữ, field, model name | ~1.0k |
| 08 | card-templates | Sửa HTML/CSS/JS của thẻ | ~1.3k |
| 09 | utils | Sửa json_parser/logger/i18n/deck_cache | ~1.0k |
| 10 | testing | Chạy/viết test, verify sau khi sửa | ~1.0k |
| 11 | upgrade-playbook | Nâng cấp version, bảo trì, release | ~1.2k |

## 🧭 SƠ ĐỒ TỔNG QUAN (TỐI GIẢN)

```
__init__.py (2,0xx dòng)       ← AnkiSmartFactory QDialog (MAIN)
├── Language/    LANG_CONFIG, LANG_GRAMMAR_CONFIG   (japanese, chinese, korean)
├── mode/        LANG_TEMPLATES, LANG_CSS, LANG_GRAMMAR_*, JS bodies
├── audio/       engine.py (router) + tts.py (Edge/gTTS/VoiceVox)
├── utils/       ai_extractor, batch_processor, deck_cache, json_parser, logger, i18n
├── workers/     ImportWorker, PreviewThread, AiExtractThread, AiChatThread, DeckScanWorker, BatchProcessThread, DeckOrganizerThread
├── ui/          AiChatDialog, ai_settings, ai_preview, batch_dialog, verify_dialog, theme
├── hooks/       reviewer.py (register_hooks)
└── tests/       56+ tests
```

## 🔒 QUY TẮC VÀNG (BẮT BUỘC)

1. **Đọc skill trước, đọc source sau** — không mở file 2000 dòng vô tội vạ.
2. **`file:line` là chân lý** — mọi line number trong skill đã được xác minh; nếu code thay đổi, cập nhật line number trong skill.
3. **Không import Anki modules (aqt) ở top-level ngoài `__init__.py`** — dùng try/except khi gọi Anki API.
4. **Mọi UI đều qua i18n `t()`** — không hardcode string tiếng Việt trong UI.
5. **Mọi log qua `get_logger()`** — không dùng `print()`.
6. **Bare `except:` cấm** — luôn `except Exception:` + log.
7. **Thread-safe cho mọi state chia sẻ** — dùng `threading.Lock` (xem audio/engine.py làm mẫu).
8. **Không commit `utils/ai_config.json`** (API key mã hóa) — chỉ commit `.example`.
9. **Sửa prompt → Bump `_PROMPT_VERSION`** trong `utils/ai_extractor.py:371` để invalidate cache.
10. **Sau khi sửa → chạy pytest** (skill 10) trước khi báo xong.

## 🏷️ NGÔN NGỮ & THUẬT NGỮ

- `vocab` = chế độ Từ vựng; `grammar` = chế độ Ngữ pháp (Note Type riêng).
- `lang` = `"japanese"` | `"chinese"` | `"korean"`.
- Model names: `"AnkiTool Japanese/Chinese/Korean [Grammar] V17.0 (Add-on)"`.
- Entry: `start_smart_factory()` (`__init__.py:1892`), shortcut `Ctrl+Shift+I`.
- Version hiện tại: **17.0.0** (`manifest.json`).
- **Combo mode**: mỗi từ = 1 card duy nhất, 5 chế độ (qa/vn/wb/pron/lg) chuyển đổi trong card qua `_COMBO_MODE_JS`; mode lưu `mw.col.conf["ai_factory_study_mode"]`; Overview patch qua `hooks/overview_mode.py`.

---

*Hệ thống skill này thay thế CODE_MAP.md/UPGRADE_GUIDE.md cũ (đã lỗi thời). Chi tiết từng module nằm trong `.claude/skills/`.*
