"""
Verify Dialog — Hiển thị báo cáo từ vựng cùng mặt chữ nhưng khác nghĩa.
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QGroupBox, QScrollArea,
    QWidget, Qt,
)
from aqt.utils import showInfo, tooltip


def show_diff_meaning_dialog(parent, prepared_data, cfg):
    """Hiển thị dialog báo cáo các từ vựng có cùng mặt chữ nhưng khác nghĩa,
    cho phép người dùng chọn từ nào được phép thêm vào.

    Args:
        parent: Parent widget
        prepared_data: List các dict đã chuẩn bị (mutable)
        cfg: Language config dict

    Returns:
        True nếu có thay đổi (cần refresh UI)
    """
    dup_diff_items = [(i, d) for i, d in enumerate(prepared_data) if d["action"] == "dup_diff"]
    if not dup_diff_items:
        tooltip("Không có từ vựng nào thuộc diện 'nghĩa khác' để báo cáo.")
        return False

    dlg = QDialog(parent)
    dlg.setWindowTitle("🔍 Báo Cáo Nghĩa Khác — Xác Nhận Thêm Từ Vựng")
    dlg.setMinimumSize(750, 500)
    vl = QVBoxLayout(dlg)

    lbl_title = QLabel(
        f"<h3>🔍 Phát hiện <span style='color:#e67e22;'>{len(dup_diff_items)} từ vựng</span> "
        f"có cùng mặt chữ nhưng <b>nghĩa khác</b> với từ đã có.</h3>"
        f"<p style='color:#555;'>Chọn những từ bạn muốn <b>cho phép thêm</b> dù trùng mặt chữ. "
        f"Các từ không chọn sẽ bị loại bỏ.</p>"
    )
    lbl_title.setWordWrap(True)
    vl.addWidget(lbl_title)

    # Tạo scroll area chứa danh sách
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll_widget = QWidget()
    scroll_layout = QVBoxLayout(scroll_widget)

    checkboxes = []

    dk = cfg["detect_key"]
    furi_label = cfg["furi_label"]
    furi_json_key = cfg["furi_json_key"]
    level_json_key = cfg["level_json_key"]

    for idx, (orig_idx, d) in enumerate(dup_diff_items):
        item = d["item"]
        ci = d.get("conflict_info", {})
        front_new = str(item.get(dk, item.get('front', ''))).strip()
        meaning_new = str(item.get('meaning', '')).strip()
        furigana_new = str(item.get(furi_json_key, '')).strip()
        level_new = str(item.get(level_json_key, '')).strip()

        front_old = ci.get("existing_front", front_new)
        meaning_old = ci.get("existing_meaning", "")
        furigana_old = ci.get("existing_furigana", "")
        level_old = ci.get("existing_level", "")

        # Tạo group box cho mỗi mục
        grp = QGroupBox(f"#{orig_idx + 1}: {front_new}")
        grp.setStyleSheet("QGroupBox{font-weight:bold;font-size:13px;color:#e67e22;}")
        grp_layout = QVBoxLayout()

        # Dòng so sánh
        comp_layout = QHBoxLayout()

        # Cột MỚI
        new_box = QGroupBox("📥 TỪ MỚI (đang nhập)")
        new_box.setStyleSheet("QGroupBox{font-weight:bold;color:#27ae60;}")
        new_layout = QVBoxLayout()
        new_layout.addWidget(QLabel(f"<b>Mặt chữ:</b> {front_new}"))
        new_layout.addWidget(QLabel(f"<b>Nghĩa:</b> <span style='color:#27ae60;font-size:15px;'>{meaning_new}</span>"))
        if furigana_new:
            new_layout.addWidget(QLabel(f"<b>{furi_label}:</b> {furigana_new}"))
        if level_new:
            new_layout.addWidget(QLabel(f"<b>Cấp độ:</b> {level_new}"))
        new_box.setLayout(new_layout)
        comp_layout.addWidget(new_box)

        # Mũi tên
        arrow_lbl = QLabel("➡️")
        arrow_lbl.setStyleSheet("font-size:24px;")
        arrow_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comp_layout.addWidget(arrow_lbl)

        # Cột CŨ
        old_box = QGroupBox("📚 TỪ ĐÃ CÓ (trong Anki)")
        old_box.setStyleSheet("QGroupBox{font-weight:bold;color:#e74c3c;}")
        old_layout = QVBoxLayout()
        old_layout.addWidget(QLabel(f"<b>Mặt chữ:</b> {front_old}"))
        old_layout.addWidget(QLabel(f"<b>Nghĩa:</b> <span style='color:#e74c3c;font-size:15px;'>{meaning_old}</span>"))
        if furigana_old:
            old_layout.addWidget(QLabel(f"<b>{furi_label}:</b> {furigana_old}"))
        if level_old:
            old_layout.addWidget(QLabel(f"<b>Cấp độ:</b> {level_old}"))
        old_box.setLayout(old_layout)
        comp_layout.addWidget(old_box)

        grp_layout.addLayout(comp_layout)

        # Checkbox
        cb = QCheckBox(f"✅ Cho phép thêm từ mới \"{front_new}\" với nghĩa \"{meaning_new}\"")
        cb.setChecked(True)
        cb.setStyleSheet("font-size:13px;font-weight:bold;padding:6px;")
        grp_layout.addWidget(cb)

        grp.setLayout(grp_layout)
        scroll_layout.addWidget(grp)

        checkboxes.append((orig_idx, cb))

    scroll_layout.addStretch()
    scroll.setWidget(scroll_widget)
    vl.addWidget(scroll)

    # Nút hành động
    btn_layout = QHBoxLayout()

    btn_select_all = QPushButton("☑️ Chọn tất cả")
    btn_select_all.clicked.connect(lambda: [cb.setChecked(True) for _, cb in checkboxes])
    btn_layout.addWidget(btn_select_all)

    btn_deselect_all = QPushButton("☐ Bỏ chọn tất cả")
    btn_deselect_all.clicked.connect(lambda: [cb.setChecked(False) for _, cb in checkboxes])
    btn_layout.addWidget(btn_deselect_all)

    btn_layout.addStretch()

    btn_cancel = QPushButton("❌ Hủy")
    btn_cancel.clicked.connect(dlg.reject)
    btn_layout.addWidget(btn_cancel)

    btn_confirm = QPushButton("🚀 XÁC NHẬN & CHO QUA")
    btn_confirm.setStyleSheet(
        "padding:10px 20px;background:#27ae60;color:white;font-weight:bold;border-radius:8px;"
    )
    btn_confirm.clicked.connect(dlg.accept)
    btn_layout.addWidget(btn_confirm)

    vl.addLayout(btn_layout)

    if dlg.exec() != QDialog.DialogCode.Accepted:
        return False

    # Xử lý: chuyển các mục được chọn từ "dup_diff" → "add"
    approved = 0
    rejected_indices = []
    for orig_idx, cb in checkboxes:
        if cb.isChecked():
            prepared_data[orig_idx]["action"] = "add"
            prepared_data[orig_idx]["nid"] = None
            prepared_data[orig_idx]["update_fields"] = []
            prepared_data[orig_idx]["conflict_info"] = None
            approved += 1
        else:
            rejected_indices.append(orig_idx)

    # Xóa các mục bị từ chối (duyệt từ cuối lên để không ảnh hưởng index)
    for orig_idx in reversed(rejected_indices):
        del prepared_data[orig_idx]

    return True
