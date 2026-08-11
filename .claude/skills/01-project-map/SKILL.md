---
name: project-map
description: Bản đồ toàn bộ dự án AnkiTool — cấu trúc, dependency, data flow, critical paths. Đọc khi bắt đầu bất kỳ task nào chưa rõ phạm vi.
---

# 🗺️ SKILL-01: PROJECT MAP

## KHI NÀO DÙNG
- Mới vào dự án / task lớn chưa biết đụng file nào.
- Cần tìm nhanh nơi chứa 1 chức năng.

## CẤU TRÚC FILE (đầy đủ)

```
__init__.py (1,902)      ← AnkiSmartFactory QDialog + entry start_smart_factory():1892
audio/engine.py (122)    ← VOICE_OPTIONS:12, router get_audio_multilang:97, speed_to_edge_rate:117
audio/tts.py (174)       ← Edge:64, gTTS:106, VoiceVox:137
Language/__init__.py     ← LANG_CONFIG:8, LANG_GRAMMAR_CONFIG:14, LANG_SELECTOR_INFO:21
Language/japanese.py (100) ← LANG_CONFIG:3, GRAMMAR_CONFIG:54
Language/chinese.py      ← tương tự
Language/korean.py       ← tương tự (V17.0 — Hàn)
mode/__init__.py         ← registry exports
mode/css.py (173)        ← css_japanese:101, css_chinese:136, css_korean:*, *_grammar:160-164
mode/templates.py        ← tmpl_*_q/a (10-516) + COMBO (tmpl_{lang}_combo_q/a), LANG_TEMPLATES (1 cặp combo/ngôn ngữ), LANG_GRAMMAR_TEMPLATES
mode/shared.py           ← _WB_JS_BODY:37, _HW_JS_BODY:79, WB_POOLS:157, _SPEED_CTRL_JS:197, _LG_JS_BODY:294, _COMBO_MODE_JS (cuối file)
utils/ai_extractor.py (2,116) ← AI core (xem SKILL-02)
utils/batch_processor.py (969) ← batch (xem SKILL-03)
utils/deck_cache.py (166) ← get_existing_vocab_from_deck:37, invalidate:93
utils/json_parser.py (78) ← safe_parse_json:13
utils/logger.py (115)    ← setup_logging:28, get_logger
utils/i18n.py (376)      ← t():301, set_language:332, SUPPORTED_LANGUAGES:24
utils/ai_config.json     ← 🚨 API key mã hóa — KHÔNG commit
workers/__init__.py      ← re-export 7 threads
workers/import_worker.py ← ImportWorker:23
workers/ai_workers.py    ← PreviewThread:20, AiExtractThread:52, AiChatThread
workers/deck_scan_worker.py ← DeckScanWorker:14
workers/batch_workers.py ← BatchProcessThread:18, DeckOrganizerThread:88
ui/__init__.py           ← re-export dialogs
ui/ai_dialogs.py         ← AiChatDialog:15
ui/ai_settings.py        ← show_ai_settings_dialog:19, _test_ai_connection:204
ui/ai_preview.py         ← show_ai_preview_dialog:19
ui/batch_dialog.py       ← BatchWordListDialog:15
ui/verify_dialog.py      ← show_diff_meaning_dialog:13
ui/theme.py (463)        ← apply_theme, ThemeDialog, snap_maximize, load_config/save_config
hooks/reviewer.py        ← register_hooks:45 (inject combo mode + LG + speed)
hooks/overview_mode.py   ← register_overview_hooks, patch Overview._table (wrap Onigiri), webview message handler
tests/                   ← 56+ tests (xem SKILL-10)
```

## DEPENDENCY GRAPH (imports chính)

```
__init__.py → Language, mode, audio.engine, utils(safe_parse_json,logger,ai_extractor)
            → workers (7 thread), ui (dialogs), ui.theme, hooks.reviewer
ai_extractor → utils.logger, utils.json_parser(ko trực tiếp—dùng batch), deck_cache(qua utils)
batch_processor → ai_extractor (get_api_config, prompts, _parse_ai_json_with_comment, _apply_reasoning_effort)
workers/* → aqt.qt, utils.ai_extractor / batch_processor / deck_cache
hooks/reviewer → audio.engine (detect_lang_from_model), mode (_SPEED_CTRL_JS, _LG_JS_BODY)
ui/* → aqt.qt, utils (batch_processor, ai_extractor, i18n)
```

**Lưu ý vòng lặp**: `utils/__init__.py` import từ `ai_extractor`; `ai_extractor` KHÔNG import lại `utils/__init__` (chỉ import `.logger`). Giữ nguyên để tránh circular import.

## DATA FLOW

```
[A] Import JSON thủ công:
    json_input → _analyze_content:887 → safe_parse_json
    → _verify_batch_impl:911 (query Anki, phân loại add/update/dup/dup_diff)
    → _process_import:1118 → ImportWorker (thread) → get_audio_multilang → add_to_import_history

[B] AI Extract:
    _ai_extract:1421 → DeckScanWorker (lấy existing words, cache 30p)
    → _start_ai_extract:1498 → AiExtractThread → extract_vocabulary_long_text
    → _show_ai_preview:1836 → ui/ai_preview → _finalize_ai_vocab:1850

[C] Batch:
    _ai_batch_process:1561 → ui/batch_dialog (BatchWordListDialog)
    → BatchProcessThread → process_large_word_list → AI per batch
    → DeckOrganizerThread → organize_decks_with_ai → create_decks_from_organization

[D] Chat:
    _ai_chat:1616 → AiChatThread → chat_with_ai (query_anki_context)
    → _show_ai_chat_dialog:1794 → AiChatDialog
```

## CRITICAL PATHS (cấm phá vỡ)

| Path | Lý do |
|------|-------|
| `get_audio_multilang` → `_install_edge_tts` | Audio = tính năng chính |
| `safe_parse_json` | Mọi input JSON đi qua |
| `get_api_config` encryption round-trip | API key mã hóa; break = mất key |
| `get_or_create_model` (`__init__.py:1251`) | Sai = hỏng Note Type/template |
| `register_hooks` (`hooks/reviewer.py:45`) | Speed control + Letter Gap khi review |
| `_PROMPT_VERSION` bump | Quên bump = cache cũ sai |

## TOKEN BUDGET (đọc tối thiểu)

| Việc | Đọc skill + source |
|------|--------------------|
| Sửa audio | SKILL-04 + `audio/engine.py` (~1k token) |
| Sửa prompt AI | SKILL-02 + `ai_extractor.py` vùng prompt (~1.5k) |
| Sửa template thẻ | SKILL-08 + `mode/templates.py` 1 hàm (~0.8k) |
| Sửa UI dialog | SKILL-06 + file ui/ tương ứng |
| Thêm ngôn ngữ mới | SKILL-07 + SKILL-08 + SKILL-04 (3 skill, ~3.5k) |
| Sửa worker | SKILL-05 + 1 file workers/ |
