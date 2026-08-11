"""
🗂️ Deck Manager — Quản lý Parent/Sub Decks trực tiếp trong Anki collection.

Tạo, đổi tên, xóa, di chuyển deck ngay trong add-on. Vì deck được thao tác
trực tiếp trên `mw.col.decks`, UI ngoài Anki (Deck list, Browser) sẽ tự cập nhật
ngay cả khi deck chưa có thẻ nào.

API:
    get_deck_tree() -> list[dict]          # cây deck parent/sub + card count
    create_deck(name) -> int               # tạo deck (hỗ trợ Parent::Sub)
    rename_deck(old_name, new_name) -> bool
    delete_deck(name) -> bool
    get_deck_card_count(name) -> int
    refresh_anki() -> None                 # gọi mw.reset() để UI ngoài cập nhật
"""

from .logger import get_logger

logger = get_logger()


# ═══════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════

def get_deck_tree() -> list:
    """Lấy cây deck parent/sub thật từ Anki collection.

    Dùng `all_names()` để lấy toàn bộ tên deck (kể cả sub deck dạng
    "Parent::Sub") rồi xây dựng cây phân cấp chính xác — không bỏ sót
    deck nào, kể cả deck không nằm dưới "Default".

    Returns:
        list[dict]: mỗi phần tử {name, id, card_count, children: [...]}
    """
    try:
        from aqt import mw
        if mw is None or mw.col is None:
            return []
        decks = mw.col.decks
        names = decks.all_names()
        return _build_tree_from_names(names, decks)
    except Exception as e:
        logger.warning("Lỗi lấy cây deck: %s", e)
        return []


def create_deck(name: str) -> int:
    """Tạo deck mới trong Anki collection.

    Hỗ trợ tên phân cấp "Parent::Sub" — Anki tự tạo parent nếu chưa có.

    Args:
        name: Tên deck (có thể chứa "::" để tạo sub deck).

    Returns:
        deck_id vừa tạo, hoặc None nếu lỗi.
    """
    try:
        from aqt import mw
        if mw is None or mw.col is None:
            return None
        name = name.strip()
        if not name:
            return None
        deck_id = mw.col.decks.id(name)
        mw.col.decks.save(mw.col.decks.get(deck_id))
        logger.info("Đã tạo deck: %s (id=%s)", name, deck_id)
        return deck_id
    except Exception as e:
        logger.warning("Lỗi tạo deck %s: %s", name, e)
        return None


def rename_deck(old_name: str, new_name: str) -> bool:
    """Đổi tên deck (và toàn bộ sub deck con nếu có).

    Args:
        old_name: Tên deck hiện tại.
        new_name: Tên deck mới.

    Returns:
        True nếu thành công.
    """
    try:
        from aqt import mw
        if mw is None or mw.col is None:
            return False
        old_name = old_name.strip()
        new_name = new_name.strip()
        if not old_name or not new_name or old_name == new_name:
            return False
        mw.col.decks.rename(mw.col.decks.get(mw.col.decks.id(old_name)), new_name)
        logger.info("Đã đổi tên deck: %s → %s", old_name, new_name)
        return True
    except Exception as e:
        logger.warning("Lỗi đổi tên deck %s → %s: %s", old_name, new_name, e)
        return False


def delete_deck(name: str) -> bool:
    """Xóa deck (và toàn bộ sub deck con + thẻ bên trong).

    Args:
        name: Tên deck cần xóa.

    Returns:
        True nếu thành công.
    """
    try:
        from aqt import mw
        if mw is None or mw.col is None:
            return False
        name = name.strip()
        if not name:
            return False
        deck_id = mw.col.decks.id(name)
        mw.col.decks.rem(deck_id, cardsToo=True)
        logger.info("Đã xóa deck: %s", name)
        return True
    except Exception as e:
        logger.warning("Lỗi xóa deck %s: %s", name, e)
        return False


def get_deck_card_count(name: str) -> int:
    """Đếm số thẻ trong deck (bao gồm sub deck con).

    Args:
        name: Tên deck.

    Returns:
        Số thẻ, hoặc 0 nếu lỗi.
    """
    try:
        from aqt import mw
        if mw is None or mw.col is None:
            return 0
        deck_id = mw.col.decks.id(name)
        return mw.col.decks.card_count(deck_id, include_subdecks=True)
    except Exception as e:
        logger.warning("Lỗi đếm thẻ deck %s: %s", name, e)
        return 0


def refresh_anki() -> None:
    """Làm mới UI Anki để deck mới hiển thị tức thì.

    Gọi mw.reset() để Anki cập nhật Deck list / Browser ngay lập tức.
    """
    try:
        from aqt import mw
        if mw is not None:
            mw.reset()
    except Exception as e:
        logger.warning("Lỗi refresh Anki: %s", e)


# ═══════════════════════════════════════════════════════════
#  INTERNAL
# ═══════════════════════════════════════════════════════════

def _build_tree_from_names(names, decks) -> list:
    """Xây dựng cây deck từ danh sách tên deck (all_names()).

    Tên deck dạng "Parent::Sub" được tách theo "::" để tạo cây phân cấp.
    Mỗi node chứa tên đầy đủ (full name), id, card_count và children.

    Args:
        names: Danh sách tên deck từ mw.col.decks.all_names().
        decks: Đối tượng mw.col.decks.

    Returns:
        list[dict] cây deck.
    """
    # Sắp xếp để parent xuất hiện trước sub deck
    sorted_names = sorted(names, key=lambda n: (n.count("::"), n))
    root = {}  # dict lồng nhau: {segment: {node, children}}

    for full_name in sorted_names:
        parts = full_name.split("::")
        # Duyệt/xây dựng đường dẫn trong cây dict
        level = root
        for i, part in enumerate(parts):
            if part not in level:
                level[part] = {"node": None, "children": {}}
            if i == len(parts) - 1:
                # Node lá = deck thật
                try:
                    deck_id = decks.id(full_name)
                    card_count = decks.card_count(deck_id, include_subdecks=True)
                except Exception:
                    deck_id = None
                    card_count = 0
                level[part]["node"] = {
                    "name": full_name,
                    "id": deck_id,
                    "card_count": card_count,
                    "children": [],
                }
            level = level[part]["children"]

    return _dict_tree_to_list(root)


def _dict_tree_to_list(level) -> list:
    """Chuyển cây dict lồng nhau thành list[dict] theo thứ tự."""
    result = []
    for key in sorted(level.keys()):
        entry = level[key]
        node = entry["node"]
        if node is None:
            # Node trung gian (parent có sub deck) — tạo node ảo
            node = {
                "name": key,
                "id": None,
                "card_count": 0,
                "children": [],
            }
        node["children"] = _dict_tree_to_list(entry["children"])
        result.append(node)
    return result
