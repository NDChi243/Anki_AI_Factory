"""
📦 Deck Vocab Cache — Incremental Anki deck scanning with intelligent caching.

Tách từ ai_extractor.py để cải thiện kiến trúc (V16.0).

Strategy:
- Lần đầu: full scan toàn bộ notes
- Các lần sau: chỉ query notes có mod >= cache timestamp
- Cache 5 phút incremental + 30 phút full rescan
"""

import json
import os
import hashlib
import time
from typing import List

from .logger import get_logger

logger = get_logger()

# Config
_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_cache")
_DECK_CACHE_TTL = 30 * 60       # 30 phút full rescan
_DECK_INCREMENTAL_TTL = 5 * 60  # 5 phút incremental merge


def _ensure_cache_dir():
    if not os.path.exists(_CACHE_DIR):
        os.makedirs(_CACHE_DIR)


# ═══════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════

def get_existing_vocab_from_deck(model_name: str, deck_id: int, front_field: str = "Front") -> List[str]:
    """Lấy danh sách mặt chữ (lowercase) hiện có trong model + deck.

    Chiến lược incremental:
    - Lần đầu: full scan → cache với timestamp
    - Các lần sau: chỉ query notes có mod >= cache timestamp → merge
    - Sau 30 phút: full rescan để đồng bộ hoàn toàn
    """
    _ensure_cache_dir()
    cache_key = hashlib.md5(f"deck|{model_name}|{deck_id}".encode("utf-8")).hexdigest()
    cache_file = os.path.join(_CACHE_DIR, f"deck_{cache_key}.json")

    cached_words = None
    cached_at = 0
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            age = time.time() - data.get("_cached_at", 0)
            if age < _DECK_CACHE_TTL:
                cached_words = data.get("words", [])
                cached_at = data.get("_cached_at", 0)
                if age < _DECK_INCREMENTAL_TTL:
                    return cached_words
        except Exception:
            pass

    if cached_words is not None and cached_at > 0:
        new_words = _query_anki_deck_incremental(model_name, front_field, cached_at)
        if new_words:
            existing_set = set(w.lower() for w in cached_words)
            added = 0
            for w in new_words:
                wl = w.lower()
                if wl not in existing_set:
                    cached_words.append(w)
                    existing_set.add(wl)
                    added += 1
            if added > 0:
                logger.info("Incremental deck scan: +%d new words (total: %d)", added, len(cached_words))
        words = cached_words
    else:
        words = _query_anki_deck_full(model_name, front_field)

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({
                "words": words, "_cached_at": time.time(),
                "_model": model_name, "_deck_id": deck_id, "_count": len(words),
            }, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return words


def invalidate_deck_cache(model_name: str = None, deck_id: int = None):
    """Xóa cache deck vocab, buộc full rescan lần sau."""
    _ensure_cache_dir()
    if model_name and deck_id is not None:
        cache_key = hashlib.md5(f"deck|{model_name}|{deck_id}".encode("utf-8")).hexdigest()
        cache_file = os.path.join(_CACHE_DIR, f"deck_{cache_key}.json")
        if os.path.exists(cache_file):
            os.remove(cache_file)
    else:
        for fname in os.listdir(_CACHE_DIR):
            if fname.startswith("deck_") and fname.endswith(".json"):
                os.remove(os.path.join(_CACHE_DIR, fname))


def make_existing_hash(existing_words: List[str]) -> str:
    """Tạo hash ngắn từ danh sách từ hiện có để dùng làm cache key."""
    if not existing_words:
        return "0"
    return hashlib.md5(",".join(sorted(existing_words[:5000])).encode("utf-8")).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════
#  INTERNAL: Anki queries
# ═══════════════════════════════════════════════════════════

def _query_anki_deck_full(model_name: str, front_field: str) -> List[str]:
    """Full scan toàn bộ notes của model."""
    try:
        from aqt import mw
        note_ids = mw.col.find_notes(f'"note:{model_name}"')
        if not note_ids:
            return []

        words = set()
        batch_size = 200
        for i in range(0, len(note_ids), batch_size):
            for nid in note_ids[i:i + batch_size]:
                try:
                    note = mw.col.get_note(nid)
                    front = str(note.get(front_field, "")).strip().lower()
                    if front:
                        words.add(front)
                except Exception:
                    continue
        logger.info("Full deck scan: %d notes → %d unique words", len(note_ids), len(words))
        return sorted(words)
    except Exception as e:
        logger.warning("Lỗi full scan deck vocab: %s", e)
        return []


def _query_anki_deck_incremental(model_name: str, front_field: str, since_timestamp: float) -> List[str]:
    """Chỉ query notes được sửa đổi từ since_timestamp."""
    try:
        from aqt import mw
        since_ms = int(since_timestamp * 1000)
        note_ids = mw.col.find_notes(f'"note:{model_name}" "mod:{since_ms}:"')
        if not note_ids:
            return []

        words = []
        for nid in note_ids:
            try:
                note = mw.col.get_note(nid)
                front = str(note.get(front_field, "")).strip().lower()
                if front:
                    words.append(front)
            except Exception:
                continue
        return words
    except Exception as e:
        logger.warning("Lỗi incremental deck scan: %s", e)
        return []
