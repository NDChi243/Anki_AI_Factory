"""
Unit tests cho cơ chế lưu trạng thái ô AI theo luồng (Từ vựng / Ngữ pháp × ngôn ngữ).

Test:
- Lưu/khôi phục text riêng cho từng (lang, mode)
- Lưu/khôi phục danh sách file kẹp (path) riêng
- Xóa text → lưu luồng rỗng (không lẫn luồng khác)
"""

import os
import sys
import types
import tempfile
from unittest.mock import MagicMock

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)


class FakeTextEdit:
    """Fake QPlainTextEdit — setPlainText/toPlainText hoạt động thật."""

    def __init__(self):
        self._text = ""

    def toPlainText(self):
        return self._text

    def setPlainText(self, t):
        self._text = t or ""

    def clear(self):
        self._text = ""


# ── Mock Anki (giống test_integration) ──────────────────────
class MockSignal:
    def __init__(self, *t): self._s = []
    def connect(self, s): self._s.append(s)
    def emit(self, *a, **k):
        for s in self._s: s(*a, **k)
    def disconnect(self, s=None):
        if s: self._s.remove(s)
        else: self._s.clear()


aqt_qt = types.ModuleType("aqt.qt")
aqt_qt.QThread = type("QThread", (object,), {"__init__": lambda self, p=None: None, "start": lambda self: None, "isRunning": lambda self: False, "wait": lambda self, m=0: None})
aqt_qt.pyqtSignal = MockSignal
_QDialog = type("QDialog", (object,), {"exec": lambda self: 1, "accept": lambda self: None, "reject": lambda self: None})
_QDialog.DialogCode = type("DialogCode", (), {"Accepted": 1, "Rejected": 0})
aqt_qt.QDialog = _QDialog
for _n in ("QVBoxLayout", "QHBoxLayout", "QGridLayout", "QFormLayout", "QLabel",
           "QPushButton", "QLineEdit", "QPlainTextEdit", "QCheckBox", "QComboBox",
           "QDoubleSpinBox", "QSpinBox", "QSlider", "QColorDialog", "QGroupBox",
           "QListWidget", "QListWidgetItem", "QProgressBar", "QTextBrowser", "QTextEdit", "QTableWidget",
           "QTableWidgetItem", "QScrollArea", "QWidget", "QAbstractItemView",
           "QTimer", "QAction", "QTreeWidget", "QTreeWidgetItem", "QInputDialog",
           "QMenu", "QTabWidget", "QHeaderView"):
    aqt_qt.__dict__[_n] = lambda *a, **k: MagicMock()
aqt_qt.QColor = type("QColor", (), {})
aqt_qt.QApplication = MagicMock()
aqt_qt.QMessageBox = MagicMock()
aqt_qt.QFileDialog = MagicMock()
aqt_qt.Qt = MagicMock()
aqt_qt.QKeySequence = lambda *a: MagicMock()
sys.modules["aqt.qt"] = aqt_qt

aqt_mock = types.ModuleType("aqt")
aqt_mock.mw = MagicMock()
aqt_mock.mw.col = MagicMock()
aqt_mock.mw.col.models = MagicMock()
aqt_mock.mw.col.decks = MagicMock()
aqt_mock.mw.app = MagicMock()
aqt_mock.gui_hooks = MagicMock()
aqt_mock.form = MagicMock()
sys.modules["aqt"] = aqt_mock
sys.modules["aqt.mw"] = aqt_mock.mw

aqt_utils = types.ModuleType("aqt.utils")
aqt_utils.showInfo = lambda *a, **k: None
aqt_utils.tooltip = lambda *a, **k: None
aqt_utils.qconnect = lambda *a, **k: None
sys.modules["aqt.utils"] = aqt_utils

anki_mock = types.ModuleType("anki")
anki_notes = types.ModuleType("anki.notes")
anki_notes.Note = MagicMock()
sys.modules["anki"] = anki_mock
sys.modules["anki.notes"] = anki_notes

audio_mock = types.ModuleType("audio")
audio_mock.__path__ = []
audio_mock.get_audio_multilang = lambda *a, **k: ""
sys.modules["audio"] = audio_mock

audio_tts_mock = types.ModuleType("audio.tts")
audio_tts_mock._install_edge_tts = lambda: False
audio_tts_mock._install_gtts = lambda: False
audio_tts_mock.get_audio_edge_tts = lambda *a, **k: ""
audio_tts_mock.get_audio_gtts = lambda *a, **k: ""
sys.modules["audio.tts"] = audio_tts_mock
audio_mock.tts = audio_tts_mock

audio_engine_mock = types.ModuleType("audio.engine")
_engine_path = os.path.join(_addon_root, "audio", "engine.py")
with open(_engine_path, "r", encoding="utf-8") as _f:
    exec(compile(_f.read(), _engine_path, "exec"), audio_engine_mock.__dict__)
sys.modules["audio.engine"] = audio_engine_mock
audio_mock.engine = audio_engine_mock

# Khởi tạo module add-on (chạy entry-point cần các mock trên)
import __init__ as addon


def _make_factory(state_path):
    """Tạo AnkiSmartFactory KHÔNG chạy __init__ (tránh UI) — chỉ test state."""
    obj = object.__new__(addon.AnkiSmartFactory)
    obj._current_lang = "japanese"
    obj._is_grammar = False
    obj._factory_state = {}
    obj._ai_attached_files = []
    obj._ai_attached_paths = []
    obj.ai_text_input = FakeTextEdit()
    obj.lbl_ai_files = MagicMock()
    addon._STATE_PATH = state_path
    obj._load_factory_state = addon.AnkiSmartFactory._load_factory_state.__get__(obj, addon.AnkiSmartFactory)
    obj._save_factory_state = addon.AnkiSmartFactory._save_factory_state.__get__(obj, addon.AnkiSmartFactory)
    obj._save_current_flow = addon.AnkiSmartFactory._save_current_flow.__get__(obj, addon.AnkiSmartFactory)
    obj._restore_current_flow = addon.AnkiSmartFactory._restore_current_flow.__get__(obj, addon.AnkiSmartFactory)
    obj._update_ai_files_label = addon.AnkiSmartFactory._update_ai_files_label.__get__(obj, addon.AnkiSmartFactory)
    obj._factory_state = obj._load_factory_state()
    return obj


class TestFactoryState:
    def test_roundtrip_text_per_flow(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "state.json")
            f = _make_factory(p)

            f.ai_text_input.setPlainText("VOCAB TEXT JA")
            f._save_current_flow()

            f._is_grammar = True
            f.ai_text_input.setPlainText("GRAMMAR TEXT JA")
            f._save_current_flow()

            f._is_grammar = False
            f.ai_text_input.clear()
            f._restore_current_flow()
            assert f.ai_text_input.toPlainText() == "VOCAB TEXT JA"

            f._is_grammar = True
            f.ai_text_input.clear()
            f._restore_current_flow()
            assert f.ai_text_input.toPlainText() == "GRAMMAR TEXT JA"

    def test_lang_separated(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "state.json")
            f = _make_factory(p)

            f.ai_text_input.setPlainText("JA")
            f._save_current_flow()

            f._current_lang = "chinese"
            f.ai_text_input.setPlainText("ZH")
            f._save_current_flow()

            f._current_lang = "japanese"
            f.ai_text_input.clear()
            f._restore_current_flow()
            assert f.ai_text_input.toPlainText() == "JA"

    def test_clear_text_saves_empty(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "state.json")
            f = _make_factory(p)

            f.ai_text_input.setPlainText("ABC")
            f._save_current_flow()

            # Giả lập "Xóa Text"
            f.ai_text_input.clear()
            f._ai_attached_paths = []
            f._save_current_flow()

            f.ai_text_input.setPlainText("ABC")
            f._restore_current_flow()
            assert f.ai_text_input.toPlainText() == ""   # đã xóa

    def test_files_persisted_per_flow(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "state.json")
            ref = os.path.join(d, "ref.txt")
            with open(ref, "w", encoding="utf-8") as fh:
                fh.write("tài liệu tham khảo")

            f = _make_factory(p)
            f._ai_attached_paths = [ref]
            f.ai_text_input.setPlainText("text+file")
            f._save_current_flow()

            f._is_grammar = True
            f._ai_attached_paths = []
            f.ai_text_input.setPlainText("grammar")
            f._save_current_flow()

            f._is_grammar = False
            f._ai_attached_paths = []
            f._ai_attached_files = []
            f.ai_text_input.clear()
            f._restore_current_flow()
            assert f._ai_attached_paths == [ref]
            assert f.ai_text_input.toPlainText() == "text+file"


class TestComboMigration:
    """Migration combo: chỉ xóa card thừa (ord>=keep_count), giữ card mode chính."""

    def test_collect_template_fields_captures_all(self):
        """Phải thu thập đủ field template tham chiếu (tránh CardTypeError khi save)."""
        import __init__ as addon
        from mode import LANG_TEMPLATES, LANG_GRAMMAR_TEMPLATES
        fields = addon.AnkiSmartFactory._collect_template_fields(LANG_TEMPLATES["japanese"])
        for f in ("Front", "Meaning", "Furigana", "JLPT Level", "Topic",
                  "Sino-Vietnamese", "Vocab Audio", "Example", "Example Audio",
                  "Example in Vietnamese", "Example2", "Example2 in Vietnamese"):
            assert f in fields, f"Thiếu field {f}"
        zh = addon.AnkiSmartFactory._collect_template_fields(LANG_TEMPLATES["chinese"])
        for f in ("Front", "Pinyin", "HSK Level", "Traditional"):
            assert f in zh, f"Thiếu field {f}"
        ko = addon.AnkiSmartFactory._collect_template_fields(LANG_TEMPLATES["korean"])
        for f in ("Front", "Romanization", "TOPIK Level", "Sino-Vietnamese",
                  "Vocab Audio", "Example", "Example Romanization",
                  "Example in Vietnamese", "Example2", "Example2 in Vietnamese"):
            assert f in ko, f"Thiếu field {f}"
        g = addon.AnkiSmartFactory._collect_template_fields(LANG_GRAMMAR_TEMPLATES["japanese"])
        assert "Pattern" in g
        gko = addon.AnkiSmartFactory._collect_template_fields(LANG_GRAMMAR_TEMPLATES["korean"])
        assert "Pattern" in gko
        assert "Romanization" in gko

    def test_drop_extra_combo_cards_keeps_first(self):
        import __init__ as addon
        from unittest.mock import patch
        # Mock addon.mw.col cho migration
        mw_mock = MagicMock()
        mw_mock.col.find_notes = MagicMock(return_value=[1, 2])
        mw_mock.col.db.list = MagicMock(
            side_effect=lambda sql, nid, k: [100 + nid * 10, 200 + nid * 10]
        )
        mw_mock.col.remCards = MagicMock()
        with patch.object(addon, "mw", mw_mock):
            addon.AnkiSmartFactory._drop_extra_combo_cards(None, mid=42, keep_count=1)
        # find_notes gọi với query đúng mid
        mw_mock.col.find_notes.assert_called_once()
        # remCards được gọi với các card thừa (ord>=1)
        mw_mock.col.remCards.assert_called()
        removed = mw_mock.col.remCards.call_args[0][0]
        assert len(removed) >= 2

    def test_drop_extra_no_notes(self):
        import __init__ as addon
        from unittest.mock import patch
        mw_mock = MagicMock()
        mw_mock.col.find_notes = MagicMock(return_value=[])
        mw_mock.col.remCards = MagicMock()
        with patch.object(addon, "mw", mw_mock):
            addon.AnkiSmartFactory._drop_extra_combo_cards(None, mid=42, keep_count=1)
        mw_mock.col.remCards.assert_not_called()
