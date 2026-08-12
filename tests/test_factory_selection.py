"""
Unit tests cho tính năng chọn lọc thẻ chờ xuất xưởng (factory) trong AnkiSmartFactory.

Test:
- _rebuild_preview: lọc theo loại thẻ (action) + tìm kiếm theo từ/nghĩa
- _get_export_indices: ưu tiên thẻ được check; không check → dùng khoảng Từ-đến
- _remove_factory_indices: xóa thẻ khỏi prepared_data + raw_data
- Persist thẻ trong xưởng qua _save/_restore_current_flow (không mất khi đóng cửa sổ)
- _cancel_order: xóa toàn bộ / xóa theo lựa chọn
"""

import os
import sys
import types
import tempfile
from unittest.mock import MagicMock

import pytest

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)


# ── Mock Anki (giống test_factory_state) ──────────────────────
class MockSignal:
    def __init__(self, *t):
        self._s = []
    def connect(self, s):
        self._s.append(s)
    def emit(self, *a, **k):
        for s in self._s:
            s(*a, **k)
    def disconnect(self, s=None):
        if s:
            self._s.remove(s)
        else:
            self._s.clear()


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
           "QMenu", "QMessageBox", "QPoint", "QTabWidget", "QHeaderView"):
    aqt_qt.__dict__[_n] = lambda *a, **k: MagicMock()
aqt_qt.QColor = type("QColor", (), {})
aqt_qt.QApplication = MagicMock()
aqt_qt.QFileDialog = MagicMock()
aqt_qt.QKeySequence = lambda *a: MagicMock()
aqt_qt.Qt = MagicMock()
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

import __init__ as addon


@pytest.fixture(autouse=True)
def _isolate_state(tmp_path, monkeypatch):
    """Mỗi test dùng file state riêng trong temp — không đụng state thật."""
    monkeypatch.setattr(addon, "_STATE_PATH", str(tmp_path / "factory_state.json"))
    monkeypatch.setattr(addon, "QMessageBox", MagicMock())
    monkeypatch.setattr(addon, "tooltip", lambda *a, **k: None)
    yield


# ── Fake Qt enums ─────────────────────────────────────────────
class _CheckState:
    Unchecked = 0
    Checked = 2


class _ItemDataRole:
    UserRole = 256


class _ItemFlag:
    ItemIsUserCheckable = 16


class _QtFake:
    CheckState = _CheckState
    ItemDataRole = _ItemDataRole
    ItemFlag = _ItemFlag


# ── Fake widgets ──────────────────────────────────────────────
class FakeListItem:
    def __init__(self, text=""):
        self.text = text
        self._state = _CheckState.Unchecked
        self._flags = 0
        self._data = {}

    def flags(self):
        return self._flags

    def setFlags(self, f):
        self._flags = f

    def checkState(self):
        return self._state

    def setCheckState(self, s):
        self._state = s

    def setData(self, role, value):
        self._data[role] = value

    def data(self, role):
        return self._data.get(role)


class FakeListWidget:
    def __init__(self):
        self.items = []

    def count(self):
        return len(self.items)

    def item(self, row):
        return self.items[row]

    def addItem(self, item):
        self.items.append(item)

    def clear(self):
        self.items = []

    def blockSignals(self, b):
        return b

    def setMinimumHeight(self, h):
        pass


class FakeSpin:
    def __init__(self):
        self._value = 1
        self._max = 9999
        self._min = 1

    def setRange(self, lo, hi):
        self._min, self._max = lo, hi
        if self._value < lo:
            self._value = lo
        if self._value > hi:
            self._value = hi

    def setValue(self, v):
        self._value = max(self._min, min(self._max, v))

    def value(self):
        return self._value


class FakeLineEdit:
    def __init__(self):
        self._text = ""

    def text(self):
        return self._text

    def setText(self, t):
        self._text = t or ""

    def setPlaceholderText(self, t):
        pass


class FakeComboBox:
    def __init__(self, items=None):
        self.items = list(items or [])
        self._index = 0

    def addItems(self, items):
        self.items = list(items)

    def currentText(self):
        return self.items[self._index] if self.items else ""

    def setCurrentIndex(self, i):
        if 0 <= i < len(self.items):
            self._index = i

    def setToolTip(self, t):
        pass

    def blockSignals(self, b):
        return b


class FakeLabel:
    def __init__(self, text=""):
        self._text = text

    def setText(self, t):
        self._text = t or ""

    def text(self):
        return self._text

    def setStyleSheet(self, s):
        pass


class FakeButton:
    def __init__(self):
        self.enabled = True
        self.visible = True

    def setEnabled(self, e):
        self.enabled = e

    def setVisible(self, v):
        self.visible = v

    def setMinimumHeight(self, h):
        pass

    def setToolTip(self, t):
        pass

    def setProperty(self, k, v):
        pass

    def setStyleSheet(self, s):
        pass


class FakeTextEdit:
    def __init__(self):
        self._text = ""

    def toPlainText(self):
        return self._text

    def setPlainText(self, t):
        self._text = t or ""

    def clear(self):
        self._text = ""


class FakePlainTextEdit(FakeTextEdit):
    def blockSignals(self, b):
        return b


class FakeMsgButton:
    def __init__(self, role):
        self.role = role


class _ButtonRole:
    ActionRole = 1
    RejectRole = 2
    AcceptRole = 3


class FakeMessageBox:
    ButtonRole = _ButtonRole
    instances = []
    auto_click_index = None

    def __init__(self, parent=None):
        self.buttons = []
        self.default = None
        self.clicked = None
        FakeMessageBox.instances.append(self)

    def setWindowTitle(self, t):
        pass

    def setText(self, t):
        self.text = t

    def addButton(self, label, role):
        b = FakeMsgButton(role)
        self.buttons.append((label, b))
        return b

    def setDefaultButton(self, b):
        self.default = b

    def exec(self):
        idx = FakeMessageBox.auto_click_index
        if idx is not None and 0 <= idx < len(self.buttons):
            self.clicked = self.buttons[idx][1]
        return 1

    def clickedButton(self):
        return self.clicked


# Dùng enum + QListWidgetItem thật cho logic (mock aqt.qt chỉ là MagicMock)
addon.Qt = _QtFake
addon.QListWidgetItem = FakeListItem


def _cfg_ja():
    return {"detect_key": "front", "label": "🇯🇵 Tiếng Nhật"}


def _make_factory():
    """Tạo AnkiSmartFactory KHÔNG chạy __init__ (tránh UI) — chỉ test logic."""
    # Buộc ngôn ngữ UI về tiếng Việt để khớp các chuỗi mock hardcode trong test
    # (t() đọc theo get_language(); i18n_config.json có thể đang ở "en" do test trước)
    try:
        addon.set_language("vi")
    except Exception:
        pass
    obj = object.__new__(addon.AnkiSmartFactory)
    obj._current_lang = "japanese"
    obj._is_grammar = False
    obj._factory_state = {}
    obj._ai_attached_files = []
    obj._ai_attached_paths = []
    obj.ai_text_input = FakeTextEdit()
    obj.json_input = FakePlainTextEdit()
    obj.raw_data = []
    obj.prepared_data = []
    obj.txt_search = FakeLineEdit()
    obj.cbo_filter = FakeComboBox(["📂 Tất cả", "✨ Mới", "🔄 Cập nhật", "⚠️ Trùng mờ", "🔍 Nghĩa khác"])
    obj.preview_list = FakeListWidget()
    obj.spin_start = FakeSpin()
    obj.spin_end = FakeSpin()
    obj.btn_import = FakeButton()
    obj.btn_cancel_order = FakeButton()
    obj.btn_diff_meaning = FakeButton()
    obj.lbl_sel = FakeLabel()
    obj.lbl_ready = FakeLabel()
    obj.lbl_raw = FakeLabel()
    obj.lbl_status = FakeLabel()
    obj.lbl_ai_status = FakeLabel()
    obj._visible_indices = []
    obj._cfg = lambda: _cfg_ja()
    obj._flow_key = lambda: (obj._current_lang, "grammar" if obj._is_grammar else "vocab")
    obj._update_ai_files_label = lambda: None

    # Bind các method cần test
    for _m in ("_rebuild_preview", "_update_selection_label", "_select_all_visible",
               "_select_none_visible", "_get_export_indices", "_remove_factory_indices",
               "_cancel_order", "_save_current_flow", "_restore_current_flow",
               "_save_factory_state", "_load_factory_state", "_on_range_changed",
               "_load_history_to_factory", "_analyze_content"):
        obj.__dict__[_m] = addon.AnkiSmartFactory.__dict__[_m].__get__(obj, addon.AnkiSmartFactory)
    return obj


def _sample_cards():
    """Trả về prepared_data mẫu với đủ loại action."""
    return [
        {"item": {"front": "食べる", "meaning": "ăn", "level": "N5"}, "action": "add",
         "nid": None, "update_fields": [], "conflict_info": None},
        {"item": {"front": "飲む", "meaning": "uống", "level": "N5"}, "action": "update",
         "nid": 11, "update_fields": ["Meaning"], "conflict_info": None},
        {"item": {"front": "勉強", "meaning": "học", "level": "N3"}, "action": "add_partial",
         "nid": None, "update_fields": [], "conflict_info": None},
        {"item": {"front": "走る", "meaning": "chạy", "level": "N4"}, "action": "dup_diff",
         "nid": None, "update_fields": [], "conflict_info": {"existing_meaning": "trốn"}},
    ]


class TestRebuildPreview:
    def test_filter_by_action(self):
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f.cbo_filter.setCurrentIndex(1)  # ✨ Mới
        f._rebuild_preview()
        assert f._visible_indices == [0]
        assert f.preview_list.count() == 1

    def test_filter_update(self):
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f.cbo_filter.setCurrentIndex(2)  # 🔄 Cập nhật
        f._rebuild_preview()
        assert f._visible_indices == [1]

    def test_search_by_front(self):
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f.txt_search.setText("食")
        f._rebuild_preview()
        assert f._visible_indices == [0]

    def test_search_by_meaning(self):
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f.txt_search.setText("học")
        f._rebuild_preview()
        assert f._visible_indices == [2]

    def test_visible_renumbered_and_maps_to_index(self):
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f.cbo_filter.setCurrentIndex(1)  # ✨ Mới → chỉ index 0
        f._rebuild_preview()
        assert f.preview_list.count() == 1
        it = f.preview_list.item(0)
        assert it.data(_ItemDataRole.UserRole) == 0
        assert "1:" in it.text  # số thứ tự hiển thị bắt đầu từ 1

    def test_buttons_enabled(self):
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f._rebuild_preview()
        assert f.btn_import.enabled is True
        assert f.btn_cancel_order.enabled is True

    def test_check_preserved_across_rebuild(self):
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f._rebuild_preview()
        f.preview_list.item(0).setCheckState(_CheckState.Checked)
        f._rebuild_preview()  # dựng lại → vẫn giữ check index 0
        assert f.preview_list.item(0).checkState() == _CheckState.Checked


class TestGetExportIndices:
    def test_range_when_nothing_checked(self):
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f._rebuild_preview()
        f.spin_start.setValue(2)
        f.spin_end.setValue(3)
        assert f._get_export_indices() == [1, 2]

    def test_checked_wins(self):
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f._rebuild_preview()
        f.preview_list.item(0).setCheckState(_CheckState.Checked)
        f.preview_list.item(2).setCheckState(_CheckState.Checked)
        f.spin_start.setValue(1)
        f.spin_end.setValue(4)
        assert f._get_export_indices() == [0, 2]

    def test_range_respects_filter(self):
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f.cbo_filter.setCurrentIndex(1)  # ✨ Mới → visible = [0]
        f._rebuild_preview()
        assert f._get_export_indices() == [0]

    def test_no_data_returns_empty(self):
        f = _make_factory()
        f._rebuild_preview()
        assert f._get_export_indices() == []


class TestRangeAutoCheck:
    def test_range_auto_checks_rows(self):
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f._rebuild_preview()
        # Giả lập user đổi khoảng Từ 2 → đến 3
        f.spin_start.setValue(2)
        f.spin_end.setValue(3)
        f._on_range_changed()
        states = [f.preview_list.item(r).checkState() for r in range(4)]
        assert states == [_CheckState.Unchecked, _CheckState.Checked,
                          _CheckState.Checked, _CheckState.Unchecked]
        assert f._get_export_indices() == [1, 2]

    def test_range_full_checks_all(self):
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f._rebuild_preview()
        f.spin_start.setValue(1)
        f.spin_end.setValue(4)
        f._on_range_changed()
        assert all(f.preview_list.item(r).checkState() == _CheckState.Checked for r in range(4))
        assert f._get_export_indices() == [0, 1, 2, 3]

    def test_rebuild_does_not_auto_check(self):
        """Dựng lại danh sách KHÔNG được tự động tích chọn theo khoảng."""
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f._rebuild_preview()
        assert all(f.preview_list.item(r).checkState() == _CheckState.Unchecked for r in range(4))

    def test_range_respects_filter(self):
        f = _make_factory()
        f.prepared_data = _sample_cards()
        f.cbo_filter.setCurrentIndex(1)  # ✨ Mới → chỉ index 0 hiển thị
        f._rebuild_preview()
        f.spin_start.setValue(1)
        f.spin_end.setValue(1)
        f._on_range_changed()
        assert f.preview_list.item(0).checkState() == _CheckState.Checked
        assert f._get_export_indices() == [0]


class TestRemoveFactoryIndices:
    def test_remove_selected(self):
        f = _make_factory()
        f.raw_data = [c["item"] for c in _sample_cards()]
        f.prepared_data = _sample_cards()
        f._remove_factory_indices([0, 2])
        assert len(f.prepared_data) == 2
        assert len(f.raw_data) == 2
        assert f.prepared_data[0]["item"]["front"] == "飲む"

    def test_remove_all(self):
        f = _make_factory()
        f.raw_data = [c["item"] for c in _sample_cards()]
        f.prepared_data = _sample_cards()
        f._remove_factory_indices(list(range(4)))
        assert f.prepared_data == []
        assert f.raw_data == []
        assert f.preview_list.count() == 0

    def test_remove_out_of_range_ignored(self):
        f = _make_factory()
        f.raw_data = [c["item"] for c in _sample_cards()]
        f.prepared_data = _sample_cards()
        f._remove_factory_indices([99, -1])
        assert len(f.prepared_data) == 4


class TestPersistence:
    def test_cards_persist_roundtrip(self):
        f = _make_factory()
        f.raw_data = [c["item"] for c in _sample_cards()]
        f.prepared_data = _sample_cards()
        f.ai_text_input.setPlainText("ABC")
        f._save_current_flow()

        # Factory mới (mô phỏng mở lại cửa sổ)
        g = _make_factory()
        g._factory_state = g._load_factory_state()
        g._restore_current_flow()

        assert len(g.prepared_data) == 4
        assert len(g.raw_data) == 4
        assert g.ai_text_input.toPlainText() == "ABC"

    def test_flow_separated(self):
        f = _make_factory()
        f.raw_data = [c["item"] for c in _sample_cards()]
        f.prepared_data = _sample_cards()
        f._save_current_flow()

        # Chuyển sang ngôn ngữ khác → luồng riêng, không lẫn
        g = _make_factory()
        g._current_lang = "chinese"
        g._factory_state = g._load_factory_state()
        g._restore_current_flow()
        assert g.prepared_data == []
        assert g.raw_data == []

        # Quay lại luồng cũ → thẻ vẫn còn
        h = _make_factory()
        h._factory_state = h._load_factory_state()
        h._restore_current_flow()
        assert len(h.prepared_data) == 4


class TestLoadHistoryToFactory:
    def test_dump_items_into_factory(self):
        f = _make_factory()
        items = [
            {"front": "食べる", "meaning": "ăn", "jlptlevel": "N5"},
            {"front": "飲む", "meaning": "uống", "jlptlevel": "N4"},
        ]
        f._load_history_to_factory("japanese", items)
        assert len(f.raw_data) == 2
        assert f.raw_data[0]["front"] == "食べる"
        assert f.json_input.toPlainText() != ""
        assert "食べる" in f.json_input.toPlainText()
        assert f.lbl_raw.text() == "📊 Kho hàng: 2 mục"

    def test_empty_items_noop(self):
        f = _make_factory()
        f._load_history_to_factory("japanese", [])
        assert f.raw_data == []

    def test_switch_lang_when_differs(self):
        f = _make_factory()
        f._current_lang = "japanese"
        items = [{"front": "学校", "meaning": "trường học"}]
        # Không gọi _on_lang_changed thật (cần full UI); giả lập để xác nhận đổi lang
        calls = []
        f._on_lang_changed = lambda: calls.append(f._current_lang)
        f._load_history_to_factory("chinese", items)
        assert f._current_lang == "chinese"
        assert calls == ["chinese"]


class TestCancelOrder:
    def test_delete_all(self):
        addon.QMessageBox = FakeMessageBox
        f = _make_factory()
        f.raw_data = [c["item"] for c in _sample_cards()]
        f.prepared_data = _sample_cards()
        FakeMessageBox.instances = []
        FakeMessageBox.auto_click_index = 1  # 🧹 Xóa toàn bộ
        f._cancel_order()
        assert f.prepared_data == []
        assert f.raw_data == []

    def test_delete_selected(self):
        addon.QMessageBox = FakeMessageBox
        f = _make_factory()
        f.raw_data = [c["item"] for c in _sample_cards()]
        f.prepared_data = _sample_cards()
        f._rebuild_preview()
        f.preview_list.item(0).setCheckState(_CheckState.Checked)
        FakeMessageBox.instances = []
        FakeMessageBox.auto_click_index = 0  # 🗑️ Xóa các thẻ đã chọn
        f._cancel_order()
        assert len(f.prepared_data) == 3
        assert f.prepared_data[0]["item"]["front"] == "飲む"

    def test_cancel_keeps_everything(self):
        addon.QMessageBox = FakeMessageBox
        f = _make_factory()
        f.raw_data = [c["item"] for c in _sample_cards()]
        f.prepared_data = _sample_cards()
        FakeMessageBox.instances = []
        FakeMessageBox.auto_click_index = 2  # Hủy
        f._cancel_order()
        assert len(f.prepared_data) == 4

    def test_empty_factory_tooltip(self):
        addon.QMessageBox = FakeMessageBox
        called = []
        addon.tooltip = lambda *a, **k: called.append(a)
        f = _make_factory()
        f._cancel_order()
        assert len(called) == 1
