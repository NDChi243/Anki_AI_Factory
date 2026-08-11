"""
🗂️ Deck Manager Dialog — UI quản lý Parent/Sub Decks ngay trong add-on.

Tree view hiển thị cấu trúc deck từ Anki collection. Cho phép:
- Tạo Parent Deck mới
- Tạo Sub Deck bên trong deck đang chọn
- Đổi tên deck
- Xóa deck (kèm sub deck + thẻ)
- Làm mới tức thì (mọi thao tác đều gọi refresh_anki để UI ngoài Anki cập nhật)
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTreeWidget, QTreeWidgetItem, QInputDialog,
    QMessageBox, Qt,
)
from aqt.utils import tooltip

from utils.deck_manager import (
    get_deck_tree, create_deck, rename_deck, delete_deck, refresh_anki,
)
from utils.i18n import t


class DeckManagerDialog(QDialog):
    """Dialog quản lý deck parent/sub với cập nhật tức thì."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("deck_manage_title"))
        self.setMinimumSize(520, 520)
        self.resize(620, 600)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self._setup_ui()
        self._reload_tree()

    # ── UI ────────────────────────────────────────────────
    def _setup_ui(self):
        vl = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(QLabel(
            "<h3>🗂️ Quản Lý Deck</h3>"
            f"<p style='color:#555;font-size:11px;'>{t('deck_manage_desc')}</p>"
        ))
        header.addStretch()
        vl.addLayout(header)

        # Tree view
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([t("deck_col_name"), t("deck_col_cards")])
        self.tree.setColumnWidth(0, 320)
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        vl.addWidget(self.tree, 1)

        # Buttons
        btn_row = QHBoxLayout()

        self.btn_add_parent = QPushButton(t("deck_add_parent"))
        self.btn_add_parent.setToolTip(t("deck_add_parent_prompt"))
        self.btn_add_parent.clicked.connect(self._add_parent)
        btn_row.addWidget(self.btn_add_parent)

        self.btn_add_sub = QPushButton(t("deck_add_sub"))
        self.btn_add_sub.setToolTip(t("deck_add_sub_tip"))
        self.btn_add_sub.clicked.connect(self._add_sub)
        btn_row.addWidget(self.btn_add_sub)

        self.btn_rename = QPushButton(t("deck_rename"))
        self.btn_rename.setToolTip(t("deck_rename_prompt"))
        self.btn_rename.clicked.connect(self._rename)
        btn_row.addWidget(self.btn_rename)

        self.btn_delete = QPushButton(t("deck_delete"))
        self.btn_delete.setToolTip(t("deck_delete_title"))
        self.btn_delete.clicked.connect(self._delete)
        btn_row.addWidget(self.btn_delete)

        self.btn_refresh = QPushButton(t("deck_refresh"))
        self.btn_refresh.setToolTip(t("deck_refresh"))
        self.btn_refresh.clicked.connect(self._reload_tree)
        btn_row.addWidget(self.btn_refresh)

        vl.addLayout(btn_row)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color:#27ae60;font-size:11px;")
        vl.addWidget(self.lbl_status)

    # ── Tree helpers ─────────────────────────────────────
    def _reload_tree(self):
        """Tải lại cây deck từ Anki collection."""
        self.tree.clear()
        tree = get_deck_tree()
        for node in tree:
            item = self._add_tree_node(None, node)
            # Item gốc phải được thêm vào tree bằng addTopLevelItem
            self.tree.addTopLevelItem(item)
        self.tree.expandAll()
        self.lbl_status.setText(t("deck_count_parents", count=len(tree)))

    def _add_tree_node(self, parent_item, node):
        item = QTreeWidgetItem(parent_item)
        # Hiển thị segment cuối cùng (sau "::") để tree gọn gàng,
        # nhưng lưu tên đầy đủ trong UserRole để thao tác chính xác.
        display_name = node["name"].split("::")[-1]
        item.setText(0, display_name)
        item.setText(1, str(node["card_count"]))
        item.setData(0, Qt.ItemDataRole.UserRole, node["name"])
        for child in node.get("children", []):
            self._add_tree_node(item, child)
        return item

    def _selected_deck_name(self):
        """Lấy tên deck đang chọn (hoặc None)."""
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.ItemDataRole.UserRole)

    # ── Actions ──────────────────────────────────────────
    def _add_parent(self):
        name, ok = QInputDialog.getText(
            self, t("deck_add_parent_title"), t("deck_add_parent_prompt")
        )
        if not ok or not name.strip():
            return
        deck_id = create_deck(name.strip())
        if deck_id is not None:
            refresh_anki()
            self._reload_tree()
            tooltip(t("deck_created", name=name.strip()))
        else:
            QMessageBox.warning(self, t("deck_add_parent_title"), t("err_file_read", error="create"))

    def _add_sub(self):
        parent_name = self._selected_deck_name()
        if not parent_name:
            tooltip(t("deck_select_first"))
            return
        name, ok = QInputDialog.getText(
            self, t("deck_add_sub_title"),
            t("deck_add_sub_prompt", parent=parent_name),
        )
        if not ok or not name.strip():
            return
        full_name = f"{parent_name}::{name.strip()}"
        deck_id = create_deck(full_name)
        if deck_id is not None:
            refresh_anki()
            self._reload_tree()
            tooltip(t("deck_created", name=full_name))
        else:
            QMessageBox.warning(self, t("deck_add_sub_title"), t("err_file_read", error="create"))

    def _rename(self):
        old_name = self._selected_deck_name()
        if not old_name:
            tooltip(t("deck_select_first"))
            return
        new_name, ok = QInputDialog.getText(
            self, t("deck_rename_title"), t("deck_rename_prompt"), text=old_name
        )
        if not ok or not new_name.strip():
            return
        if rename_deck(old_name, new_name.strip()):
            refresh_anki()
            self._reload_tree()
            tooltip(t("deck_renamed", old=old_name, new=new_name.strip()))
        else:
            QMessageBox.warning(self, t("deck_rename_title"), t("err_file_read", error="rename"))

    def _delete(self):
        name = self._selected_deck_name()
        if not name:
            tooltip(t("deck_select_first"))
            return
        ret = QMessageBox.question(
            self, t("deck_delete_title"),
            t("deck_delete_confirm", name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret != QMessageBox.StandardButton.Yes:
            return
        if delete_deck(name):
            refresh_anki()
            self._reload_tree()
            tooltip(t("deck_deleted", name=name))
        else:
            QMessageBox.warning(self, t("deck_delete_title"), t("err_file_read", error="delete"))

    def _on_context_menu(self, pos):
        """Menu chuột phải nhanh."""
        from aqt.qt import QMenu
        menu = QMenu(self)
        menu.addAction(t("deck_add_sub"), self._add_sub)
        menu.addAction(t("deck_rename"), self._rename)
        menu.addAction(t("deck_delete"), self._delete)
        menu.exec(self.tree.viewport().mapToGlobal(pos))
