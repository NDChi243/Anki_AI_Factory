"""
🛠️ Utilities Package — Các tiện ích dùng chung
"""

from .json_parser import safe_parse_json
from .ai_extractor import (
    get_api_config,
    save_api_config,
    extract_text_from_file,
    extract_vocabulary_with_ai,
    extract_vocabulary_long_text,
    chat_with_ai,
    query_anki_context,
    init_import_history,
    add_to_import_history,
    get_import_history,
    search_import_history,
    get_history_summary_text,
)
from .deck_cache import (
    get_existing_vocab_from_deck,
    invalidate_deck_cache,
)
from .batch_processor import (
    parse_word_list,
    smart_group_words,
    process_large_word_list,
    organize_decks_with_ai,
    create_decks_from_organization,
    estimate_batch_cost,
)

__all__ = [
    "safe_parse_json",
    "get_api_config",
    "save_api_config",
    "extract_text_from_file",
    "extract_vocabulary_with_ai",
    "extract_vocabulary_long_text",
    "chat_with_ai",
    "query_anki_context",
    "init_import_history",
    "add_to_import_history",
    "get_import_history",
    "search_import_history",
    "get_history_summary_text",
    "parse_word_list",
    "smart_group_words",
    "process_large_word_list",
    "organize_decks_with_ai",
    "create_decks_from_organization",
    "estimate_batch_cost",
]
