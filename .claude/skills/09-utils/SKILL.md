---
name: utils
description: Tiện ích dùng chung — json_parser, logger, i18n, deck_cache. Đọc khi sửa parsing JSON, logging, cache deck, hoặc cần hiểu cấu trúc utils/__init__.py.
---

# 🛠️ SKILL-09: UTILS (`utils/`)

## `utils/__init__.py` — EXPORT PUBLIC (nơi khác import từ đây)

```python
from utils import safe_parse_json, get_api_config, save_api_config, extract_text_from_file,
                  extract_vocabulary_with_ai, extract_vocabulary_long_text, chat_with_ai,
                  query_anki_context, init_import_history, add_to_import_history,
                  get_import_history, search_import_history, get_history_summary_text,
                  parse_word_list, smart_group_words, process_large_word_list,
                  organize_decks_with_ai, create_decks_from_organization, estimate_batch_cost
```
> ⚠️ Không import `utils` ở top-level trong `ai_extractor`/`batch_processor` (chúng import `.logger` trực tiếp) → tránh circular import.

## `utils/json_parser.py` (78 dòng) — safe_parse_json:13

```python
safe_parse_json(text: str) -> list
```
- Dùng `json.JSONDecoder.raw_decode()` (C parser, ~25x nhanh hơn stack loop).
- Nhận: JSON array, JSON object đơn, nhiều object rời, có `_comment` field đi kèm (AI output).
- KHÔNG crash trên input rác — trả list rỗng/object parse được.

## `utils/logger.py` (115 dòng)

```python
from utils.logger import get_logger
logger = get_logger()
logger.debug/info/warning/error("...", args)
setup_logging(level="INFO", log_to_file=True, log_to_console=True)  # dòng 28, singleton
```
- File log: `anki_tool.log` (thư mục addon), rotation 5MB × 3 file cũ.
- **Thay thế print()** — mọi module dùng pattern này.

## `utils/deck_cache.py` (166 dòng) — Deck Vocab Cache

```python
get_existing_vocab_from_deck(model_name, deck_id, front_field="Front") -> list[str]  # :37
invalidate_deck_cache(model_name=None, deck_id=None)                                  # :93
make_existing_hash(existing_words) -> str                                             # :107
```
- Chiến lược: lần đầu full scan → incremental (notes mod >= cache time) 5 phút → full rescan 30 phút.
- Cache dir: `utils/ai_cache/`, key md5(`deck|{model}|{deck_id}`).
- **Bất kỳ chỗ nào thêm/sửa note trong deck đều nên `invalidate_deck_cache()` sau đó** để lần sau quét đúng.

## `utils/i18n.py` (376 dòng) — xem chi tiết SKILL-06

```python
t(key, lang=None, **kwargs); set_language(lang); get_language(); SUPPORTED_LANGUAGES
```

## TRAPS

1. `safe_parse_json` là **bất biến về hành vi** — có 20+ test; đừng đổi logic trừ khi test vẫn xanh.
2. Logger là singleton — `setup_logging` chỉ gọi 1 lần; các module gọi `get_logger()`.
3. Deck cache dùng file — nếu đổi format cache phải xóa cache cũ hoặc đổi key.
4. Không đặt Anki import (`aqt`) ở top-level trong utils — chúng được test offline với mock.

## VERIFY

```
python -m pytest tests/test_json_parser.py tests/test_comprehensive.py tests/test_factory_state.py -v
```
