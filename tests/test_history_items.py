"""
Tests cho hàm get_import_history_items + lưu item gốc trong lịch sử AI.

Đảm bảo: sau khi add_to_import_history, ta có thể lấy lại item đầy đủ để
đưa vào xưởng và import lại (kể cả entry cũ chưa lưu item gốc).
"""

import os
import sys

import pytest

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)


def _mod():
    from utils import ai_extractor
    return ai_extractor


@pytest.fixture(autouse=True)
def _iso(tmp_path, monkeypatch):
    mod = _mod()
    monkeypatch.setattr(mod, "_HISTORY_PATH", str(tmp_path / "import_history.json"))
    monkeypatch.setattr(mod, "_HISTORY_VERSION", mod._HISTORY_VERSION)


class TestGetImportHistoryItems:
    def test_returns_stored_full_item(self):
        mod = _mod()
        items = [
            {"front": "食べる", "meaning": "ăn", "furigana": "たべる", "jlptlevel": "N5", "topic": "food"},
            {"front": "飲む", "meaning": "uống", "jlptlevel": "N4"},
        ]
        mod.add_to_import_history(items, "japanese", deck_name="Deck A", source="manual")
        out = mod.get_import_history_items(lang="japanese")
        assert len(out) == 2
        langs = {l for l, _ in out}
        assert langs == {"japanese"}
        fronts = {it["front"] for _, it in out}
        assert fronts == {"食べる", "飲む"}
        # Item gốc được giữ nguyên (furigana, topic, level)
        eat = next(it for _, it in out if it["front"] == "食べる")
        assert eat["furigana"] == "たべる"
        assert eat["topic"] == "food"
        assert eat["jlptlevel"] == "N5"

    def test_reconstruct_old_entry_without_item(self):
        mod = _mod()
        data = mod._load_history()
        data["entries"] = {
            "japanese": {
                "たべる": {
                    "front": "食べる", "front_lower": "たべる", "meaning": "ăn",
                    "level": "N5", "furigana": "たべる", "imported_at": 1, "source": "deck_scan",
                }
            }
        }
        mod._save_history(data)
        out = mod.get_import_history_items(lang="japanese")
        assert len(out) == 1
        item = out[0][1]
        assert item["front"] == "食べる"
        assert item["meaning"] == "ăn"
        assert item["jlptlevel"] == "N5"   # japanese → jlptlevel
        assert item["furigana"] == "たべる"

    def test_reconstruct_chinese_uses_hsk(self):
        mod = _mod()
        data = mod._load_history()
        data["entries"] = {
            "chinese": {
                "学校": {
                    "front": "学校", "front_lower": "学校", "meaning": "trường học",
                    "level": "HSK4", "pinyin": "xuéxiào", "imported_at": 2, "source": "deck_scan",
                }
            }
        }
        mod._save_history(data)
        out = mod.get_import_history_items(lang="chinese")
        item = out[0][1]
        assert item["hsk_level"] == "HSK4"
        assert item["pinyin"] == "xuéxiào"

    def test_lang_filter_and_sort_newest_first(self):
        mod = _mod()
        mod.add_to_import_history([{"front": "ja1", "meaning": "a"}], "japanese")
        mod.add_to_import_history([{"front": "zh1", "meaning": "b"}], "chinese")
        out_ja = mod.get_import_history_items(lang="japanese")
        assert len(out_ja) == 1 and out_ja[0][1]["front"] == "ja1"
        out_all = mod.get_import_history_items(lang=None)
        # chinese added sau → mới hơn → đứng trước
        assert out_all[0][1]["front"] == "zh1"
        assert len(out_all) == 2

    def test_skips_entries_without_front(self):
        mod = _mod()
        mod.add_to_import_history([{"meaning": "no front"}], "japanese")
        out = mod.get_import_history_items(lang="japanese")
        assert out == []

    def test_limit(self):
        mod = _mod()
        mod.add_to_import_history([{"front": f"w{i}", "meaning": "m"} for i in range(5)], "japanese")
        out = mod.get_import_history_items(lang="japanese", limit=3)
        assert len(out) == 3
