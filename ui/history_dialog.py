"""
History Dialog — Xem lại lịch sử từ vựng đã lưu (AI / import) và đưa lại vào xưởng.

Khi đóng Factory, người dùng vẫn có thể mở lại lịch sử này để xem lại,
tích chọn các từ cần và đưa vào xưởng để kiểm định & xuất xưởng lại.
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    Qt,
)
from aqt.utils import tooltip

from utils.ai_extractor import get_import_history_items

_LANG_OPTIONS = [
    ("📂 Tất cả", None),
    ("🇯🇵 Tiếng Nhật", "japanese"),
    ("🇨🇳 Tiếng Trung", "chinese"),
    ("🇰🇷 Tiếng Hàn", "korean"),
]

_LANG_TAG = {
    "japanese": "🇯🇵",
    "chinese": "🇨🇳",
    "korean": "🇰🇷",
}


class HistoryBrowserDialog(QDialog):
    """Xem lịch sử từ vựng đã lưu; chọn và đưa lại vào xưởng để import lại."""

    def __init__(self, parent=None, current_lang="japanese"):
        super().__init__(parent)
        self.current_lang = current_lang if current_lang in ("japanese", "chinese", "korean") else "japanese"
        self.accepted_items = []
        self.accepted_lang = self.current_lang
        self._all_entries = []   # [(lang, item_dict), ...]
        self._visible = []

        self.setWindowTitle("📚 Lịch Sử AI — Từ Vựng Đã Lưu")
        self.setMinimumSize(780, 560)
        self.resize(900, 650)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self._setup_ui()
        self._reload_data()

    def _setup_ui(self):
        vl = QVBoxLayout(self)

        header = QLabel(
            "<h3>📚 Lịch Sử Từ Vựng Đã Lưu (AI / Import)</h3>"
            "<p style='color:#555;font-size:11px;'>"
            "Xem lại các từ đã được AI trích xuất hoặc import. "
            "Tích chọn rồi bấm <b>📥 Đưa Vào Xưởng</b> để đưa vào xưởng, "
            "sau đó bấm <b>Kiểm Định</b> và <b>XUẤT XƯỞNG</b> lại."
            "</p>"
        )
        header.setWordWrap(True)
        vl.addWidget(header)

        # ── Search + lọc ngôn ngữ ──
        bar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Tìm theo từ / nghĩa / cấp độ...")
        self.txt_search.textChanged.connect(self._rebuild_list)
        bar.addWidget(self.txt_search, 1)
        self.cbo_lang = QComboBox()
        for label, _ in _LANG_OPTIONS:
            self.cbo_lang.addItem(label)
        for i, (_, lk) in enumerate(_LANG_OPTIONS):
            if lk == self.current_lang:
                self.cbo_lang.setCurrentIndex(i)
                break
        self.cbo_lang.setToolTip("Lọc lịch sử theo ngôn ngữ")
        self.cbo_lang.currentIndexChanged.connect(self._reload_data)
        bar.addWidget(self.cbo_lang, 0)
        vl.addLayout(bar)

        self.lst = QListWidget()
        self.lst.setToolTip("Tích chọn các từ muốn đưa vào xưởng")
        vl.addWidget(self.lst, 1)

        # ── Nút chọn nhanh + đếm ──
        sel = QHBoxLayout()
        self.btn_select_all = QPushButton("✅ Chọn Tất Cả")
        self.btn_select_all.clicked.connect(self._select_all)
        sel.addWidget(self.btn_select_all)
        self.btn_select_none = QPushButton("☐ Bỏ Chọn")
        self.btn_select_none.clicked.connect(self._select_none)
        sel.addWidget(self.btn_select_none)
        sel.addStretch()
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("color:#2980b9;font-weight:bold;")
        sel.addWidget(self.lbl_count)
        vl.addLayout(sel)

        # ── Nút hành động ──
        btn_row = QHBoxLayout()
        btn_close = QPushButton("❌ Đóng")
        btn_close.setStyleSheet(
            "padding:10px 20px;background:#95a5a6;color:white;font-weight:bold;border-radius:8px;"
        )
        btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_close)
        btn_row.addStretch()
        self.btn_pull = QPushButton("📥 Đưa Vào Xưởng")
        self.btn_pull.setStyleSheet(
            "padding:10px 30px;background:#27ae60;color:white;font-weight:bold;border-radius:8px;font-size:14px;"
        )
        self.btn_pull.setToolTip("Đưa các từ đã chọn vào xưởng để Kiểm Định & xuất xưởng lại")
        self.btn_pull.clicked.connect(self._on_pull)
        btn_row.addWidget(self.btn_pull)
        vl.addLayout(btn_row)

    def _selected_lang(self):
        idx = self.cbo_lang.currentIndex()
        if 0 <= idx < len(_LANG_OPTIONS):
            return _LANG_OPTIONS[idx][1]
        return None

    def _reload_data(self):
        lang = self._selected_lang()
        self._all_entries = get_import_history_items(lang=lang, limit=5000)
        self._rebuild_list()

    def _rebuild_list(self):
        query = self.txt_search.text().strip().lower()
        self.lst.blockSignals(True)
        self.lst.clear()
        self._visible = []
        for lang, item in self._all_entries:
            front = str(item.get("front", ""))
            meaning = str(item.get("meaning", ""))
            if query and query not in front.lower() and query not in meaning.lower():
                continue
            self._visible.append((lang, item))
        for lang, item in self._visible:
            front = str(item.get("front", ""))
            meaning = str(item.get("meaning", ""))
            level = str(item.get("jlptlevel") or item.get("hsk_level") or item.get("level", "") or "")
            tag = _LANG_TAG.get(lang, "")
            text = f"{front} — {meaning}"
            if level:
                text += f"  [{level}]"
            li = QListWidgetItem(f"{tag} {text}")
            li.setFlags(li.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            li.setCheckState(Qt.CheckState.Unchecked)
            self.lst.addItem(li)
        self.lst.blockSignals(False)
        self.lbl_count.setText(f"📚 {len(self._visible)} từ đang hiển thị")

    def _select_all(self):
        self.lst.blockSignals(True)
        for row in range(self.lst.count()):
            self.lst.item(row).setCheckState(Qt.CheckState.Checked)
        self.lst.blockSignals(False)

    def _select_none(self):
        self.lst.blockSignals(True)
        for row in range(self.lst.count()):
            self.lst.item(row).setCheckState(Qt.CheckState.Unchecked)
        self.lst.blockSignals(False)

    def _checked_entries(self):
        """Trả về [(lang, item)] của các dòng đang tích chọn."""
        out = []
        for row in range(self.lst.count()):
            if self.lst.item(row).checkState() == Qt.CheckState.Checked:
                if row < len(self._visible):
                    out.append(self._visible[row])
        return out

    def _on_pull(self):
        checked = self._checked_entries()
        if not checked:
            tooltip("⚠️ Chưa chọn từ nào. Hãy tích chọn các từ cần đưa vào xưởng.")
            return
        self.accepted_items = [item for _, item in checked]
        langs = {l for l, _ in checked}
        if len(langs) == 1:
            self.accepted_lang = langs.pop()
        else:
            self.accepted_lang = self.current_lang
        self.accept()
