"""
🎨 Glassmorphism Theme Engine — AnkiTool.

Cung cấp:
- build_stylesheet(cfg): tạo QSS glassmorphism hiện đại từ cấu hình.
- apply_theme(widget, cfg): áp theme cho widget (dialog/panel) + lưu config.
- load_config() / save_config(cfg): đọc/ghi cấu hình tại utils/ui_theme.json.
- ThemeDialog: hộp thoại tùy chỉnh sâu (theme, màu nhấn, độ trong kính, cỡ chữ, bo góc).
- snap_left / snap_right / snap_maximize: gắn cửa sổ nửa màn hình để chia đôi
  với ứng dụng khác hoặc chính Anki trên cùng một màn hình.
"""

import json
import os

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QSlider, QSpinBox, QColorDialog, QGroupBox, QGridLayout,
    Qt, QColor,
)
from aqt.utils import tooltip

from utils.i18n import t

# QSplitter có thể không có trong aqt.qt của một số version Anki → fallback
try:
    from aqt.qt import QSplitter
except ImportError:
    try:
        from PyQt6.QtWidgets import QSplitter
    except ImportError:
        try:
            from PyQt5.QtWidgets import QSplitter
        except ImportError:
            try:
                from PySide6.QtWidgets import QSplitter
            except ImportError:
                try:
                    from PySide2.QtWidgets import QSplitter
                except ImportError:
                    # Fallback cuối: stub class (chỉ để import không lỗi khi test ngoài Anki)
                    class QSplitter:
                        def __init__(self, *args, **kwargs):
                            pass

THEME_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "utils", "ui_theme.json",
)

DEFAULT_CONFIG = {
    "preset": "glass_dark",   # chủ đề nền
    "accent": "#6aa7ff",      # màu nhấn
    "glass_alpha": 7,         # % độ trong của kính (4-26)
    "font_size": 13,          # cỡ chữ cơ bản (11-17)
    "radius": 14,             # bo góc (8-22)
}

PRESETS = {
    "glass_dark": {
        "name": "🌑 Glass Dark",
        "bg1": "#0b1b2a",
        "bg2": "#172a45",
        "bg3": "#1f3a5f",
        "text": "#eaf0f6",
        "text_dim": "rgba(234,240,246,0.66)",
    },
    "glass_light": {
        "name": "🌕 Glass Light",
        "bg1": "#dfe9f3",
        "bg2": "#c3d7ec",
        "bg3": "#a9c4e4",
        "text": "#22303f",
        "text_dim": "rgba(34,48,63,0.62)",
    },
    "midnight": {
        "name": "🌌 Midnight",
        "bg1": "#05070f",
        "bg2": "#0c1220",
        "bg3": "#171f38",
        "text": "#d7e1f0",
        "text_dim": "rgba(215,225,240,0.6)",
    },
}

ACCENT_PRESETS = [
    ("🔵 Xanh dương", "#6aa7ff"),
    ("🟣 Tím", "#a78bfa"),
    ("🟢 Xanh lá", "#34d399"),
    ("🟠 Cam", "#fbbf24"),
    ("🌸 Hồng", "#f472b6"),
    ("🔴 Đỏ", "#f87171"),
    ("🩵 Cyan", "#22d3ee"),
]


# ── Color helpers ─────────────────────────────────────────
def _hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lighten(hex_color, factor=0.22):
    r, g, b = _hex_to_rgb(hex_color)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def _darken(hex_color, factor=0.15):
    r, g, b = _hex_to_rgb(hex_color)
    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


# ── QSS template (dùng token __XXX__ để tránh xung đột dấu ngoặc CSS) ──
_QSS_TEMPLATE = """
QDialog, QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 __BG1__, stop:0.5 __BG2__, stop:1 __BG3__);
}
QWidget {
    color: __TEXT__;
    font-size: __FONT__px;
}
QLabel { background: transparent; color: __TEXT__; }
QLabel[class="dim"] { color: __TEXT_DIM__; }
QToolTip {
    background: __BG2__; color: __TEXT__;
    border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; padding: 4px 8px;
}

QGroupBox {
    background: rgba(255,255,255,__GLASS__);
    border: 1px solid rgba(255,255,255,__BORDER__);
    border-radius: __RADIUS__px;
    margin-top: __RADIUS__px;
    padding: 10px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 2px 8px;
    color: __ACCENT__;
    background: transparent;
}

QPushButton {
    background: rgba(255,255,255,__GLASS_PLUS__);
    color: __TEXT__;
    border: 1px solid rgba(255,255,255,__BORDER__);
    border-radius: 10px;
    padding: 7px 14px;
    font-weight: 600;
}
QPushButton:hover { background: rgba(255,255,255,__GLASS_HOVER__); border-color: rgba(255,255,255,__BORDER_HOVER__); }
QPushButton:pressed { background: rgba(255,255,255,__GLASS_PRESS__); }
QPushButton:disabled { color: __TEXT_DIM__; background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.05); }
QPushButton:checked {
    background: rgba(255,255,255,0.16);
    border: 1px solid __ACCENT__;
    color: __ACCENT__;
}

/* Nhóm nút màu ngữ nghĩa — dùng dynamic property class="..." */
QPushButton[class="primary"] { background: __ACCENT__; color: #ffffff; border: none; }
QPushButton[class="primary"]:hover { background: __ACCENT_LIGHT__; }
QPushButton[class="success"] { background: #2ecc71; color: #ffffff; border: none; }
QPushButton[class="success"]:hover { background: #43d97f; }
QPushButton[class="danger"] { background: #e74c3c; color: #ffffff; border: none; }
QPushButton[class="danger"]:hover { background: #ef5b4d; }
QPushButton[class="warning"] { background: #f39c12; color: #ffffff; border: none; }
QPushButton[class="warning"]:hover { background: #f5ad3a; }
QPushButton[class="purple"] { background: #8e44ad; color: #ffffff; border: none; }
QPushButton[class="purple"]:hover { background: #a24fbf; }
QPushButton[class="info"] { background: #3498db; color: #ffffff; border: none; }
QPushButton[class="info"]:hover { background: #4aa3df; }
QPushButton[class="ghost"] { background: transparent; border: 1px solid rgba(255,255,255,__BORDER__); }
QPushButton[class="ghost"]:hover { background: rgba(255,255,255,__GLASS_HOVER__); }

QLineEdit, QPlainTextEdit, QTextEdit, QListWidget, QSpinBox, QDoubleSpinBox, QComboBox {
    background: rgba(255,255,255,__GLASS__);
    border: 1px solid rgba(255,255,255,__BORDER__);
    border-radius: 10px;
    color: __TEXT__;
    padding: 5px 8px;
    selection-background-color: __ACCENT__;
    selection-color: #ffffff;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QListWidget:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid __ACCENT__;
}
QListWidget::item { padding: 5px 8px; border-radius: 8px; }
QListWidget::item:selected { background: __ACCENT__; color: #ffffff; }
QListWidget::item:hover:!selected { background: rgba(255,255,255,0.08); }

QComboBox::drop-down { border: none; width: 26px; }
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid __TEXT_DIM__;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background: __BG2__; color: __TEXT__;
    border: 1px solid rgba(255,255,255,__BORDER__);
    border-radius: 10px;
    selection-background-color: __ACCENT__;
    selection-color: #ffffff;
}

QCheckBox { color: __TEXT__; spacing: 8px; background: transparent; }
QCheckBox::indicator {
    width: 16px; height: 16px; border-radius: 5px;
    border: 1px solid rgba(255,255,255,0.35); background: transparent;
}
QCheckBox::indicator:hover { border-color: __ACCENT_LIGHT__; }
QCheckBox::indicator:checked { background: __ACCENT__; border-color: __ACCENT__; }

QProgressBar {
    background: rgba(255,255,255,0.08);
    border: none; border-radius: 9px;
    color: #ffffff; font-weight: 700; text-align: center;
    min-height: 16px; max-height: 18px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 __ACCENT__, stop:1 __ACCENT_LIGHT__);
    border-radius: 9px;
}

QSplitter::handle { background: rgba(255,255,255,0.06); }
QSplitter::handle:hover { background: __ACCENT__; }
QSplitter::handle:horizontal { width: 5px; }
QSplitter::handle:vertical { height: 5px; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: rgba(255,255,255,0.18); border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.3); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: rgba(255,255,255,0.18); border-radius: 5px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: rgba(255,255,255,0.3); }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background: transparent; border: none; width: 18px;
}
"""


def build_stylesheet(cfg=None):
    cfg = cfg or load_config()
    preset = PRESETS.get(cfg.get("preset"), PRESETS["glass_dark"])
    accent = cfg.get("accent") or "#6aa7ff"
    accent_light = _lighten(accent, 0.28)
    alpha = max(3, min(28, int(cfg.get("glass_alpha", 7)))) / 100.0
    font_size = max(10, min(18, int(cfg.get("font_size", 13))))
    radius = max(6, min(24, int(cfg.get("radius", 14))))

    tokens = {
        "__BG1__": preset["bg1"],
        "__BG2__": preset["bg2"],
        "__BG3__": preset["bg3"],
        "__TEXT__": preset["text"],
        "__TEXT_DIM__": preset["text_dim"],
        "__ACCENT__": accent,
        "__ACCENT_LIGHT__": accent_light,
        "__GLASS__": f"{alpha:.2f}",
        "__GLASS_PLUS__": f"{min(alpha + 0.04, 0.30):.2f}",
        "__GLASS_HOVER__": f"{min(alpha + 0.09, 0.38):.2f}",
        "__GLASS_PRESS__": f"{min(alpha + 0.02, 0.30):.2f}",
        "__BORDER__": f"{min(alpha + 0.10, 0.32):.2f}",
        "__BORDER_HOVER__": f"{min(alpha + 0.18, 0.45):.2f}",
        "__FONT__": str(font_size),
        "__RADIUS__": str(radius),
    }
    qss = _QSS_TEMPLATE
    for key, val in tokens.items():
        qss = qss.replace(key, val)
    return qss


# ── Config persistence ────────────────────────────────────
def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(THEME_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg.update({k: v for k, v in data.items() if k in DEFAULT_CONFIG})
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        os.makedirs(os.path.dirname(THEME_FILE), exist_ok=True)
        with open(THEME_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def apply_theme(widget, cfg=None):
    cfg = cfg or load_config()
    widget.setStyleSheet(build_stylesheet(cfg))
    save_config(cfg)
    return cfg


# ── RatioSplitter: kéo phân cách mượt, giới hạn tỷ lệ cột ──
class RatioSplitter(QSplitter):
    """QSplitter giới hạn mỗi cột trong khoảng MIN_RATIO–MAX_RATIO (mặc định 3/10–7/10).

    - Kéo mượt, không bị khóa cứng.
    - Không cho thu gọn hết cột (min 30%).
    - Không cho cột nào chiếm quá 70% (max 70%).
    """

    MIN_RATIO = 0.30
    MAX_RATIO = 0.70

    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._clamping = False
        self.setChildrenCollapsible(False)
        self.setOpaqueResize(True)
        self.splitterMoved.connect(self._on_moved)

    def _clamp(self):
        """Siết tỷ lệ mỗi cột về [MIN_RATIO, MAX_RATIO] của tổng chiều rộng."""
        if self._clamping:
            return
        self._clamping = True
        try:
            sizes = self.sizes()
            total = sum(sizes)
            n = len(sizes)
            if n < 2 or total <= 0:
                return
            lo = int(total * self.MIN_RATIO)
            hi = int(total * self.MAX_RATIO)
            new_sizes = list(sizes)
            changed = False
            for i in range(n):
                if new_sizes[i] < lo:
                    new_sizes[i] = lo
                    changed = True
                elif new_sizes[i] > hi:
                    new_sizes[i] = hi
                    changed = True
            if changed:
                self.setSizes(new_sizes)
        finally:
            self._clamping = False

    def _on_moved(self, pos, index):
        self._clamp()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._clamp()


# ── Window snap helpers (chia đôi màn hình với app khác / Anki) ──
def snap_left(widget):
    geo = widget.screen().availableGeometry()
    widget.showNormal()
    widget.setGeometry(geo.x(), geo.y(), geo.width() // 2, geo.height())


def snap_right(widget):
    geo = widget.screen().availableGeometry()
    w = geo.width() // 2
    widget.showNormal()
    widget.setGeometry(geo.x() + w, geo.y(), w, geo.height())


def snap_maximize(widget):
    widget.showMaximized()


# ── Theme customization dialog ────────────────────────────
class ThemeDialog(QDialog):
    """Hộp thoại tùy chỉnh giao diện glassmorphism — cập nhật live."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("theme_title"))
        self.setMinimumSize(480, 560)
        self.resize(520, 600)
        self.cfg = load_config()
        self._build_ui()
        self._load_current()

    def _build_ui(self):
        vl = QVBoxLayout(self)

        title = QLabel(f"<h3>{t('theme_header')}</h3>")
        vl.addWidget(title)
        vl.addWidget(QLabel(t("theme_live_hint")))

        gl = QGridLayout()
        gl.setHorizontalSpacing(10)
        gl.setVerticalSpacing(10)

        gl.addWidget(QLabel(t("theme_preset_label")), 0, 0)
        self.cbo_preset = QComboBox()
        for key, p in PRESETS.items():
            self.cbo_preset.addItem(p["name"], key)
        gl.addWidget(self.cbo_preset, 0, 1)

        gl.addWidget(QLabel(t("theme_accent_label")), 1, 0)
        self.cbo_accent = QComboBox()
        for label, hexv in ACCENT_PRESETS:
            self.cbo_accent.addItem(f"{label}  ({hexv})", hexv)
        self.cbo_accent.addItem("🌈 Tùy chỉnh...", "__custom__")
        gl.addWidget(self.cbo_accent, 1, 1)

        gl.addWidget(QLabel(t("theme_alpha_label")), 2, 0)
        self.slider_alpha = QSlider(Qt.Orientation.Horizontal)
        self.slider_alpha.setRange(4, 26)
        self.lbl_alpha = QLabel("")
        alpha_row = QHBoxLayout()
        alpha_row.addWidget(self.slider_alpha, 1)
        alpha_row.addWidget(self.lbl_alpha, 0)
        gl.addLayout(alpha_row, 2, 1)

        gl.addWidget(QLabel(t("theme_font_label")), 3, 0)
        self.spin_font = QSpinBox()
        self.spin_font.setRange(11, 17)
        self.spin_font.setSuffix(" px")
        gl.addWidget(self.spin_font, 3, 1)

        gl.addWidget(QLabel(t("theme_radius_label")), 4, 0)
        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(8, 22)
        self.spin_radius.setSuffix(" px")
        gl.addWidget(self.spin_radius, 4, 1)

        vl.addLayout(gl)

        # Preview panel
        self.preview = QGroupBox(t("theme_preview_grp"))
        pv = QVBoxLayout()
        row = QHBoxLayout()
        b1 = QPushButton(t("btn_button_sample"))
        b1.setProperty("class", "primary")
        b2 = QPushButton(t("btn_success_sample"))
        b2.setProperty("class", "success")
        b3 = QPushButton(t("btn_ghost_sample"))
        b3.setProperty("class", "ghost")
        row.addWidget(b1)
        row.addWidget(b2)
        row.addWidget(b3)
        pv.addLayout(row)
        inp = QComboBox()
        inp.addItems([t("theme_combo_sample"), t("item_label_grammar"), "Topic A", "Topic B"])
        pv.addWidget(inp)
        self.preview.setLayout(pv)
        vl.addWidget(self.preview, 1)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        btn_apply = QPushButton(t("theme_apply_save"))
        btn_apply.setProperty("class", "success")
        btn_apply.clicked.connect(self._apply)
        btn_cancel = QPushButton(t("theme_cancel"))
        btn_cancel.setProperty("class", "ghost")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_apply)
        btns.addWidget(btn_cancel)
        vl.addLayout(btns)

        self.slider_alpha.valueChanged.connect(self._refresh)
        self.cbo_preset.currentIndexChanged.connect(self._refresh)
        self.cbo_accent.currentIndexChanged.connect(self._on_accent_changed)
        self.spin_font.valueChanged.connect(self._refresh)
        self.spin_radius.valueChanged.connect(self._refresh)

    def _load_current(self):
        preset_key = self.cfg.get("preset", "glass_dark")
        idx = self.cbo_preset.findData(preset_key)
        if idx >= 0:
            self.cbo_preset.setCurrentIndex(idx)
        accent = self.cfg.get("accent", "#6aa7ff")
        aidx = self.cbo_accent.findData(accent)
        if aidx >= 0:
            self.cbo_accent.setCurrentIndex(aidx)
        self.slider_alpha.setValue(int(self.cfg.get("glass_alpha", 7)))
        self.spin_font.setValue(int(self.cfg.get("font_size", 13)))
        self.spin_radius.setValue(int(self.cfg.get("radius", 14)))
        self._refresh()

    def _on_accent_changed(self, index):
        data = self.cbo_accent.itemData(index)
        if data == "__custom__":
            color = QColorDialog.getColor(
                QColor(self.cfg.get("accent", "#6aa7ff")), self, t("theme_color_dialog_title")
            )
            if color.isValid():
                self.cfg["accent"] = color.name()
        self._refresh()

    def _refresh(self):
        self.cfg["preset"] = self.cbo_preset.currentData()
        self.cfg["glass_alpha"] = self.slider_alpha.value()
        self.cfg["font_size"] = self.spin_font.value()
        self.cfg["radius"] = self.spin_radius.value()
        self.lbl_alpha.setText(f"{self.slider_alpha.value()}%")
        self.setStyleSheet(build_stylesheet(self.cfg))

    def _apply(self):
        data = self.cbo_accent.currentData()
        if data != "__custom__":
            self.cfg["accent"] = data
        self.cfg["preset"] = self.cbo_preset.currentData()
        self.cfg["glass_alpha"] = self.slider_alpha.value()
        self.cfg["font_size"] = self.spin_font.value()
        self.cfg["radius"] = self.spin_radius.value()
        save_config(self.cfg)
        parent = self.parent()
        if parent is not None:
            apply_theme(parent, self.cfg)
            if hasattr(parent, "_theme_cfg"):
                parent._theme_cfg = dict(self.cfg)
        tooltip(t("theme_applied_tip"))
        self.accept()
