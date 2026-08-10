"""
AnkiTool Multi-Language V16.0 — Japanese & Chinese.

Multi-language vocabulary factory for Anki note creation, templates, and audio.
"""

import json
import os
import sys
import re

from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, qconnect, tooltip

# ═══════════════════════════════════════════════════════════
#  Đảm bảo thư mục addon có trong sys.path để import
#  subpackages (Language/, mode/, audio/, utils/) hoạt động
# ═══════════════════════════════════════════════════════════
_addon_root = os.path.dirname(os.path.abspath(__file__))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

# ═══════════════════════════════════════════════════════════
#  IMPORTS FROM MODULES (Bridge)
# ═══════════════════════════════════════════════════════════
from Language import LANG_CONFIG, LANG_GRAMMAR_CONFIG, LANG_SELECTOR_INFO
from mode import LANG_TEMPLATES, LANG_CSS, LANG_GRAMMAR_TEMPLATES, LANG_GRAMMAR_CSS
from audio.engine import get_voice_options, get_selected_voice, set_selected_voice, VOICE_SAMPLE
from audio.engine import get_default_speed, set_default_speed
from utils import safe_parse_json
from utils.logger import get_logger
from utils.ai_extractor import (
    get_api_config,
    get_existing_vocab_from_deck, invalidate_deck_cache,
    extract_vocabulary_with_ai, extract_vocabulary_long_text,
    init_import_history, add_to_import_history, get_history_summary_text,
)

logger = get_logger()

# Import workers (đã tách ra workers/)
from workers import ImportWorker, PreviewThread, AiExtractThread, AiChatThread
from workers.deck_scan_worker import DeckScanWorker

# Import UI dialogs (đã tách ra ui/)
from ui import AiChatDialog, show_ai_settings_dialog, show_diff_meaning_dialog, show_ai_preview_dialog

# Import glassmorphism theme engine
from ui.theme import (
    load_config as load_theme_config,
    apply_theme, ThemeDialog, snap_maximize,
)

# Import hooks (đã tách ra hooks/)
from hooks.reviewer import register_hooks

# ═══════════════════════════════════════════════════════════
#  MAIN DIALOG
# ═══════════════════════════════════════════════════════════
class AnkiSmartFactory(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AnkiTool Multi-Lang V16.0 — Vocabulary Factory")
        # Cho phép kéo thả cửa sổ tự do (thích ứng mọi kích thước, chia đôi màn hình)
        self.setMinimumSize(640, 420)
        self.resize(1300, 900)
        # Cho phép maximize / full màn hình
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        # Cấu hình giao diện glassmorphism (đọc từ utils/ui_theme.json)
        self._theme_cfg = load_theme_config()
        # Cho phép vẽ nền gradient glassmorphism
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.raw_data = []
        self.prepared_data = []
        self._current_lang = "japanese"
        self._is_grammar = False   # False = từ vựng, True = ngữ pháp
        self.import_worker = None
        self._ai_thread = None
        # Danh sách file tài liệu tham khảo đã kẹp: [(name, text), ...]
        self._ai_attached_files = []
        # Debounce timer cho JSON parsing (tránh parse liên tục khi gõ)
        self._analyze_timer = QTimer(self)
        self._analyze_timer.setSingleShot(True)
        self._analyze_timer.setInterval(500)  # 500ms debounce
        self._analyze_timer.timeout.connect(self._analyze_content)
        self._setup_ui()
        self._on_lang_changed()

        # Khởi tạo lịch sử import (quét deck lần đầu nếu cần)
        self._init_history()

    def _init_history(self):
        """Khởi tạo lịch sử import trong background (không chặn UI)"""
        try:
            # Chạy init trong thread để không chặn UI
            history = init_import_history(force_rescan=False)
            total = sum(len(v) for v in history.get("entries", {}).values())
            if total > 0:
                self.lbl_ai_status.setText(f"📚 Lịch sử: {total} từ vựng đã có")
                self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;")
        except Exception as e:
            logger.warning("Lỗi init history: %s", e)

    def _cfg(self):
        if getattr(self, '_is_grammar', False):
            return LANG_GRAMMAR_CONFIG[self._current_lang]
        return LANG_CONFIG[self._current_lang]

    def _select_mode(self, is_grammar):
        """Chuyển chế độ Từ vựng ↔ Ngữ pháp (Note Type riêng)"""
        # Luôn đồng bộ trạng thái nút (tránh toggle lệch khi bấm lại nút đang active)
        self.btn_mode_vocab.setChecked(not is_grammar)
        self.btn_mode_grammar.setChecked(is_grammar)
        if getattr(self, '_is_grammar', False) == is_grammar:
            return
        self._is_grammar = is_grammar
        self._on_lang_changed()
        tooltip("📘 Đã chuyển sang Ngữ pháp" if is_grammar else "📖 Đã chuyển sang Từ vựng")

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 10)
        root.setSpacing(8)

        # ── TOP TOOLBAR: giao diện + chia cửa sổ ─────────
        top = QHBoxLayout()
        top.setSpacing(6)
        lbl_brand = QLabel("🧊 AnkiTool Glass")
        lbl_brand.setStyleSheet("font-size:14px;font-weight:bold;")
        top.addWidget(lbl_brand)

        btn_theme = QPushButton("🎨 Giao diện")
        btn_theme.setProperty("class", "primary")
        btn_theme.setToolTip("Tùy chỉnh giao diện glassmorphism (theme, màu nhấn, độ trong, cỡ chữ, bo góc)")
        btn_theme.clicked.connect(self._open_theme_dialog)
        top.addWidget(btn_theme)

        btn_snap_max = QPushButton("⛶ Phóng to")
        btn_snap_max.setProperty("class", "ghost")
        btn_snap_max.setToolTip("Phóng to toàn màn hình")
        btn_snap_max.clicked.connect(lambda: snap_maximize(self))
        top.addWidget(btn_snap_max)

        top.addStretch()
        lbl_tip = QLabel("💡 Kéo phân cách giữa 2 cột")
        lbl_tip.setProperty("class", "dim")
        top.addWidget(lbl_tip)
        root.addLayout(top)

        # ── MAIN SPLITTER (chia đôi, kéo thả thích ứng) ──
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── LEFT ─────────────────────────────────────────
        left_panel = QWidget()
        left = QVBoxLayout(left_panel)
        left.setContentsMargins(0, 0, 4, 0)
        left.setSpacing(6)

        # Language selector
        self.lang_grp = QGroupBox("🇯🇵 Tiếng Nhật")
        lang_layout = QHBoxLayout()

        self.btn_lang = {}
        for key, label, code in LANG_SELECTOR_INFO:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self._select_lang(k))
            self.btn_lang[key] = btn
            lang_layout.addWidget(btn)

        self.lang_grp.setLayout(lang_layout)
        left.addWidget(self.lang_grp)

        # Mode selector: Từ vựng / Ngữ pháp
        mode_grp = QGroupBox("📚 Loại Thẻ")
        mode_layout = QHBoxLayout()
        self.btn_mode_vocab = QPushButton("📖 Từ vựng")
        self.btn_mode_vocab.setCheckable(True)
        self.btn_mode_vocab.setChecked(True)
        self.btn_mode_vocab.setStyleSheet(
            "padding:10px;font-weight:bold;border-radius:10px;"
            "QPushButton:checked{background:#2ecc71;color:white;border:2px solid #27ae60;}"
            "QPushButton:!checked{background:rgba(255,255,255,0.08);color:#eaf0f6;border:1px solid rgba(255,255,255,0.18);}"
        )
        self.btn_mode_vocab.clicked.connect(lambda checked: self._select_mode(False))
        mode_layout.addWidget(self.btn_mode_vocab)
        self.btn_mode_grammar = QPushButton("📘 Ngữ pháp")
        self.btn_mode_grammar.setCheckable(True)
        self.btn_mode_grammar.setStyleSheet(
            "padding:10px;font-weight:bold;border-radius:10px;"
            "QPushButton:checked{background:#34495e;color:white;border:2px solid #2c3e50;}"
            "QPushButton:!checked{background:rgba(255,255,255,0.08);color:#eaf0f6;border:1px solid rgba(255,255,255,0.18);}"
        )
        self.btn_mode_grammar.clicked.connect(lambda checked: self._select_mode(True))
        mode_layout.addWidget(self.btn_mode_grammar)
        mode_grp.setLayout(mode_layout)
        left.addWidget(mode_grp)

        # Deck + file
        bar = QHBoxLayout()
        self.deck_chooser = QComboBox()
        self.deck_chooser.addItems(mw.col.decks.all_names())
        bar.addWidget(QLabel("📦 Deck:"), 0)
        bar.addWidget(self.deck_chooser, 1)
        btn_load = QPushButton("📁 MỞ FILE (JSON/TXT)")
        btn_load.setProperty("class", "info")
        btn_load.clicked.connect(self._load_from_file)
        bar.addWidget(btn_load, 0)
        left.addLayout(bar)

        # Sample buttons
        bar2 = QHBoxLayout()
        self.btn_sample = QPushButton("💡 Xem mẫu JSON")
        self.btn_sample.setProperty("class", "ghost")
        self.btn_sample.clicked.connect(self._show_sample_json)
        bar2.addWidget(self.btn_sample)
        bar2.addStretch()
        left.addLayout(bar2)

        # ── AI Trích Xuất Từ Vựng ──────────────────────────
        ai_grp = QGroupBox("🤖 AI Trích Xuất Từ Vựng (OpenAI / DeepSeek / Ollama)")
        ai_main = QVBoxLayout()

        # Row 1: Buttons
        ai_bar = QHBoxLayout()

        self.btn_ai_settings = QPushButton("⚙️ Cài Đặt API")
        self.btn_ai_settings.setStyleSheet(
            "padding:6px 14px;background:#8e44ad;color:white;"
            "font-weight:bold;border-radius:6px;border:none;"
        )
        self.btn_ai_settings.clicked.connect(self._show_ai_settings)
        ai_bar.addWidget(self.btn_ai_settings)

        self.btn_ai_clear_text = QPushButton("🗑 Xóa Text")
        self.btn_ai_clear_text.setStyleSheet(
            "padding:6px 10px;background:#95a5a6;color:white;"
            "font-weight:bold;border-radius:6px;border:none;"
        )
        self.btn_ai_clear_text.clicked.connect(self._ai_clear_text)
        ai_bar.addWidget(self.btn_ai_clear_text)

        self.btn_ai_extract = QPushButton("🤖 AI Trích Xuất")
        self.btn_ai_extract.setStyleSheet(
            "padding:6px 18px;background:#e67e22;color:white;"
            "font-weight:bold;border-radius:6px;border:none;font-size:13px;"
        )
        self.btn_ai_extract.clicked.connect(self._ai_extract)
        self.btn_ai_extract.setEnabled(True)
        ai_bar.addWidget(self.btn_ai_extract)

        self.btn_ai_batch = QPushButton("📋 Batch Từ Vựng")
        self.btn_ai_batch.setStyleSheet(
            "padding:6px 14px;background:#2ecc71;color:white;"
            "font-weight:bold;border-radius:6px;border:none;font-size:12px;"
        )
        self.btn_ai_batch.setToolTip(
            "Xử lý danh sách từ vựng LỚN (hàng trăm/hàng nghìn từ).\n"
            "AI sẽ làm giàu từng từ + tự động tổ chức Parent/Sub Deck theo chủ đề."
        )
        self.btn_ai_batch.clicked.connect(self._ai_batch_process)
        self.btn_ai_batch.setEnabled(True)
        ai_bar.addWidget(self.btn_ai_batch)

        self.btn_ai_chat = QPushButton("💬 Gửi")
        self.btn_ai_chat.setStyleSheet(
            "padding:6px 18px;background:#2980b9;color:white;"
            "font-weight:bold;border-radius:6px;border:none;font-size:13px;"
        )
        self.btn_ai_chat.setToolTip(
            "Gửi câu hỏi/yêu cầu đến AI. AI sẽ làm việc thông minh với hệ thống Anki,\n"
            "chỉ truy vấn những gì cần thiết, không quét toàn bộ database."
        )
        self.btn_ai_chat.clicked.connect(self._ai_chat)
        self.btn_ai_chat.setEnabled(True)
        ai_bar.addWidget(self.btn_ai_chat)

        self.btn_ai_stop = QPushButton("⏹ Dừng")
        self.btn_ai_stop.setStyleSheet(
            "padding:6px 12px;background:#e74c3c;color:white;"
            "font-weight:bold;border-radius:6px;border:none;font-size:12px;"
        )
        self.btn_ai_stop.setToolTip("Dừng yêu cầu AI đang chạy")
        self.btn_ai_stop.clicked.connect(self._cancel_ai_chat)
        self.btn_ai_stop.setVisible(False)
        ai_bar.addWidget(self.btn_ai_stop)

        self.lbl_ai_status = QLabel("")
        self.lbl_ai_status.setProperty("class", "dim")
        ai_bar.addWidget(self.lbl_ai_status, 1)

        ai_main.addLayout(ai_bar)

        # Row 1b: Đính kèm file tài liệu tham khảo cho AI
        file_bar = QHBoxLayout()
        self.btn_ai_attach = QPushButton("📎 Kẹp File")
        self.btn_ai_attach.setStyleSheet(
            "padding:5px 12px;background:#16a085;color:white;"
            "font-weight:bold;border-radius:6px;border:none;"
        )
        self.btn_ai_attach.setToolTip(
            "Đính kèm file tài liệu tham khảo (TXT/MD/DOCX/PDF/XLSX/CSV).\n"
            "AI sẽ đọc nội dung file để trích xuất từ vựng / ngữ pháp.\n"
            "Lưu ý: DeepSeek chỉ nhận TEXT → add-on tự trích text từ file tại máy."
        )
        self.btn_ai_attach.clicked.connect(self._attach_ai_files)
        file_bar.addWidget(self.btn_ai_attach)

        self.btn_ai_attach_clear = QPushButton("🧹 Bỏ File")
        self.btn_ai_attach_clear.setStyleSheet(
            "padding:5px 12px;background:#95a5a6;color:white;"
            "font-weight:bold;border-radius:6px;border:none;"
        )
        self.btn_ai_attach_clear.setToolTip("Bỏ toàn bộ file đã kẹp và xóa nội dung trong ô AI")
        self.btn_ai_attach_clear.clicked.connect(self._clear_ai_files)
        file_bar.addWidget(self.btn_ai_attach_clear)

        self.lbl_ai_files = QLabel("")
        self.lbl_ai_files.setStyleSheet("color:#27ae60;font-size:11px;")
        self.lbl_ai_files.setWordWrap(True)
        file_bar.addWidget(self.lbl_ai_files, 1)
        ai_main.addLayout(file_bar)

        # Row 2: Text input area for AI
        self.ai_text_input = QPlainTextEdit()
        self.ai_text_input.setPlaceholderText("📝 Dán văn bản vào đây (300-800 ký tự là tối ưu nhất, ~50-100 từ). Hỗ trợ tiếng Nhật & tiếng Trung.")
        self.ai_text_input.setMaximumHeight(80)
        self.ai_text_input.setStyleSheet("font-size:12px;")
        ai_main.addWidget(self.ai_text_input)

        # Row 3: Custom instruction
        instr_bar = QHBoxLayout()
        instr_bar.addWidget(QLabel("💬 Lời nhắn:"))
        self.ai_instruction = QLineEdit()
        self.ai_instruction.setPlaceholderText("VD: Chỉ lấy từ HSK3+, chủ đề ẩm thực, ưu tiên từ khó...")
        self.ai_instruction.setStyleSheet("font-size:12px;padding:4px;")
        instr_bar.addWidget(self.ai_instruction, 1)
        ai_main.addLayout(instr_bar)

        ai_grp.setLayout(ai_main)
        left.addWidget(ai_grp)

        left.addWidget(QLabel("📝 Dán dữ liệu JSON (hỗ trợ array hoặc multiple objects):"))
        self.json_input = QPlainTextEdit()
        self.json_input.textChanged.connect(self._schedule_analyze)
        left.addWidget(self.json_input)

        # Filters
        self.filter_grp = QGroupBox("⚙️ Bộ Lọc & Gác Cổng V5+")
        gl = QGridLayout()

        self.lbl_raw = QLabel("📊 Kho hàng: 0 mục")
        self.lbl_raw.setStyleSheet("color:#e67e22;font-weight:bold;")
        gl.addWidget(self.lbl_raw, 0, 0, 1, 2)

        self.lbl_level = QLabel("🎓 Cấp độ:")
        self.cbo_level = QComboBox()
        gl.addWidget(self.lbl_level, 1, 0)
        gl.addWidget(self.cbo_level, 1, 1)

        self.txt_topic = QLineEdit()
        self.txt_topic.setPlaceholderText("Lọc theo topic...")
        gl.addWidget(QLabel("🔍 Topic:"), 2, 0)
        gl.addWidget(self.txt_topic, 2, 1)

        audio_box = QHBoxLayout()
        self.chk_audio_vocab = QCheckBox("🎵 Vocab")
        self.chk_audio_vocab.setChecked(True)
        self.chk_audio_ex1 = QCheckBox("🎵 Ví dụ 1")
        self.chk_audio_ex1.setChecked(True)
        self.chk_audio_ex2 = QCheckBox("🎵 Ví dụ 2")
        self.chk_audio_ex2.setChecked(True)
        for c in (self.chk_audio_vocab, self.chk_audio_ex1, self.chk_audio_ex2):
            audio_box.addWidget(c)
        gl.addWidget(QLabel("🔊 Auto Audio:"), 3, 0)
        gl.addLayout(audio_box, 3, 1)

        btn_verify = QPushButton("🌪️ Kiểm Định")
        btn_verify.setProperty("class", "warning")
        btn_verify.setMinimumHeight(42)
        btn_verify.setToolTip("Kiểm định lô hàng — kiểm tra trùng lặp, cập nhật, từ mới")
        btn_verify.clicked.connect(self._verify_batch)

        btn_rebuild = QPushButton("🔨 Tái Tạo Model")
        btn_rebuild.setProperty("class", "purple")
        btn_rebuild.setMinimumHeight(42)
        btn_rebuild.setToolTip("Tái tạo / cập nhật Model Note (template, CSS, fields)")
        btn_rebuild.clicked.connect(self._force_rebuild_model)

        self.btn_diff_meaning = QPushButton("🔍 Nghĩa Khác")
        self.btn_diff_meaning.setProperty("class", "warning")
        self.btn_diff_meaning.setMinimumHeight(42)
        self.btn_diff_meaning.setEnabled(False)
        self.btn_diff_meaning.setToolTip("Xem các từ vựng có cùng mặt chữ nhưng khác nghĩa để xác nhận thêm")
        self.btn_diff_meaning.clicked.connect(self._show_diff_meaning_report)

        # Hàng ngang 3 nút
        action_bar = QHBoxLayout()
        action_bar.addWidget(btn_verify, 1)
        action_bar.addWidget(btn_rebuild, 1)
        action_bar.addWidget(self.btn_diff_meaning, 1)
        gl.addLayout(action_bar, 4, 0, 1, 2)

        # ── Voice Selection ───────────────────────────────
        voice_grp = QGroupBox("🎤 Chọn Giọng Đọc & Tốc Độ")
        vgl = QHBoxLayout()
        vgl.addWidget(QLabel("Giọng:"), 0)
        self.cbo_voice = QComboBox()
        self.cbo_voice.setMinimumWidth(150)
        self.cbo_voice.currentIndexChanged.connect(self._on_voice_changed)
        vgl.addWidget(self.cbo_voice, 1)
        self.btn_preview_voice = QPushButton("▶ Nghe thử")
        self.btn_preview_voice.setProperty("class", "purple")
        self.btn_preview_voice.clicked.connect(self._preview_voice)
        vgl.addWidget(self.btn_preview_voice, 0)
        vgl.addSpacing(12)
        vgl.addWidget(QLabel("⏩ Tốc độ:"), 0)
        self.spin_speed = QDoubleSpinBox()
        self.spin_speed.setRange(0.25, 4.0)
        self.spin_speed.setSingleStep(0.05)
        self.spin_speed.setDecimals(2)
        self.spin_speed.setSuffix(" ×")
        self.spin_speed.setValue(1.0)
        self.spin_speed.setMinimumWidth(70)
        self.spin_speed.setToolTip("Tốc độ phát audio mặc định cho thẻ học\n(0.25× = chậm nhất, 4.0× = nhanh nhất)")
        self.spin_speed.valueChanged.connect(self._on_speed_changed)
        vgl.addWidget(self.spin_speed, 0)
        voice_grp.setLayout(vgl)
        left.addWidget(voice_grp)

        self.main_splitter.addWidget(left_panel)

        # ── RIGHT ────────────────────────────────────────
        right_panel = QWidget()
        right = QVBoxLayout(right_panel)
        right.setContentsMargins(4, 0, 0, 0)
        right.setSpacing(6)

        # Bộ Lọc & Gác Cổng V5+ (chuyển sang cột phải)
        self.filter_grp.setLayout(gl)
        right.addWidget(self.filter_grp)

        right.addWidget(QLabel("📋 Thẻ chờ xuất xưởng (✨ New | 🔄 Update | ⚠️ Trùng mờ):"))

        self.preview_list = QListWidget()
        self.preview_list.setMinimumHeight(120)  # thích ứng theo kích thước kéo thả
        right.addWidget(self.preview_list)

        rng = QHBoxLayout()
        self.spin_start = QSpinBox()
        self.spin_start.setRange(1, 9999)
        self.spin_end = QSpinBox()
        self.spin_end.setRange(1, 9999)
        rng.addWidget(QLabel("🔢 Từ:"))
        rng.addWidget(self.spin_start)
        rng.addWidget(QLabel("đến:"))
        rng.addWidget(self.spin_end)
        right.addLayout(rng)

        self.lbl_ready = QLabel("✅ Sẵn sàng: 0 thẻ")
        self.lbl_ready.setStyleSheet("color:#27ae60;font-weight:bold;")
        right.addWidget(self.lbl_ready)

        self.pbar = QProgressBar()
        self.pbar.setVisible(False)
        right.addWidget(self.pbar)

        self.lbl_status = QLabel("")
        self.lbl_status.setProperty("class", "dim")
        right.addWidget(self.lbl_status)

        self.btn_import = QPushButton("🚀 XUẤT XƯỞNG (IMPORT)")
        self.btn_import.setProperty("class", "success")
        self.btn_import.setMinimumHeight(52)
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self._process_import)
        right.addWidget(self.btn_import)

        self.btn_cancel = QPushButton("⏹️ DỪNG LẠI")
        self.btn_cancel.setProperty("class", "danger")
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._cancel_import)
        right.addWidget(self.btn_cancel)

        self.main_splitter.addWidget(right_panel)
        self.main_splitter.setStretchFactor(0, 5)
        self.main_splitter.setStretchFactor(1, 5)
        self.main_splitter.setSizes([660, 640])
        # Cho phép kéo thanh phân cách tự do (2 cột co/giãn thích ứng)
        self.main_splitter.setChildrenCollapsible(True)
        self.main_splitter.setHandleWidth(8)
        root.addWidget(self.main_splitter, 1)

        # Áp theme glassmorphism
        self._theme_cfg = apply_theme(self, self._theme_cfg)

    def _open_theme_dialog(self):
        """Mở hộp thoại tùy chỉnh giao diện glassmorphism"""
        dlg = ThemeDialog(self)
        dlg.exec()

    def _apply_lang_button_styles(self):
        """Áp dụng style chuẩn quốc kỳ cho nút ngôn ngữ"""
        default_style = """
        QPushButton {
            padding: 12px 20px;
            font-weight: bold;
            font-size: 14px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.18);
            background: rgba(255,255,255,0.08);
            color: #eaf0f6;
        }
        QPushButton:hover {
            background: rgba(255,255,255,0.15);
        }
        """

        selected_styles = {
            "japanese": """
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ffffff, stop:1 #f5f5f5);
                    color: #bc002d;
                    border: 2px solid #bc002d;
                    font-size: 15px;
                }
            """,
            "chinese": """
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #fff5f5, stop:1 #fef0e0);
                    color: #de2910;
                    border: 2px solid #de2910;
                    font-size: 15px;
                }
            """
        }

        for key, btn in self.btn_lang.items():
            style = default_style + selected_styles.get(key, "")
            btn.setStyleSheet(style)

    def _select_lang(self, lang_key):
        self._current_lang = lang_key
        self._on_lang_changed()

    def _on_lang_changed(self):
        cfg = self._cfg()
        for k, btn in self.btn_lang.items():
            btn.setChecked(k == self._current_lang)

        self._apply_lang_button_styles()

        # Cập nhật tiêu đề group box ngôn ngữ
        self.lang_grp.setTitle(cfg["label"])
        if self._is_grammar:
            self.setWindowTitle(f"AnkiTool Multi-Lang V16.0 — {cfg['label']} (Ngữ pháp)")
        else:
            self.setWindowTitle(f"AnkiTool Multi-Lang V16.0 — {cfg['label']}")

        self.lbl_level.setText(cfg["level_label"])
        self.cbo_level.clear()
        self.cbo_level.addItems(cfg["level_choices"])

        tooltip_text = "🎤 Sử dụng Edge TTS Online (cần internet, fallback gTTS)"
        self.chk_audio_vocab.setToolTip(tooltip_text)
        self.chk_audio_ex1.setToolTip(tooltip_text)
        self.chk_audio_ex2.setToolTip(tooltip_text)

        self.raw_data = []
        self.prepared_data = []
        self.preview_list.clear()
        self.lbl_raw.setText("📊 Kho hàng: 0 mục")
        self.lbl_ready.setText("✅ Sẵn sàng: 0 thẻ")
        self.btn_import.setEnabled(False)
        self.json_input.clear()
        self.btn_diff_meaning.setEnabled(False)

        # Bỏ file tham khảo cũ khi đổi ngôn ngữ / chế độ
        self._ai_attached_files = []
        if hasattr(self, 'lbl_ai_files'):
            self.lbl_ai_files.setText("")

        # Cập nhật placeholder theo chế độ
        if self._is_grammar:
            self.ai_text_input.setPlaceholderText(
                "📝 Dán văn bản để trích xuất NGỮ PHÁP (cấu trúc, cách dùng, công thức, ví dụ)..."
            )
        else:
            self.ai_text_input.setPlaceholderText(
                "📝 Dán văn bản vào đây (300-800 ký tự là tối ưu nhất, ~50-100 từ). Hỗ trợ tiếng Nhật & tiếng Trung."
            )

        # Sync voice dropdown với ngôn ngữ hiện tại
        lang = cfg["lang_code"]
        voices = get_voice_options(lang)
        self.cbo_voice.blockSignals(True)
        self.cbo_voice.clear()
        sel_id = get_selected_voice(lang)
        for i, v in enumerate(voices):
            icon = "👩" if v["gender"] == "female" else "👨"
            self.cbo_voice.addItem(f"{icon} {v['name']}")
            if v["id"] == sel_id:
                self.cbo_voice.setCurrentIndex(i)
        self.cbo_voice.blockSignals(False)

        # Sync speed spinner với ngôn ngữ hiện tại
        self.spin_speed.blockSignals(True)
        self.spin_speed.setValue(get_default_speed(lang))
        self.spin_speed.blockSignals(False)

        self.get_or_create_model()

    def _on_voice_changed(self, index):
        lang = self._cfg()["lang_code"]
        voices = get_voice_options(lang)
        if 0 <= index < len(voices):
            set_selected_voice(lang, voices[index]["id"])

    def _on_speed_changed(self, value):
        lang = self._cfg()["lang_code"]
        set_default_speed(lang, round(value, 2))

    def _preview_voice(self):
        lang = self._cfg()["lang_code"]
        voices = get_voice_options(lang)
        idx = self.cbo_voice.currentIndex()
        if not voices or idx < 0 or idx >= len(voices):
            return
        voice_id = voices[idx]["id"]
        sample = VOICE_SAMPLE.get(lang, "Hello!")

        self.btn_preview_voice.setEnabled(False)
        self.btn_preview_voice.setText("⏳")

        speed = self.spin_speed.value()
        self._preview_thread = PreviewThread(sample, voice_id, lang, speed=speed)
        self._preview_thread.done.connect(self._on_preview_done)
        self._preview_thread.start()

    def _on_preview_done(self, filepath):
        self.btn_preview_voice.setEnabled(True)
        self.btn_preview_voice.setText("▶ Nghe thử")
        if filepath and os.path.exists(filepath):
            try:
                from aqt.sound import av_player
                from anki.sound import SoundOrVideoTag
                av_player.play_tags([SoundOrVideoTag(filename=os.path.basename(filepath))])
            except Exception:
                try:
                    import subprocess
                    subprocess.Popen([filepath], shell=True)
                except Exception:
                    tooltip("Không thể phát audio preview.")
        else:
            tooltip("⚠️ Không thể tạo audio. Kiểm tra kết nối internet và edge-tts.")

    def _show_sample_json(self):
        samples = {
            "japanese": '''{
  "front": "食べる",
  "furigana": "たべる",
  "meaning": "ăn",
  "sino-vietnamese": "",
  "jlptlevel": "N5",
  "topic": "Động từ",
  "example": "毎日ご飯を食べる。",
  "example_vn": "Hàng ngày tôi ăn cơm.",
  "example_2": "友達と一緒に食べました。",
  "example_2_vn": "Tôi đã ăn cùng bạn bè."
}''',
            "chinese": '''{
  "simplified": "学习",
  "traditional": "學習",
  "pinyin": "xuéxí",
  "meaning": "học tập",
  "sino_vietnamese": "học tập",
  "hsk_level": "HSK1",
  "topic": "Động từ",
  "example": "我每天学习中文。",
  "example_pinyin": "Wǒ měitiān xuéxí zhōngwén.",
  "example_vn": "Mỗi ngày tôi học tiếng Trung.",
  "example_2": "他在图书馆学习。",
  "example_2_pinyin": "Tā zài túshūguǎn xuéxí.",
  "example_2_vn": "Anh ấy học ở thư viện."
}'''
        }

        # Mẫu JSON ngữ pháp khi đang ở chế độ Ngữ pháp
        grammar_samples = {
            "japanese": '''{
  "pattern": "〜てもいい",
  "reading": "てもいい",
  "meaning": "được phép làm gì đó",
  "jlptlevel": "N5",
  "topic": "Cho phép / Xin phép",
  "usage": "Vて + もいいです",
  "explanation": "Dùng để xin phép hoặc cho phép. Thân mật: 〜てもいいよ",
  "example": "ここで写真を撮ってもいいですか。",
  "example_vn": "Tôi chụp ảnh ở đây được không?",
  "example_2": "明日は休んでもいいよ。",
  "example_2_vn": "Mai nghỉ cũng được nhé."
}''',
            "chinese": '''{
  "pattern": "把 + N + V",
  "pinyin": "bǎ + N + V",
  "meaning": "đem/ làm gì đó với ... (nhấn mạnh kết quả)",
  "hsk_level": "HSK3",
  "topic": "Cấu trúc câu",
  "usage": "Chủ ngữ + 把 + 宾语 + V + Kết quả",
  "explanation": "Dùng khi nhấn mạnh kết quả của việc tác động lên vật.",
  "example": "我把作业做完了。",
  "example_pinyin": "Wǒ bǎ zuòyè zuò wán le.",
  "example_vn": "Tôi đã làm xong bài tập.",
  "example_2": "请把门关上。",
  "example_2_pinyin": "Qǐng bǎ mén guān shàng.",
  "example_2_vn": "Làm ơn đóng cửa lại."
}'''
        }

        raw = samples[self._current_lang]
        if self._is_grammar:
            raw = grammar_samples[self._current_lang]

        if isinstance(raw, dict):
            # Multiple sub-samples: show a combo to choose
            sub_keys = list(raw.keys())
            dlg = QDialog(self)
            dlg.setWindowTitle(f"💡 Mẫu JSON — {self._cfg()['label']}")
            dlg.setMinimumWidth(600)
            vl = QVBoxLayout(dlg)

            top_bar = QHBoxLayout()
            top_bar.addWidget(QLabel("Chọn loại:"))
            cbo = QComboBox()
            cbo.addItems(sub_keys)
            top_bar.addWidget(cbo, 1)
            vl.addLayout(top_bar)

            te = QPlainTextEdit()
            te.setReadOnly(True)
            te.setPlainText(raw[sub_keys[0]])
            te.setStyleSheet("font-family:monospace;font-size:13px;")
            vl.addWidget(te)

            def on_sub_changed(idx):
                te.setPlainText(raw[cbo.currentText()])

            cbo.currentIndexChanged.connect(on_sub_changed)

            btn_copy = QPushButton("📋 Copy & Đóng")
            btn_copy.clicked.connect(lambda: (
                QApplication.clipboard().setText(te.toPlainText()),
                dlg.accept()
            ))
            vl.addWidget(btn_copy)
            dlg.exec()
        else:
            dlg = QDialog(self)
            dlg.setWindowTitle(f"💡 Mẫu JSON — {self._cfg()['label']}")
            dlg.setMinimumWidth(600)
            vl = QVBoxLayout(dlg)
            te = QPlainTextEdit()
            te.setReadOnly(True)
            te.setPlainText(raw)
            te.setStyleSheet("font-family:monospace;font-size:13px;")
            vl.addWidget(te)

            btn_copy = QPushButton("📋 Copy & Đóng")
            btn_copy.clicked.connect(lambda: (
                QApplication.clipboard().setText(te.toPlainText()),
                dlg.accept()
            ))
            vl.addWidget(btn_copy)
            dlg.exec()

    def _load_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file dữ liệu", "", "Dữ liệu (*.json *.txt)"
        )
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.json_input.setPlainText(f.read())
            except Exception as e:
                showInfo(f"Lỗi đọc file: {e}")

    def _schedule_analyze(self):
        """Debounced analyze — chỉ parse JSON khi user ngừng gõ 500ms."""
        self._analyze_timer.start()

    def _analyze_content(self):
        raw = self.json_input.toPlainText().strip()
        if not raw:
            self.raw_data = []
        else:
            self.raw_data = safe_parse_json(raw)

        self.lbl_raw.setText(f"📊 Kho hàng: {len(self.raw_data)} mục")

    def _verify_batch(self):
        try:
            self._verify_batch_impl()
        except Exception as e:
            import traceback
            showInfo(f"❌ Lỗi Kiểm Định:\n\n{str(e)}\n\n{traceback.format_exc()}")

    def _get_model_id(self):
        """Lấy model ID (mid) của model hiện tại — an toàn hơn note: trong find_notes"""
        cfg = self._cfg()
        m = mw.col.models.by_name(cfg["model_name"])
        if m:
            return m["id"]
        return None

    def _verify_batch_impl(self):
        cfg = self._cfg()
        self.preview_list.clear()
        self.prepared_data = []

        mid = self._get_model_id()
        mid_filter = f'"mid:{mid}"' if mid else ""

        target_level = self.cbo_level.currentText()
        target_topic = self.txt_topic.text().strip().lower()
        cnt = {"dup": 0, "update": 0, "new": 0, "partial": 0, "dup_diff": 0}
        front_field = cfg["front_field"]
        level_field = cfg["level_field"]
        jfm = cfg["json_field_map"]

        def get_front(item):
            dk = cfg["detect_key"]
            return str(item.get(dk, item.get('front', ''))).strip()

        def get_level(item):
            for k, fn in jfm.items():
                if fn == level_field and k in item:
                    return str(item[k]).strip()
            return ''

        for item in self.raw_data:
            if not isinstance(item, dict):
                continue

            front = get_front(item)
            level = get_level(item)
            topic = str(item.get('topic', '')).strip().lower()
            meaning = str(item.get('meaning', '')).strip()

            if not front:
                continue
            if target_level != "Tất cả" and target_level not in level:
                continue
            if target_topic and target_topic not in topic:
                continue

            action, target_nid, updatable = "add", None, []
            conflict_info = None

            exact_ids = mw.col.find_notes(f'{mid_filter} "{front_field}:{self._esc(front)}"')
            if exact_ids:
                old = mw.col.get_note(exact_ids[0])
                updatable = self._find_updatable_fields(old, item)
                if updatable:
                    action, target_nid = "update", exact_ids[0]
                    cnt["update"] += 1
                else:
                    # Kiểm tra xem nghĩa có khác không
                    try:
                        existing_meaning = old["Meaning"].strip()
                    except Exception:
                        existing_meaning = ""
                    existing_meaning_lower = existing_meaning.lower()
                    new_meaning_lower = meaning.lower()

                    if existing_meaning_lower and new_meaning_lower and existing_meaning_lower != new_meaning_lower:
                        # Cùng mặt chữ nhưng khác nghĩa → đưa vào diện "dup_diff" để người dùng xác nhận
                        action = "dup_diff"
                        cnt["dup_diff"] += 1
                        try:
                            _efuri = str(old[cfg["furi_label"]]).strip()
                        except Exception:
                            _efuri = ""
                        try:
                            _elevel = str(old[level_field]).strip()
                        except Exception:
                            _elevel = ""
                        conflict_info = {
                            "existing_front": str(old[front_field]).strip() if front_field in old else front,
                            "existing_meaning": existing_meaning,
                            "existing_furigana": _efuri,
                            "existing_level": _elevel,
                            "existing_nid": exact_ids[0],
                        }
                    else:
                        cnt["dup"] += 1
                        continue
                self._add_to_queue(item, action, target_nid, updatable, cnt, conflict_info)
                continue

            if level:
                same_mean = mw.col.find_notes(
                    f'{mid_filter} Meaning:"{self._esc(meaning)}" "{level_field}:{level}"'
                )
                if same_mean:
                    action = "add_partial"
                    cnt["partial"] += 1

            if action in ("add", "add_partial"):
                cnt["new"] += 1
            self._add_to_queue(item, action, target_nid, updatable, cnt, conflict_info)

        self.spin_start.setValue(1)
        self.spin_end.setValue(len(self.prepared_data))
        self.btn_import.setEnabled(len(self.prepared_data) > 0)
        self.btn_diff_meaning.setEnabled(cnt["dup_diff"] > 0)
        self.lbl_ready.setText(
            f"✨ {cnt['new']} mới   🔄 {cnt['update']} cập nhật   "
            f"⚠️ {cnt['partial']} trùng mờ   🔍 {cnt['dup_diff']} nghĩa khác   ❌ {cnt['dup']} bỏ qua"
        )

    def _add_to_queue(self, item, action, nid, updatable, cnt, conflict_info=None):
        self.prepared_data.append({
            "item": item, "action": action,
            "nid": nid, "update_fields": updatable,
            "conflict_info": conflict_info,
        })
        idx = len(self.prepared_data)
        icon = {"add": "✨", "add_partial": "⚠️", "update": "🔄", "dup_diff": "🔍"}.get(action, "✨")
        cfg = self._cfg()
        dk = cfg["detect_key"]
        front = str(item.get(dk, item.get('front', ''))).strip()
        if action == "dup_diff" and conflict_info:
            suffix = f"  [🔍 Nghĩa khác: mới='{item.get('meaning','')}' ← cũ='{conflict_info['existing_meaning']}']"
        elif action == "update" and updatable:
            suffix = f"  [Cập nhật: {', '.join(updatable)}]"
        elif action == "add_partial":
            suffix = "  [Trùng mờ — vẫn thêm]"
        else:
            suffix = ""
        self.preview_list.addItem(
            f"{icon} {idx}: {front} — {item.get('meaning','')}{suffix}"
        )

    def _show_diff_meaning_report(self):
        """Hiển thị dialog báo cáo các từ vựng có cùng mặt chữ nhưng khác nghĩa,
        cho phép người dùng chọn từ nào được phép thêm vào."""
        cfg = self._cfg()
        changed = show_diff_meaning_dialog(self, self.prepared_data, cfg)
        if not changed:
            return

        # Cập nhật lại preview_list sau khi module xử lý
        dk = cfg["detect_key"]
        self.preview_list.clear()
        for i, d in enumerate(self.prepared_data):
            item = d["item"]
            action = d["action"]
            updatable = d.get("update_fields", [])
            ci = d.get("conflict_info")
            front = str(item.get(dk, item.get('front', ''))).strip()
            icon = {"add": "✨", "add_partial": "⚠️", "update": "🔄", "dup_diff": "🔍"}.get(action, "✨")

            if action == "dup_diff" and ci:
                suffix = f"  [🔍 Nghĩa khác: mới='{item.get('meaning','')}' ← cũ='{ci['existing_meaning']}']"
            elif action == "update" and updatable:
                suffix = f"  [Cập nhật: {', '.join(updatable)}]"
            elif action == "add_partial":
                suffix = "  [Trùng mờ — vẫn thêm]"
            else:
                suffix = ""

            self.preview_list.addItem(
                f"{icon} {i+1}: {front} — {item.get('meaning','')}{suffix}"
            )

        # Cập nhật label và nút
        self.spin_start.setValue(1)
        self.spin_end.setValue(len(self.prepared_data))
        self.btn_import.setEnabled(len(self.prepared_data) > 0)

        # Đếm lại
        remaining_dup_diff = sum(1 for d in self.prepared_data if d["action"] == "dup_diff")
        self.btn_diff_meaning.setEnabled(remaining_dup_diff > 0)

    def _find_updatable_fields(self, note, item):
        cfg = self._cfg()
        updatable = []
        for jk, fn in cfg["json_field_map"].items():
            if fn not in cfg["all_fields"]:
                continue
            try:
                cur = note[fn].strip()
            except Exception:
                continue
            new_val = str(item.get(jk, '')).strip()
            if not cur and new_val:
                updatable.append(fn)

        for audio_fn, src_fn in cfg["audio_fields"]:
            try:
                if not note[audio_fn].strip() and note[src_fn].strip():
                    updatable.append(audio_fn)
            except Exception:
                pass

        return list(dict.fromkeys(updatable))

    @staticmethod
    def _esc(s):
        return s.replace('\\', '\\\\').replace('"', '\\"')

    def _process_import(self):
        if not self.prepared_data:
            return

        batch = self.prepared_data[self.spin_start.value()-1 : self.spin_end.value()]
        if not batch:
            return

        mw.checkpoint("Anki V16 Import")
        cfg = self._cfg()
        deck_id = mw.col.decks.id(self.deck_chooser.currentText())

        audio_options = (
            self.chk_audio_vocab.isChecked(),
            self.chk_audio_ex1.isChecked(),
            self.chk_audio_ex2.isChecked()
        )

        self.btn_import.setEnabled(False)
        self.btn_cancel.setVisible(True)
        self.pbar.setMaximum(len(batch))
        self.pbar.setValue(0)
        self.pbar.setVisible(True)

        speed = self.spin_speed.value()
        self.import_worker = ImportWorker(batch, cfg, deck_id, audio_options, speed=speed)
        self.import_worker.progress.connect(self._on_import_progress)
        self.import_worker.finished.connect(self._on_import_finished)
        self.import_worker.error.connect(self._on_import_error)
        self.import_worker.start()

    def _on_import_progress(self, current, status_text):
        self.pbar.setValue(current)
        self.lbl_status.setText(status_text)
        mw.app.processEvents()

    def _on_import_finished(self, report):
        mw.reset()
        self.pbar.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_import.setEnabled(True)
        self.lbl_status.setText("✅ Hoàn tất!")

        # Ghi nhận vào lịch sử import
        if report.get('added', 0) > 0:
            try:
                deck_name = self.deck_chooser.currentText()
                # Lấy các mục đã import từ prepared_data
                batch = self.prepared_data[self.spin_start.value()-1 : self.spin_end.value()]
                imported_items = [d["item"] for d in batch if d["action"] in ("add", "add_partial")]
                if imported_items:
                    add_to_import_history(
                        imported_items,
                        self._current_lang,
                        deck_name=deck_name,
                        source="manual",
                    )
                invalidate_deck_cache()
            except Exception as e:
                logger.warning("Lỗi ghi lịch sử import: %s", e)

        msg = (
            f"🚀 XUẤT XƯỞNG V16.0 THÀNH CÔNG! [{self._cfg()['label']}]\n"
            f"──────────────────────────────\n"
            f"✨ Thêm mới   : {report['added']} thẻ\n"
            f"🔄 Cập nhật  : {report['updated']} thẻ\n"
            f"🎵 Audio gen  : {report['audio_gen']} file\n"
        )
        if report.get('errors', 0) > 0:
            msg += f"\n⚠️ Lỗi: {report['errors']} thẻ\n"
            if 'errors_detail' in report:
                msg += "\n".join(report['errors_detail'])

        showInfo(msg)
        self.import_worker = None

    def _on_import_error(self, error_msg):
        showInfo(f"Lỗi import: {error_msg}")
        self.btn_import.setEnabled(True)
        self.btn_cancel.setVisible(False)
        self.pbar.setVisible(False)

    def _cancel_import(self):
        if self.import_worker and self.import_worker.isRunning():
            self.import_worker.stop()
            self.lbl_status.setText("⏸️ Đang dừng...")
            self.btn_cancel.setEnabled(False)

    def _force_rebuild_model(self):
        cfg = self._cfg()
        mm = mw.col.models
        m = self._get_or_migrate_model(mm, cfg)
        if m:
            if self._is_grammar:
                m['css'] = LANG_GRAMMAR_CSS[self._current_lang]()
                tmpls = LANG_GRAMMAR_TEMPLATES[self._current_lang]
            else:
                m['css'] = LANG_CSS[self._current_lang]()
                tmpls = LANG_TEMPLATES[self._current_lang]
            tmpl_count = len(tmpls) // 2
            for i in range(tmpl_count):
                if i < len(m['tmpls']):
                    m['tmpls'][i]['qfmt'] = tmpls[i * 2]()
                    m['tmpls'][i]['afmt'] = tmpls[i * 2 + 1]()
                else:
                    t = mm.new_template(cfg["template_names"][i])
                    t['qfmt'] = tmpls[i * 2]()
                    t['afmt'] = tmpls[i * 2 + 1]()
                    mm.add_template(m, t)
            # Remove extra templates if model has more than needed
            while len(m['tmpls']) > tmpl_count:
                mm.remove_template(m, m['tmpls'][-1])
            mm.save(m)
            showInfo(f"✅ Đã tái tạo model: {cfg['model_name']}")
        else:
            self.get_or_create_model()
            showInfo(f"✅ Đã tạo model mới: {cfg['model_name']}")

    def _get_or_migrate_model(self, mm, cfg):
        name = cfg["model_name"]
        m = mm.by_name(name)
        if m:
            return m

        for old_name in cfg.get("old_model_names", []):
            m = mm.by_name(old_name)
            if m:
                m["name"] = name
                mm.save(m)
                return m

        return None

    def get_or_create_model(self):
        cfg   = self._cfg()
        mm    = mw.col.models
        name  = cfg["model_name"]
        m     = self._get_or_migrate_model(mm, cfg)
        if self._is_grammar:
            tmpls = LANG_GRAMMAR_TEMPLATES[self._current_lang]
            css   = LANG_GRAMMAR_CSS[self._current_lang]()
        else:
            tmpls = LANG_TEMPLATES[self._current_lang]
            css   = LANG_CSS[self._current_lang]()
        tmpl_count = len(tmpls) // 2

        if m:
            existing = {f['name'] for f in m['flds']}
            for fn in cfg["all_fields"]:
                if fn not in existing:
                    mm.add_field(m, mm.new_field(fn))
            m['css'] = css
            for i in range(tmpl_count):
                if i < len(m['tmpls']):
                    m['tmpls'][i]['qfmt'] = tmpls[i * 2]()
                    m['tmpls'][i]['afmt'] = tmpls[i * 2 + 1]()
                else:
                    t = mm.new_template(cfg["template_names"][i])
                    t['qfmt'] = tmpls[i * 2]()
                    t['afmt'] = tmpls[i * 2 + 1]()
                    mm.add_template(m, t)
            # Remove extra templates if model has more than needed
            while len(m['tmpls']) > tmpl_count:
                mm.remove_template(m, m['tmpls'][-1])
            mm.save(m)
            return m

        m = mm.new(name)
        for fn in cfg["all_fields"]:
            mm.add_field(m, mm.new_field(fn))
        for i in range(tmpl_count):
            t = mm.new_template(cfg["template_names"][i])
            t['qfmt'] = tmpls[i * 2]()
            t['afmt'] = tmpls[i * 2 + 1]()
            mm.add_template(m, t)
        m['css'] = css
        mm.add(m)
        return m

    # ═══════════════════════════════════════════════════════
    #  AI SETTINGS DIALOG (wired → ui/ai_settings.py)
    # ═══════════════════════════════════════════════════════
    def _show_ai_settings(self):
        """Mở dialog cấu hình API Key & endpoint cho AI"""
        show_ai_settings_dialog(self)

    # ═══════════════════════════════════════════════════════
    #  AI TEXT INPUT & EXTRACT (quét deck → AI → tránh trùng)
    # ═══════════════════════════════════════════════════════
    @staticmethod
    def _warn_reasoner_model():
        """Cảnh báo nếu đang dùng model reasoning (chậm, dễ timeout)"""
        cfg_api = get_api_config()
        model = cfg_api.get("model", "")
        if "reasoner" in model.lower():
            tooltip(
                f"⚠️ Bạn đang dùng model '{model}'.\n"
                f"Model này suy nghĩ rất kỹ trước khi trả lời,\n"
                f"có thể mất 3-10 phút. Hãy kiên nhẫn chờ đợi.\n\n"
                f"💡 Mẹo: Chuyển sang 'deepseek-chat' để nhanh hơn."
            )

    def _ai_clear_text(self):
        """Xóa text input và reset trạng thái"""
        self.ai_text_input.clear()
        self.lbl_ai_status.setText("")
        self.lbl_ai_status.setStyleSheet("color:rgba(234,240,246,0.7);font-size:11px;font-weight:normal;")

    def _attach_ai_files(self):
        """📎 Đính kèm file tài liệu tham khảo → AI đọc text để trích xuất.

        DeepSeek/OpenAI chat chỉ nhận TEXT → add-on tự trích text từ file tại máy
        (txt/md/csv/pdf/docx/doc/xlsx/xls) rồi đưa vào ô AI làm tham khảo.
        """
        paths, _ = QFileDialog.getOpenFileNames(
            self, "📎 Chọn file tài liệu tham khảo",
            "",
            "Tài liệu (*.txt *.md *.csv *.docx *.doc *.pdf *.xlsx *.xls);;Tất cả (*)",
        )
        if not paths:
            return

        from utils.ai_extractor import extract_text_from_file
        self.lbl_ai_status.setText("📖 Đang đọc nội dung file... (lần đầu có thể tự cài thư viện đọc file)")
        mw.app.processEvents()

        new_files = []
        combined_parts = []
        errors = []
        for p in paths:
            name = os.path.basename(p)
            try:
                text = extract_text_from_file(p)
            except Exception as e:
                errors.append(f"• {name}: {e}")
                continue
            if not text.strip():
                errors.append(f"• {name}: không đọc được nội dung")
                continue
            new_files.append((name, text))
            combined_parts.append(f"===== 📄 FILE: {name} =====\n{text}")

        if not new_files:
            self.lbl_ai_status.setText("")
            showInfo("⚠️ Không đọc được nội dung file nào.\n\n" + "\n".join(errors))
            return

        self._ai_attached_files.extend(new_files)

        # Đưa nội dung file vào ô AI để làm tài liệu tham khảo
        combined = "\n\n".join(combined_parts)
        current = self.ai_text_input.toPlainText()
        if current.strip():
            self.ai_text_input.setPlainText(current.rstrip() + "\n\n" + combined)
        else:
            self.ai_text_input.setPlainText(combined)

        self._update_ai_files_label()
        self.lbl_ai_status.setText("")

        if errors:
            tooltip(f"📎 Đã kẹp {len(new_files)} file.\n⚠️ Không đọc được:\n" + "\n".join(errors))
        else:
            tooltip(f"✅ Đã kẹp {len(new_files)} file làm tài liệu tham khảo!")

    def _clear_ai_files(self):
        """🧹 Bỏ toàn bộ file đã kẹp và xóa nội dung ô AI."""
        self._ai_attached_files = []
        self.ai_text_input.clear()
        self.lbl_ai_files.setText("")
        tooltip("🧹 Đã bỏ toàn bộ file đính kèm.")

    def _update_ai_files_label(self):
        names = ", ".join(n for n, _ in self._ai_attached_files)
        total_chars = sum(len(t) for _, t in self._ai_attached_files)
        self.lbl_ai_files.setText(f"📎 {len(self._ai_attached_files)} file ({total_chars:,} ký tự): {names}")

    def _get_existing_words_for_ai(self):
        """Lấy danh sách từ hiện có trong deck (có cache 30 phút)"""
        cfg = self._cfg()
        deck_name = self.deck_chooser.currentText()
        if not deck_name:
            return []
        try:
            deck_id = mw.col.decks.id(deck_name)
            words = get_existing_vocab_from_deck(
                cfg["model_name"], deck_id, cfg["front_field"]
            )
            return words
        except Exception as e:
            logger.warning("Lỗi lấy deck vocab: %s", e)
            return []

    def _ai_extract(self):
        """Quét deck → gọi AI với context tránh trùng → preview"""
        text = self.ai_text_input.toPlainText().strip()
        if not text:
            tooltip("⚠️ Vui lòng dán văn bản vào ô trên trước.")
            return

        cfg_api = get_api_config()
        if not cfg_api.get("api_key") and "localhost" not in cfg_api.get("api_base", ""):
            reply = QMessageBox.question(
                self, "⚠️ Chưa có API Key",
                "Bạn chưa cấu hình API Key.\n\n"
                "Nếu dùng DeepSeek/OpenAI/OpenRouter: cần API Key.\n"
                "Nếu dùng Ollama/LM Studio local: có thể để trống.\n\n"
                "Mở Cài Đặt AI?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._show_ai_settings()
            return

        # Cảnh báo nếu dùng model reasoning (chậm)
        self._warn_reasoner_model()

        custom_instr = self.ai_instruction.text().strip()

        # Disable UI
        self.btn_ai_extract.setEnabled(False)
        self.btn_ai_chat.setEnabled(False)
        self.btn_ai_batch.setEnabled(False)
        self.btn_ai_settings.setEnabled(False)
        self.btn_ai_clear_text.setEnabled(False)
        self.lbl_ai_status.setText("🔍 Đang quét deck Anki...")
        self.lbl_ai_status.setStyleSheet("color:#e67e22;font-size:11px;font-weight:bold;")
        self.btn_ai_stop.setVisible(True)
        mw.app.processEvents()

        # Lưu params để dùng trong callback
        self._ai_pending_text = text
        self._ai_pending_instr = custom_instr

        # Quét deck trong background thread (không chặn UI)
        cfg = self._cfg()
        deck_name = self.deck_chooser.currentText()
        if deck_name:
            try:
                deck_id = mw.col.decks.id(deck_name)
                self._deck_scan_worker = DeckScanWorker(
                    cfg["model_name"], deck_id, cfg["front_field"]
                )
                self._deck_scan_worker.progress.connect(self._on_deck_scan_progress)
                self._deck_scan_worker.finished.connect(self._on_deck_scan_finished)
                self._deck_scan_worker.error.connect(self._on_deck_scan_error)
                self._deck_scan_worker.start()
                return
            except Exception as e:
                logger.warning("Lỗi khởi tạo deck scan: %s", e)

        # Fallback: nếu không scan được deck, gọi AI luôn
        self._start_ai_extract(text, custom_instr, [])

    def _on_deck_scan_progress(self, msg):
        self.lbl_ai_status.setText(msg)
        mw.app.processEvents()

    def _on_deck_scan_finished(self, existing_words):
        text = getattr(self, '_ai_pending_text', '')
        instr = getattr(self, '_ai_pending_instr', '')
        self._start_ai_extract(text, instr, existing_words)

    def _on_deck_scan_error(self, err_msg):
        logger.warning("Deck scan error: %s", err_msg)
        text = getattr(self, '_ai_pending_text', '')
        instr = getattr(self, '_ai_pending_instr', '')
        self._start_ai_extract(text, instr, [])

    def _start_ai_extract(self, text, custom_instr, existing_words):
        """Khởi động AI extract thread sau khi đã có existing_words"""
        if existing_words:
            self.lbl_ai_status.setText(f"📚 Deck có {len(existing_words)} từ → AI sẽ tránh trùng")
        else:
            self.lbl_ai_status.setText("⏳ Đang gọi AI...")
        mw.app.processEvents()

        self._ai_thread = AiExtractThread(
            text=text,
            lang=self._current_lang,
            custom_instruction=custom_instr,
            existing_words=existing_words,
            grammar=self._is_grammar,
        )
        self._ai_thread.progress.connect(self._on_ai_progress)
        self._ai_thread.finished.connect(self._on_ai_finished)
        self._ai_thread.error.connect(self._on_ai_error)
        self._ai_thread.start()

    def _on_ai_progress(self, msg):
        self.lbl_ai_status.setText(msg)
        self.lbl_ai_status.setStyleSheet("color:#e67e22;font-size:11px;font-weight:bold;")
        mw.app.processEvents()

    def _on_ai_finished(self, vocab_list):
        self._enable_ai_buttons()

        # Giữ nguyên status từ progress_callback (đã chứa token/cost info)
        # chỉ thêm emoji check nếu chưa có
        current = self.lbl_ai_status.text()
        if not current.startswith("✅"):
            self.lbl_ai_status.setText(f"✅ {current}")
        self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")

        # Lưu tạm để preview
        self._ai_vocab_list = vocab_list

        # Mở dialog Xem Trước & Chỉnh Sửa
        self._show_ai_preview(vocab_list)

        self._ai_thread = None

    def _on_ai_error(self, error_msg):
        self._enable_ai_buttons()

        self.lbl_ai_status.setText(f"❌ Lỗi: {error_msg[:80]}")
        self.lbl_ai_status.setStyleSheet("color:#e74c3c;font-size:11px;font-weight:bold;")

        showInfo(f"❌ Lỗi AI Trích Xuất:\n\n{error_msg}")
        self._ai_thread = None

    def _enable_ai_buttons(self):
        self.btn_ai_extract.setEnabled(True)
        self.btn_ai_chat.setEnabled(True)
        self.btn_ai_batch.setEnabled(True)
        self.btn_ai_settings.setEnabled(True)
        self.btn_ai_clear_text.setEnabled(True)
        self.btn_ai_stop.setVisible(False)

    # ═══════════════════════════════════════════════════════
    #  AI BATCH PROCESS — Xử lý danh sách từ vựng lớn
    # ═══════════════════════════════════════════════════════
    def _ai_batch_process(self):
        """Mở dialog xử lý danh sách từ vựng lớn qua AI"""
        cfg_api = get_api_config()
        if not cfg_api.get("api_key") and "localhost" not in cfg_api.get("api_base", ""):
            reply = QMessageBox.question(
                self, "⚠️ Chưa có API Key",
                "Bạn chưa cấu hình API Key.\n\n"
                "Nếu dùng DeepSeek/OpenAI/OpenRouter: cần API Key.\n"
                "Nếu dùng Ollama/LM Studio local: có thể để trống.\n\n"
                "Mở Cài Đặt AI?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._show_ai_settings()
            return

        from ui.batch_dialog import BatchWordListDialog
        existing_words = []
        try:
            cfg = self._cfg()
            deck_id = mw.col.decks.id(self.deck_chooser.currentText())
            existing_words = get_existing_vocab_from_deck(
                cfg.get("model_name", ""), deck_id, cfg.get("front_field", "Front")
            )
        except Exception:
            pass

        dlg = BatchWordListDialog(
            lang=self._current_lang,
            existing_words=existing_words,
            parent=self,
            grammar=self._is_grammar,
        )
        if dlg.exec():
            vocab_list = dlg.get_result_vocab()
            if vocab_list:
                label = "cấu trúc" if self._is_grammar else "từ"
                self.lbl_ai_status.setText(f"✅ Batch: {len(vocab_list)} {label} đã xử lý!")
                self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")
                # Đổ JSON vào text input để hiển thị trong xưởng
                import json as _json
                json_str = _json.dumps(vocab_list, indent=2, ensure_ascii=False)
                self.json_input.setPlainText(json_str)
                self.raw_data = list(vocab_list)
                self.lbl_raw.setText(f"📊 Kho hàng: {len(self.raw_data)} mục")
                # Mở preview dialog để người dùng xem và chỉnh sửa
                self._show_ai_preview(vocab_list)
            else:
                self.lbl_ai_status.setText("⚠️ Batch: Không có kết quả")
                self.lbl_ai_status.setStyleSheet("color:#e67e22;font-size:11px;")

    # ═══════════════════════════════════════════════════════
    #  AI CHAT — Gửi câu hỏi/yêu cầu đến AI (không cần text)
    # ═══════════════════════════════════════════════════════
    def _ai_chat(self):
        """Gửi yêu cầu đến AI — không cần văn bản trích xuất"""
        user_msg = self.ai_text_input.toPlainText().strip()
        custom_instr = self.ai_instruction.text().strip()

        # Kết hợp message
        full_message = ""
        if custom_instr:
            full_message = custom_instr
        if user_msg:
            if full_message:
                full_message += "\n\n---\n" + user_msg
            else:
                full_message = user_msg

        if not full_message:
            # Cho phép gửi trống — AI sẽ phản hồi dựa trên ngữ cảnh Anki
            full_message = "Xin chào! Hãy phân tích hệ thống Anki của tôi và đưa ra gợi ý học tập."

        # Bảo vệ context DeepSeek: cắt message quá dài (VD kẹp file lớn)
        _MAX_CHAT_CHARS = 12000
        if len(full_message) > _MAX_CHAT_CHARS:
            tooltip(
                f"⚠️ Nội dung quá dài ({len(full_message):,} ký tự).\n"
                f"Chỉ gửi {_MAX_CHAT_CHARS:,} ký tự đầu để tránh vượt context DeepSeek.\n"
                f"💡 Nên dùng 'AI Trích Xuất' cho file lớn (tự chia đoạn xử lý toàn bộ)."
            )
            full_message = full_message[:_MAX_CHAT_CHARS] + "\n\n[⏳ ...(phần còn lại đã cắt do quá dài)]"

        cfg_api = get_api_config()
        if not cfg_api.get("api_key") and "localhost" not in cfg_api.get("api_base", ""):
            reply = QMessageBox.question(
                self, "⚠️ Chưa có API Key",
                "Bạn chưa cấu hình API Key.\n\n"
                "Nếu dùng DeepSeek/OpenAI/OpenRouter: cần API Key.\n"
                "Nếu dùng Ollama/LM Studio local: có thể để trống.\n\n"
                "Mở Cài Đặt AI?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._show_ai_settings()
            return

        # Cảnh báo nếu dùng model reasoning (chậm)
        self._warn_reasoner_model()

        # Disable UI
        self.btn_ai_chat.setEnabled(False)
        self.btn_ai_extract.setEnabled(False)
        self.btn_ai_batch.setEnabled(False)
        self.btn_ai_settings.setEnabled(False)
        self.btn_ai_clear_text.setEnabled(False)

        # Khởi tạo conversation history nếu chưa có
        if not hasattr(self, '_ai_chat_history'):
            self._ai_chat_history = []

        # Ước tính thời gian
        import time as _time
        model = cfg_api.get("model", "")
        is_reasoner = "reasoner" in model.lower()
        est_seconds = 300 if is_reasoner else 30
        est_text = f"~{est_seconds // 60}ph" if est_seconds >= 60 else f"~{est_seconds}s"

        # Bắt đầu đếm thời gian
        self._ai_chat_start_time = _time.time()
        if not hasattr(self, '_ai_chat_timer'):
            self._ai_chat_timer = QTimer(self)
            self._ai_chat_timer.timeout.connect(self._update_ai_chat_timer)
        self._ai_chat_timer.start(1000)

        self.lbl_ai_status.setText(f"⏱ 00:00 | Dự kiến: {est_text} | Đang kết nối...")
        self.lbl_ai_status.setStyleSheet("color:#2980b9;font-size:11px;font-weight:bold;")

        # Hiện nút dừng
        self.btn_ai_stop.setVisible(True)
        mw.app.processEvents()

        # Chạy trong thread
        self._ai_chat_thread = AiChatThread(
            message=full_message,
            lang=self._current_lang,
            conversation_history=self._ai_chat_history if len(self._ai_chat_history) > 0 else None,
        )
        self._ai_chat_thread.progress.connect(self._on_ai_chat_progress)
        self._ai_chat_thread.finished.connect(self._on_ai_chat_finished)
        self._ai_chat_thread.error.connect(self._on_ai_chat_error)
        self._ai_chat_thread.start()

    def _on_ai_chat_progress(self, msg):
        elapsed = self._get_elapsed_str()
        self.lbl_ai_status.setText(f"⏱ {elapsed} | {msg}")
        self.lbl_ai_status.setStyleSheet("color:#2980b9;font-size:11px;font-weight:bold;")
        mw.app.processEvents()

    def _on_ai_chat_finished(self, result: dict):
        self._stop_ai_chat_timer()
        self._enable_ai_buttons()
        elapsed = self._get_elapsed_str()
        token_info = result.get("token_info")
        status_text = f"✅ Hoàn tất sau {elapsed}!"
        if token_info:
            from utils.ai_extractor import _format_token_report
            status_text += f" | {_format_token_report(token_info)}"
        self.lbl_ai_status.setText(status_text)
        self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")

        # Lưu vào conversation history để lần sau AI có context
        reply_text = result.get("reply", "")
        if reply_text:
            self._ai_chat_history.append({"role": "user", "content": self._ai_chat_thread.message})
            self._ai_chat_history.append({"role": "assistant", "content": reply_text[:3000]})
            # Giới hạn 30 tin nhắn
            if len(self._ai_chat_history) > 30:
                self._ai_chat_history = self._ai_chat_history[-30:]

        self._ai_chat_thread = None

        # Mở dialog chat hiển thị kết quả
        self._show_ai_chat_dialog(result)

    def _on_ai_chat_error(self, error_msg):
        self._stop_ai_chat_timer()
        self._enable_ai_buttons()
        elapsed = self._get_elapsed_str()
        self.lbl_ai_status.setText(f"❌ Lỗi sau {elapsed}: {error_msg[:60]}")
        self.lbl_ai_status.setStyleSheet("color:#e74c3c;font-size:11px;font-weight:bold;")
        showInfo(f"❌ Lỗi AI Chat:\n\n{error_msg}")
        self._ai_chat_thread = None

    def _get_elapsed_str(self) -> str:
        """Trả về thời gian đã trôi qua dạng MM:SS"""
        if not hasattr(self, '_ai_chat_start_time'):
            return "00:00"
        import time as _time
        elapsed = int(_time.time() - self._ai_chat_start_time)
        return f"{elapsed // 60:02d}:{elapsed % 60:02d}"

    def _update_ai_chat_timer(self):
        """Cập nhật hiển thị đồng hồ đếm"""
        if hasattr(self, '_ai_chat_start_time') and self._ai_chat_timer.isActive():
            elapsed = self._get_elapsed_str()
            current = self.lbl_ai_status.text()
            # Chỉ cập nhật phần thời gian
            import re
            new_text = re.sub(r'⏱ \d{2}:\d{2}', f'⏱ {elapsed}', current)
            self.lbl_ai_status.setText(new_text)

    def _stop_ai_chat_timer(self):
        """Dừng đồng hồ đếm và ẩn nút dừng"""
        if hasattr(self, '_ai_chat_timer'):
            self._ai_chat_timer.stop()
        self.btn_ai_stop.setVisible(False)

    def _cancel_ai_chat(self):
        """Dừng tác vụ AI (cả chat và extract)"""
        # Dừng AI chat thread
        if hasattr(self, '_ai_chat_thread') and self._ai_chat_thread and self._ai_chat_thread.isRunning():
            self._ai_chat_thread.stop()
            self._ai_chat_thread.wait(2000)
            self._ai_chat_thread = None

        # Dừng AI extract thread
        if hasattr(self, '_ai_thread') and self._ai_thread and self._ai_thread.isRunning():
            self._ai_thread.terminate()
            self._ai_thread.wait(2000)
            self._ai_thread = None

        self._stop_ai_chat_timer()
        self._enable_ai_buttons()
        elapsed = self._get_elapsed_str() if hasattr(self, '_ai_chat_start_time') else "?"
        self.lbl_ai_status.setText(f"⏹ Đã dừng sau {elapsed}")
        self.lbl_ai_status.setStyleSheet("color:#e67e22;font-size:11px;font-weight:bold;")
        tooltip("⏹ Đã dừng yêu cầu AI.")

    def _show_ai_chat_dialog(self, result: dict):
        """Hiển thị dialog chat với phản hồi của AI"""
        reply_text = result.get("reply", "")
        vocab_json = result.get("vocab_json")
        error = result.get("error")

        dlg = AiChatDialog(
            reply_text=reply_text,
            vocab_json=vocab_json,
            error=error,
            parent=self,
        )

        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.accepted_vocab:
            # Người dùng muốn đổ từ vựng vào xưởng
            json_str = json.dumps(dlg.accepted_vocab, indent=2, ensure_ascii=False)
            self.json_input.setPlainText(json_str)
            self._schedule_analyze()

            # Ghi nhận vào lịch sử import
            try:
                deck_name = self.deck_chooser.currentText()
                add_to_import_history(
                    dlg.accepted_vocab,
                    self._current_lang,
                    deck_name=deck_name,
                    source="ai_chat",
                )
            except Exception as e:
                logger.warning("Lỗi ghi lịch sử AI chat: %s", e)

            self.lbl_ai_status.setText(f"✅ Đã đổ {len(dlg.accepted_vocab)} từ vựng vào xưởng!")
            self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")
            showInfo(
                f"🤖 AI Chat Hoàn Tất!\n\n"
                f"📊 Đã đổ {len(dlg.accepted_vocab)} từ vựng vào khung JSON.\n"
                f"👉 Nhấn <b>'Kiểm Định Lô Hàng'</b> để kiểm tra và import."
            )

    # ═══════════════════════════════════════════════════════
    #  DIALOG XEM TRƯỚC & CHỈNH SỬA THẺ SAU AI (wired → ui/ai_preview.py)
    # ═══════════════════════════════════════════════════════
    def _show_ai_preview(self, vocab_list):
        """Mở dialog cho phép xem, sửa, xóa, tái tạo từng thẻ"""
        show_ai_preview_dialog(
            parent=self,
            vocab_list=vocab_list,
            lang=self._current_lang,
            ai_text_input=self.ai_text_input,
            ai_instruction=self.ai_instruction,
            lbl_ai_status=self.lbl_ai_status,
            get_existing_words_fn=self._get_existing_words_for_ai,
            on_finalize_callback=self._finalize_ai_vocab,
        )

    def _finalize_ai_vocab(self, final_list):
        """Nhận dữ liệu cuối cùng từ AI preview, đổ vào json_input và phân tích"""
        if not final_list:
            tooltip("⚠️ Không có từ vựng nào sau khi chỉnh sửa.")
            return

        # Đổ vào json_input
        json_str = json.dumps(final_list, indent=2, ensure_ascii=False)
        self.json_input.setPlainText(json_str)
        self._schedule_analyze()

        # Ghi nhận vào lịch sử import
        try:
            deck_name = self.deck_chooser.currentText()
            add_to_import_history(
                final_list,
                self._current_lang,
                deck_name=deck_name,
                source="ai_extract",
            )
        except Exception as e:
            logger.warning("Lỗi ghi lịch sử AI extract: %s", e)

        self.lbl_ai_status.setText(f"✅ Đã đổ {len(final_list)} từ vựng vào xưởng!")
        self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")

        showInfo(
            f"🤖 AI Trích Xuất Hoàn Tất!\n\n"
            f"📊 Đã đổ {len(final_list)} từ vựng vào khung JSON.\n"
            f"👉 Nhấn <b>'Kiểm Định Lô Hàng'</b> để kiểm tra và import."
        )


# ═══════════════════════════════════════════════════════════
#  REVIEWER HOOKS (wired → hooks/reviewer.py)
# ═══════════════════════════════════════════════════════════
register_hooks()


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════
def start_smart_factory():
    mw.factory_dialog = AnkiSmartFactory(mw)
    mw.factory_dialog.show()


action = QAction("🌐 AnkiTool Multi-Lang V16", mw)
action.setShortcut(QKeySequence("Ctrl+Shift+I"))
qconnect(action.triggered, start_smart_factory)
mw.form.menuTools.addAction(action)

