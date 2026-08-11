---
name: language-config
description: Cấu hình ngôn ngữ — Language/ (japanese, chinese, korean). LANG_CONFIG + GRAMMAR_CONFIG + registry. Đọc khi thêm ngôn ngữ mới hoặc sửa field/model name.
---

# 🈺 SKILL-07: LANGUAGE CONFIG

> Mỗi ngôn ngữ 1 file: `Language/japanese.py` (100 dòng), `Language/chinese.py`, `Language/korean.py`. Registry tại `Language/__init__.py`.

## REGISTRY (`Language/__init__.py`)

```python
LANG_CONFIG          = {"japanese": _JA, "chinese": _ZH, "korean": _KO}   # dòng 8
LANG_GRAMMAR_CONFIG  = {"japanese": _JA_G, "chinese": _ZH_G, "korean": _KO_G}  # dòng 14
LANG_KEYS            = list(LANG_CONFIG.keys())
LANG_SELECTOR_INFO   = [("japanese","🇯🇵 日本語","JP"), ("chinese","🇨🇳 中文","CN"), ("korean","🇰🇷 한국어","KR")]  # dòng 21
```

## CẤU TRÚC LANG_CONFIG (japanese.py:3)

```python
LANG_CONFIG = {
    "label": "🇯🇵 Tiếng Nhật",
    "lang_code": "ja",                                    # "zh" cho Trung, "ko" cho Hàn
    "model_name": "AnkiTool Japanese V17.0 (Add-on)",     # ⚠️ format version phải khớp
    "old_model_names": [...],                              # migration từ bản cũ
    "all_fields": [...],                                   # toàn bộ field của Note Type
    "json_field_map": {...},                               # JSON key → Anki field (front, meaning, furigana/simplified, example...)
    "detect_key": "front",                                 # key nhận diện từ
    "level_field": "JLPT Level", "level_choices": ["Tất cả","N5","N4","N3","N2","N1"],  # Trung: HSK Level/HSK1-6
    "front_field": "Front",
    "audio_fields": [("Vocab Audio","Front"), ("Example Audio","Example"), ("Example2 Audio","Example2")],
    "template_names": ("1. Nhật → Việt", ..., "5. 🔤 Ẩn Chữ Cái"),
    "furi_label": "Furigana", "furi_json_key": "furigana", "level_json_key": "jlptlevel",
    # Trung thêm: "sino_label"..., "pinyin_json_key": "pinyin"
}
```

## CẤU TRÚC GRAMMAR_CONFIG (japanese.py:54)

```python
GRAMMAR_CONFIG = {
    "label": "🇯🇵 Ngữ pháp Tiếng Nhật",
    "lang_code": "ja",
    "model_name": "AnkiTool Japanese Grammar V17.0 (Add-on)",
    "old_model_names": [],
    "all_fields": ["Pattern", "Reading", "Meaning", "JLPT Level", "Topic", ...],  # Trung: Pinyin, HSK
    "json_field_map": {"pattern": "Pattern", "reading": "Reading", "meaning": "Meaning", ...},
    "detect_key": "pattern", "level_field": ..., "template_names": (...), ...
}
```

## BẢN ĐỒ NGÔN NGỮ (map key chung)

| Khái niệm | Nhật | Trung | Hàn |
|-----------|------|-------|------|
| Field mặt chữ | Front + Furigana | Front (simplified) + Pinyin | Front (Hangul) + Romanization |
| Level | JLPT Level / jlptlevel | HSK Level / hsk_level | TOPIK Level / topik_level |
| Mặt chữ báo cáo | furi_label=Furigana | pinyin_label=Pinyin | furi_label=Romanization |
| Audio fields | Vocab Audio/Example Audio/Example2 Audio | tương tự | tương tự |

## THÊM NGÔN NGỮ MỚI (7 bước — checklist)

1. Tạo `Language/korean.py` với `LANG_CONFIG` + `GRAMMAR_CONFIG` (đã có — Hàn)
2. Thêm vào registry `Language/__init__.py` (LANG_CONFIG, LANG_GRAMMAR_CONFIG, LANG_SELECTOR_INFO, LANG_KEYS)
3. Tạo templates trong `mode/templates.py` (SKILL-08)
4. Thêm CSS trong `mode/css.py` (SKILL-08)
5. Thêm voice trong `audio/engine.py` VOICE_OPTIONS + `_MODEL_LANG_MAP` (SKILL-04)
6. Thêm system prompt + JSON template trong `utils/ai_extractor.py` (_SYSTEM_PROMPTS/_JSON_TEMPLATES/_GRAMMAR_*) (SKILL-02) + bump `_PROMPT_VERSION`
7. Thêm WB_POOL trong `mode/shared.py` (SKILL-08)

## TRAPS

1. `model_name` chứa version (V17.0) — khi nâng cấp version phải đổi + thêm cái cũ vào `old_model_names` (để migration). **Đồng bộ với `audio/engine.py:_MODEL_LANG_MAP` (81).**
2. `json_field_map` phải cover đủ key AI trả ra (front/simplified/word/pattern + level jlptlevel/hsk_level/topik_level).
3. Sửa field → Note Type cũ không tự cập nhật → user phải "Tái Tạo Model" (`_force_rebuild_model:1206`) hoặc `_get_or_migrate_model:1236`.
4. i18n: thêm label mới vào `utils/i18n.py` (SKILL-06) nếu hiển thị trong UI.

## VERIFY

```
python -m pytest tests/test_grammar.py tests/test_integration.py tests/test_comprehensive.py -v
```
