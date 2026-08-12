"""
AnkiTool Multi-Language V17.0 — Japanese, Chinese & Korean.

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

# Lưu trạng thái ô AI (text + file kẹp) theo từng luồng: {lang: {vocab|grammar: {...}}}
_STATE_PATH = os.path.join(_addon_root, "utils", "factory_state.json")

# ═══════════════════════════════════════════════════════════
#  IMPORTS FROM MODULES (Bridge)
# ═══════════════════════════════════════════════════════════
from Language import LANG_CONFIG, LANG_GRAMMAR_CONFIG, LANG_SELECTOR_INFO
from mode import LANG_TEMPLATES, LANG_CSS, LANG_GRAMMAR_TEMPLATES, LANG_GRAMMAR_CSS
from mode.card_render import build_qfmt as _build_qfmt, build_afmt as _build_afmt
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

# i18n — dịch UI (vi/en) + listener để refresh mượt mà khi đổi ngôn ngữ
from utils.i18n import (
    t, set_language, get_language, toggle_language,
    add_language_listener, remove_language_listener, SUPPORTED_LANGUAGES,
    study_mode_labels,
)

# Import workers (đã tách ra workers/)
from workers import ImportWorker, PreviewThread, AiExtractThread, AiChatThread
from workers.deck_scan_worker import DeckScanWorker

# Import UI dialogs (đã tách ra ui/)
from ui import AiChatDialog, show_ai_settings_dialog, show_diff_meaning_dialog, show_ai_preview_dialog
from ui.deck_manager_dialog import DeckManagerDialog
from utils.deck_manager import refresh_anki

# Import glassmorphism theme engine
from ui.theme import (
    load_config as load_theme_config,
    apply_theme, ThemeDialog, snap_maximize, RatioSplitter,
)

# Import hooks (đã tách ra hooks/)
from hooks.reviewer import register_hooks
from hooks.overview_mode import (
    register_overview_hooks,
    get_study_mode,
    set_study_mode,
    MODES as STUDY_MODES,
    CONF_LANG_KEY,
)

# ═══════════════════════════════════════════════════════════
#  MAIN DIALOG
# ═══════════════════════════════════════════════════════════
class AnkiSmartFactory(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AnkiTool Multi-Lang V17.0 — Vocabulary Factory")
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
        # Danh sách file tài liệu tham khảo đã kẹp: [(name, text), ...] + đường dẫn
        self._ai_attached_files = []
        self._ai_attached_paths = []
        # Trạng thái lưu theo luồng (từ vựng / ngữ pháp) cho từng ngôn ngữ
        self._factory_state = self._load_factory_state()
        # Debounce timer cho JSON parsing (tránh parse liên tục khi gõ)
        self._analyze_timer = QTimer(self)
        self._analyze_timer.setSingleShot(True)
        self._analyze_timer.setInterval(500)  # 500ms debounce
        self._analyze_timer.timeout.connect(self._analyze_content)
        self._setup_ui()
        self._on_lang_changed()

        # Đăng ký refresh UI khi ngôn ngữ giao diện thay đổi (từ nút toggle VI/EN)
        add_language_listener(self._retranslate_ui)

        # Khởi tạo lịch sử import (quét deck lần đầu nếu cần)
        self._init_history()

    def _init_history(self):
        """Khởi tạo lịch sử import trong background (không chặn UI)"""
        try:
            # Chạy init trong thread để không chặn UI
            history = init_import_history(force_rescan=False)
            total = sum(len(v) for v in history.get("entries", {}).values())
            if total > 0:
                self.lbl_ai_status.setText(t("status_history_count", count=total))
                self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;")
        except Exception as e:
            logger.warning("Lỗi init history: %s", e)

    def _cfg(self):
        # Mức 1 (Field Map Editor): bơm json_field_map + all_fields HIỆU LỰC
        # (defaults từ Language/*.py + ghi đè của người dùng trong ai_prompts.json)
        # vào config → mọi nơi dùng self._cfg() đều tự có field mới.
        from utils.prompt_config import apply_field_map_to_cfg
        is_grammar = bool(getattr(self, '_is_grammar', False))
        base = (LANG_GRAMMAR_CONFIG if is_grammar else LANG_CONFIG)[self._current_lang]
        kind = "grammar" if is_grammar else "vocab"
        return apply_field_map_to_cfg(base, self._current_lang, kind)

    def _select_mode(self, is_grammar):
        """Chuyển chế độ Từ vựng ↔ Ngữ pháp (Note Type riêng)"""
        # Luôn đồng bộ trạng thái nút (tránh toggle lệch khi bấm lại nút đang active)
        self.btn_mode_vocab.setChecked(not is_grammar)
        self.btn_mode_grammar.setChecked(is_grammar)
        if getattr(self, '_is_grammar', False) == is_grammar:
            return
        # Lưu trạng thái luồng hiện tại TRƯỚC khi đổi mode
        self._save_current_flow()
        self._is_grammar = is_grammar
        self._on_lang_changed()
        tooltip(t("tooltip_switched_grammar") if is_grammar else t("tooltip_switched_vocab"))

    # ═══════════════════════════════════════════════════════
    #  LƯU / KHÔI PHỤC TRẠNG THÁI Ô AI (text + file) theo luồng
    #  {lang: {vocab|grammar: {"text": ..., "files": [paths]}}}
    # ═══════════════════════════════════════════════════════
    def _load_factory_state(self):
        """Đọc trạng thái đã lưu từ file JSON."""
        try:
            if os.path.exists(_STATE_PATH):
                with open(_STATE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
        except Exception as e:
            logger.warning("Lỗi đọc factory_state: %s", e)
        return {}

    def _save_factory_state(self):
        """Ghi trạng thái vào file JSON."""
        try:
            with open(_STATE_PATH, "w", encoding="utf-8") as f:
                json.dump(self._factory_state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("Lỗi ghi factory_state: %s", e)

    def _flow_key(self):
        """Trả về (lang, mode) — mode: 'vocab' hoặc 'grammar'."""
        mode = "grammar" if self._is_grammar else "vocab"
        return self._current_lang, mode

    def _save_current_flow(self):
        """Lưu text + file paths + thẻ trong xưởng (raw_data/prepared_data/JSON) của luồng
        đang hiển thị (gọi TRƯỚC khi đổi ngôn ngữ/mode/đóng)."""
        try:
            lang, mode = self._flow_key()
            flow = self._factory_state.setdefault(lang, {}).setdefault(mode, {})
            flow["text"] = self.ai_text_input.toPlainText()
            flow["files"] = list(getattr(self, '_ai_attached_paths', []))
            # Lưu thẻ chờ xuất xưởng để KHÔNG bị mất khi đóng Factory
            flow["raw"] = [d for d in getattr(self, 'raw_data', []) if isinstance(d, dict)]
            flow["cards"] = [d for d in getattr(self, 'prepared_data', []) if isinstance(d, dict)]
            try:
                flow["json"] = self.json_input.toPlainText()
            except Exception:
                pass
            self._save_factory_state()
        except Exception as e:
            logger.warning("Lỗi lưu flow state: %s", e)

    def _restore_current_flow(self):
        """Khôi phục text + file kẹp + thẻ trong xưởng cho luồng đang hiển thị (gọi SAU khi setup UI)."""
        try:
            lang, mode = self._flow_key()
            flow = self._factory_state.get(lang, {}).get(mode, {})
            self.ai_text_input.setPlainText(flow.get("text", ""))
            # Khôi phục danh sách file kẹp (đọc lại nếu file còn tồn tại)
            self._ai_attached_files = []
            self._ai_attached_paths = []
            for p in flow.get("files", []):
                if not os.path.exists(p):
                    continue
                try:
                    from utils.ai_extractor import extract_text_from_file
                    text = extract_text_from_file(p)
                    self._ai_attached_files.append((os.path.basename(p), text))
                    self._ai_attached_paths.append(p)
                except Exception:
                    pass
            self._update_ai_files_label()
            # Khôi phục thẻ chờ xuất xưởng (chỉ khi UI đã dựng xong)
            self.raw_data = [d for d in flow.get("raw", []) if isinstance(d, dict)]
            self.prepared_data = [d for d in flow.get("cards", []) if isinstance(d, dict)]
            if hasattr(self, 'lbl_raw'):
                self.lbl_raw.setText(t("filter_raw_count", count=len(self.raw_data)))
            if hasattr(self, 'json_input'):
                try:
                    self.json_input.blockSignals(True)
                    self.json_input.setPlainText(flow.get("json", ""))
                    self.json_input.blockSignals(False)
                except Exception:
                    pass
            if hasattr(self, 'txt_search'):
                self._rebuild_preview()
                self.btn_import.setEnabled(len(self.prepared_data) > 0)
                self.btn_cancel_order.setEnabled(len(self.prepared_data) > 0)
                if self.prepared_data:
                    self.lbl_ready.setText(t("preview_ready", count=len(self.prepared_data)))
        except Exception as e:
            logger.warning("Lỗi khôi phục flow state: %s", e)

    def closeEvent(self, event):
        """Lưu trạng thái ô AI khi đóng Factory."""
        try:
            self._save_current_flow()
        except Exception:
            pass
        try:
            super().closeEvent(event)
        except Exception:
            event.accept()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 10)
        root.setSpacing(8)

        # ── TOP TOOLBAR: giao diện + ngôn ngữ + chia cửa sổ ─────────
        top = QHBoxLayout()
        top.setSpacing(6)
        self.lbl_brand = QLabel(t("brand_label"))
        self.lbl_brand.setStyleSheet("font-size:14px;font-weight:bold;")
        top.addWidget(self.lbl_brand)

        self.btn_theme = QPushButton(t("btn_theme"))
        self.btn_theme.setProperty("class", "primary")
        self.btn_theme.setToolTip(t("btn_theme_tip"))
        self.btn_theme.clicked.connect(self._open_theme_dialog)
        top.addWidget(self.btn_theme)

        self.btn_lang_toggle = QPushButton(t("btn_lang_toggle"))
        self.btn_lang_toggle.setProperty("class", "ghost")
        self.btn_lang_toggle.setToolTip(t("btn_lang_toggle_tip"))
        self.btn_lang_toggle.clicked.connect(self._toggle_ui_language)
        top.addWidget(self.btn_lang_toggle)

        self.btn_snap_max = QPushButton(t("btn_snap_max"))
        self.btn_snap_max.setProperty("class", "ghost")
        self.btn_snap_max.setToolTip(t("btn_snap_max_tip"))
        self.btn_snap_max.clicked.connect(lambda: snap_maximize(self))
        top.addWidget(self.btn_snap_max)

        top.addStretch()
        self.lbl_tip = QLabel(t("lbl_tip"))
        self.lbl_tip.setProperty("class", "dim")
        top.addWidget(self.lbl_tip)
        root.addLayout(top)

        # ── MAIN SPLITTER (chia đôi, kéo thả 3:7, thích ứng) ──
        self.main_splitter = RatioSplitter()

        # ── LEFT ─────────────────────────────────────────
        left_panel = QWidget()
        left = QVBoxLayout(left_panel)
        left.setContentsMargins(0, 0, 4, 0)
        left.setSpacing(6)

        # Language selector
        self.lang_grp = QGroupBox(t("lang_grp_title"))
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
        self.mode_grp = QGroupBox(t("mode_grp_title"))
        mode_layout = QHBoxLayout()
        self.btn_mode_vocab = QPushButton(t("btn_mode_vocab"))
        self.btn_mode_vocab.setCheckable(True)
        self.btn_mode_vocab.setChecked(True)
        self.btn_mode_vocab.setStyleSheet(
            "padding:8px;font-weight:bold;border-radius:10px;"
            "QPushButton:checked{background:#2ecc71;color:white;border:2px solid #27ae60;}"
            "QPushButton:!checked{background:rgba(255,255,255,0.08);color:#eaf0f6;border:1px solid rgba(255,255,255,0.18);}"
        )
        self.btn_mode_vocab.clicked.connect(lambda checked: self._select_mode(False))
        mode_layout.addWidget(self.btn_mode_vocab)
        self.btn_mode_grammar = QPushButton(t("btn_mode_grammar"))
        self.btn_mode_grammar.setCheckable(True)
        self.btn_mode_grammar.setStyleSheet(
            "padding:8px;font-weight:bold;border-radius:10px;"
            "QPushButton:checked{background:#34495e;color:white;border:2px solid #2c3e50;}"
            "QPushButton:!checked{background:rgba(255,255,255,0.08);color:#eaf0f6;border:1px solid rgba(255,255,255,0.18);}"
        )
        self.btn_mode_grammar.clicked.connect(lambda checked: self._select_mode(True))
        mode_layout.addWidget(self.btn_mode_grammar)
        self.mode_grp.setLayout(mode_layout)
        left.addWidget(self.mode_grp)

        # Deck + file
        bar = QHBoxLayout()
        self.deck_chooser = QComboBox()
        self.deck_chooser.addItems(mw.col.decks.all_names())
        self.lbl_deck = QLabel(t("deck_label"))
        bar.addWidget(self.lbl_deck, 0)
        bar.addWidget(self.deck_chooser, 1)
        self.btn_refresh_deck = QPushButton("🔄")
        self.btn_refresh_deck.setToolTip(t("btn_refresh_deck_tip"))
        self.btn_refresh_deck.setMaximumWidth(36)
        self.btn_refresh_deck.clicked.connect(self._refresh_deck_chooser)
        bar.addWidget(self.btn_refresh_deck, 0)
        self.btn_manage_deck = QPushButton(t("deck_manage_btn"))
        self.btn_manage_deck.setProperty("class", "info")
        self.btn_manage_deck.setToolTip(t("btn_manage_deck_tip"))
        self.btn_manage_deck.clicked.connect(self._open_deck_manager)
        bar.addWidget(self.btn_manage_deck, 0)
        self.btn_load = QPushButton(t("open_file_btn"))
        self.btn_load.setProperty("class", "info")
        self.btn_load.clicked.connect(self._load_from_file)
        bar.addWidget(self.btn_load, 0)
        left.addLayout(bar)

        # Sample buttons
        bar2 = QHBoxLayout()
        self.btn_sample = QPushButton(t("sample_json_btn"))
        self.btn_sample.setProperty("class", "ghost")
        self.btn_sample.clicked.connect(self._show_sample_json)
        bar2.addWidget(self.btn_sample)
        self.btn_history = QPushButton(t("btn_history"))
        self.btn_history.setProperty("class", "ghost")
        self.btn_history.setToolTip(t("btn_history_tip"))
        self.btn_history.clicked.connect(self._open_history_browser)
        bar2.addWidget(self.btn_history)
        bar2.addStretch()
        left.addLayout(bar2)

        # ── AI Trích Xuất Từ Vựng ──────────────────────────
        self.ai_grp = QGroupBox(t("ai_group_title"))
        ai_main = QVBoxLayout()

        # Row 1: Buttons
        ai_bar = QHBoxLayout()

        self.btn_ai_settings = QPushButton(t("ai_settings_btn"))
        self.btn_ai_settings.setStyleSheet(
            "padding:5px 8px;background:#8e44ad;color:white;"
            "font-weight:bold;border-radius:6px;border:none;"
        )
        self.btn_ai_settings.clicked.connect(self._show_ai_settings)
        ai_bar.addWidget(self.btn_ai_settings)

        self.btn_ai_clear_text = QPushButton(t("ai_clear_text_btn"))
        self.btn_ai_clear_text.setStyleSheet(
            "padding:5px 8px;background:#95a5a6;color:white;"
            "font-weight:bold;border-radius:6px;border:none;"
        )
        self.btn_ai_clear_text.clicked.connect(self._ai_clear_text)
        ai_bar.addWidget(self.btn_ai_clear_text)

        self.btn_ai_extract = QPushButton(t("ai_extract_btn"))
        self.btn_ai_extract.setStyleSheet(
            "padding:5px 10px;background:#e67e22;color:white;"
            "font-weight:bold;border-radius:6px;border:none;font-size:13px;"
        )
        self.btn_ai_extract.clicked.connect(self._ai_extract)
        self.btn_ai_extract.setEnabled(True)
        ai_bar.addWidget(self.btn_ai_extract)

        self.btn_ai_batch = QPushButton(t("ai_batch_btn"))
        self.btn_ai_batch.setStyleSheet(
            "padding:5px 8px;background:#2ecc71;color:white;"
            "font-weight:bold;border-radius:6px;border:none;font-size:12px;"
        )
        self.btn_ai_batch.setToolTip(t("btn_ai_batch_tip"))
        self.btn_ai_batch.clicked.connect(self._ai_batch_process)
        self.btn_ai_batch.setEnabled(True)
        ai_bar.addWidget(self.btn_ai_batch)

        self.btn_ai_chat = QPushButton(t("ai_chat_btn"))
        self.btn_ai_chat.setStyleSheet(
            "padding:5px 10px;background:#2980b9;color:white;"
            "font-weight:bold;border-radius:6px;border:none;font-size:13px;"
        )
        self.btn_ai_chat.setToolTip(t("btn_ai_chat_tip"))
        self.btn_ai_chat.clicked.connect(self._ai_chat)
        self.btn_ai_chat.setEnabled(True)
        ai_bar.addWidget(self.btn_ai_chat)

        self.btn_ai_stop = QPushButton(t("ai_stop_btn"))
        self.btn_ai_stop.setStyleSheet(
            "padding:5px 8px;background:#e74c3c;color:white;"
            "font-weight:bold;border-radius:6px;border:none;font-size:12px;"
        )
        self.btn_ai_stop.setToolTip(t("btn_ai_stop_tip"))
        self.btn_ai_stop.clicked.connect(self._cancel_ai_chat)
        self.btn_ai_stop.setVisible(False)
        ai_bar.addWidget(self.btn_ai_stop)

        self.lbl_ai_status = QLabel("")
        self.lbl_ai_status.setProperty("class", "dim")
        ai_bar.addWidget(self.lbl_ai_status, 1)

        ai_main.addLayout(ai_bar)

        # Row 1b: Đính kèm file tài liệu tham khảo cho AI
        file_bar = QHBoxLayout()
        self.btn_ai_attach = QPushButton(t("btn_ai_attach"))
        self.btn_ai_attach.setStyleSheet(
            "padding:5px 12px;background:#16a085;color:white;"
            "font-weight:bold;border-radius:6px;border:none;"
        )
        self.btn_ai_attach.setToolTip(t("btn_ai_attach_tip"))
        self.btn_ai_attach.clicked.connect(self._attach_ai_files)
        file_bar.addWidget(self.btn_ai_attach)

        self.btn_ai_attach_clear = QPushButton(t("btn_ai_attach_clear"))
        self.btn_ai_attach_clear.setStyleSheet(
            "padding:5px 12px;background:#95a5a6;color:white;"
            "font-weight:bold;border-radius:6px;border:none;"
        )
        self.btn_ai_attach_clear.setToolTip(t("btn_ai_attach_clear_tip"))
        self.btn_ai_attach_clear.clicked.connect(self._clear_ai_files)
        file_bar.addWidget(self.btn_ai_attach_clear)

        self.lbl_ai_files = QLabel("")
        self.lbl_ai_files.setStyleSheet("color:#27ae60;font-size:11px;")
        self.lbl_ai_files.setWordWrap(True)
        file_bar.addWidget(self.lbl_ai_files, 1)
        ai_main.addLayout(file_bar)

        # Row 2: Text input area for AI
        self.ai_text_input = QPlainTextEdit()
        self.ai_text_input.setPlaceholderText(t("ai_input_placeholder_vocab"))
        self.ai_text_input.setMaximumHeight(80)
        self.ai_text_input.setStyleSheet("font-size:12px;")
        ai_main.addWidget(self.ai_text_input)

        # Row 3: Custom instruction
        instr_bar = QHBoxLayout()
        self.lbl_instruction = QLabel(t("ai_instruction_label"))
        instr_bar.addWidget(self.lbl_instruction)
        self.ai_instruction = QLineEdit()
        self.ai_instruction.setPlaceholderText(t("ai_instruction_placeholder"))
        self.ai_instruction.setStyleSheet("font-size:12px;padding:4px;")
        instr_bar.addWidget(self.ai_instruction, 1)
        ai_main.addLayout(instr_bar)

        self.ai_grp.setLayout(ai_main)
        left.addWidget(self.ai_grp)

        self.lbl_json_label = QLabel(t("json_input_label"))
        left.addWidget(self.lbl_json_label)
        self.json_input = QPlainTextEdit()
        self.json_input.textChanged.connect(self._schedule_analyze)
        left.addWidget(self.json_input)

        # Filters
        self.filter_grp = QGroupBox(t("filter_group_title"))
        gl = QGridLayout()

        self.lbl_raw = QLabel(t("filter_raw_count", count=0))
        self.lbl_raw.setStyleSheet("color:#e67e22;font-weight:bold;")
        gl.addWidget(self.lbl_raw, 0, 0, 1, 2)

        self.lbl_level = QLabel(t("filter_level_label"))
        self.cbo_level = QComboBox()
        gl.addWidget(self.lbl_level, 1, 0)
        gl.addWidget(self.cbo_level, 1, 1)

        self.txt_topic = QLineEdit()
        self.txt_topic.setPlaceholderText(t("filter_topic_placeholder"))
        self.lbl_topic = QLabel(t("filter_topic_label"))
        gl.addWidget(self.lbl_topic, 2, 0)
        gl.addWidget(self.txt_topic, 2, 1)

        audio_box = QHBoxLayout()
        self.chk_audio_vocab = QCheckBox(t("filter_audio_vocab"))
        self.chk_audio_vocab.setChecked(True)
        self.chk_audio_ex1 = QCheckBox(t("filter_audio_ex1"))
        self.chk_audio_ex1.setChecked(True)
        self.chk_audio_ex2 = QCheckBox(t("filter_audio_ex2"))
        self.chk_audio_ex2.setChecked(True)
        for c in (self.chk_audio_vocab, self.chk_audio_ex1, self.chk_audio_ex2):
            audio_box.addWidget(c)
        self.lbl_audio = QLabel(t("filter_audio_label"))
        gl.addWidget(self.lbl_audio, 3, 0)
        gl.addLayout(audio_box, 3, 1)

        self.btn_verify = QPushButton(t("btn_verify"))
        self.btn_verify.setProperty("class", "warning")
        self.btn_verify.setMinimumHeight(42)
        self.btn_verify.setToolTip(t("btn_verify_tip"))
        self.btn_verify.clicked.connect(self._verify_batch)

        self.btn_rebuild = QPushButton(t("btn_rebuild"))
        self.btn_rebuild.setProperty("class", "purple")
        self.btn_rebuild.setMinimumHeight(42)
        self.btn_rebuild.setToolTip(t("btn_rebuild_tip"))
        self.btn_rebuild.clicked.connect(self._force_rebuild_model)

        self.btn_diff_meaning = QPushButton(t("btn_diff_meaning"))
        self.btn_diff_meaning.setProperty("class", "warning")
        self.btn_diff_meaning.setMinimumHeight(42)
        self.btn_diff_meaning.setEnabled(False)
        self.btn_diff_meaning.setToolTip(t("btn_diff_meaning_tip"))
        self.btn_diff_meaning.clicked.connect(self._show_diff_meaning_report)

        # Hàng ngang 3 nút
        action_bar = QHBoxLayout()
        action_bar.addWidget(self.btn_verify, 1)
        action_bar.addWidget(self.btn_rebuild, 1)
        action_bar.addWidget(self.btn_diff_meaning, 1)
        gl.addLayout(action_bar, 4, 0, 1, 2)

        # ── Voice Selection ───────────────────────────────
        self.voice_grp = QGroupBox(t("voice_group_title"))
        vgl = QHBoxLayout()
        self.lbl_voice = QLabel(t("voice_label"))
        vgl.addWidget(self.lbl_voice, 0)
        self.cbo_voice = QComboBox()
        self.cbo_voice.setMinimumWidth(150)
        self.cbo_voice.currentIndexChanged.connect(self._on_voice_changed)
        vgl.addWidget(self.cbo_voice, 1)
        self.btn_preview_voice = QPushButton(t("voice_preview_btn"))
        self.btn_preview_voice.setProperty("class", "purple")
        self.btn_preview_voice.clicked.connect(self._preview_voice)
        vgl.addWidget(self.btn_preview_voice, 0)
        vgl.addSpacing(12)
        self.lbl_speed = QLabel(t("voice_speed_label"))
        vgl.addWidget(self.lbl_speed, 0)
        self.spin_speed = QDoubleSpinBox()
        self.spin_speed.setRange(0.25, 4.0)
        self.spin_speed.setSingleStep(0.05)
        self.spin_speed.setDecimals(2)
        self.spin_speed.setSuffix(" ×")
        self.spin_speed.setValue(1.0)
        self.spin_speed.setMinimumWidth(70)
        self.spin_speed.setToolTip(t("spin_speed_tip"))
        self.spin_speed.valueChanged.connect(self._on_speed_changed)
        vgl.addWidget(self.spin_speed, 0)
        # ── Chế độ học mặc định (đồng bộ với Study now của Onigiri) ──
        vgl.addSpacing(12)
        self.lbl_study_mode = QLabel(t("study_mode_label"))
        vgl.addWidget(self.lbl_study_mode, 0)
        self.cbo_study_mode = QComboBox()
        self.cbo_study_mode.setMinimumWidth(130)
        self.cbo_study_mode.currentIndexChanged.connect(self._on_study_mode_changed)
        vgl.addWidget(self.cbo_study_mode, 0)
        self.voice_grp.setLayout(vgl)
        left.addWidget(self.voice_grp)

        self.main_splitter.addWidget(left_panel)

        # ── RIGHT ────────────────────────────────────────
        right_panel = QWidget()
        right = QVBoxLayout(right_panel)
        right.setContentsMargins(4, 0, 0, 0)
        right.setSpacing(6)

        # Bộ Lọc & Gác Cổng V5+ (chuyển sang cột phải)
        self.filter_grp.setLayout(gl)
        right.addWidget(self.filter_grp)

        self.lbl_preview_title = QLabel(t("preview_label"))
        right.addWidget(self.lbl_preview_title)

        # ── Tìm kiếm + lọc nhanh theo loại thẻ ──
        sf = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(t("search_placeholder"))
        self.txt_search.textChanged.connect(self._rebuild_preview)
        sf.addWidget(self.txt_search, 1)
        self.cbo_filter = QComboBox()
        self._repopulate_filter_combo()
        self.cbo_filter.setToolTip(t("cbo_filter_tip"))
        self.cbo_filter.currentIndexChanged.connect(self._rebuild_preview)
        sf.addWidget(self.cbo_filter, 0)
        right.addLayout(sf)

        self.preview_list = QListWidget()
        self.preview_list.setMinimumHeight(120)  # thích ứng theo kích thước kéo thả
        self.preview_list.itemChanged.connect(self._update_selection_label)
        right.addWidget(self.preview_list)

        # ── Nút chọn nhanh + số thẻ đã chọn ──
        sel = QHBoxLayout()
        self.btn_select_all = QPushButton(t("btn_select_all"))
        self.btn_select_all.setToolTip(t("btn_select_all_tip"))
        self.btn_select_all.clicked.connect(self._select_all_visible)
        sel.addWidget(self.btn_select_all)
        self.btn_select_none = QPushButton(t("btn_select_none"))
        self.btn_select_none.setToolTip(t("btn_select_none_tip"))
        self.btn_select_none.clicked.connect(self._select_none_visible)
        sel.addWidget(self.btn_select_none)
        sel.addStretch()
        self.lbl_sel = QLabel(t("lbl_sel_count", selected=0, total=0))
        self.lbl_sel.setStyleSheet("color:#2980b9;font-weight:bold;")
        sel.addWidget(self.lbl_sel)
        right.addLayout(sel)

        rng = QHBoxLayout()
        self.spin_start = QSpinBox()
        self.spin_start.setRange(1, 9999)
        self.spin_start.setToolTip(t("rng_tip"))
        self.spin_start.valueChanged.connect(self._on_range_changed)
        self.spin_end = QSpinBox()
        self.spin_end.setRange(1, 9999)
        self.spin_end.setToolTip(t("rng_tip"))
        self.spin_end.valueChanged.connect(self._on_range_changed)
        self.lbl_rng_from = QLabel(t("rng_from_label"))
        self.lbl_rng_to = QLabel(t("rng_to_label"))
        self.lbl_rng_hint = QLabel(t("rng_hint"))
        rng.addWidget(self.lbl_rng_from)
        rng.addWidget(self.spin_start)
        rng.addWidget(self.lbl_rng_to)
        rng.addWidget(self.spin_end)
        rng.addWidget(self.lbl_rng_hint)
        rng.addStretch()
        right.addLayout(rng)

        self.lbl_ready = QLabel(t("preview_ready", count=0))
        self.lbl_ready.setStyleSheet("color:#27ae60;font-weight:bold;")
        right.addWidget(self.lbl_ready)

        self.pbar = QProgressBar()
        self.pbar.setVisible(False)
        right.addWidget(self.pbar)

        self.lbl_status = QLabel("")
        self.lbl_status.setProperty("class", "dim")
        right.addWidget(self.lbl_status)

        self.btn_import = QPushButton(t("btn_import"))
        self.btn_import.setProperty("class", "success")
        self.btn_import.setMinimumHeight(52)
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self._process_import)
        right.addWidget(self.btn_import)

        op_row = QHBoxLayout()
        self.btn_cancel = QPushButton(t("btn_cancel"))
        self.btn_cancel.setProperty("class", "danger")
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._cancel_import)
        op_row.addWidget(self.btn_cancel)
        self.btn_cancel_order = QPushButton(t("btn_cancel_order"))
        self.btn_cancel_order.setProperty("class", "danger")
        self.btn_cancel_order.setMinimumHeight(40)
        self.btn_cancel_order.setEnabled(False)
        self.btn_cancel_order.setToolTip(t("btn_cancel_order_tip"))
        self.btn_cancel_order.clicked.connect(self._cancel_order)
        op_row.addWidget(self.btn_cancel_order)
        right.addLayout(op_row)

        self.main_splitter.addWidget(right_panel)
        self.main_splitter.setStretchFactor(0, 5)
        self.main_splitter.setStretchFactor(1, 5)
        self.main_splitter.setSizes([660, 640])
        # Thanh phân cách kéo mượt, mỗi cột giới hạn 30%–70% (3:7)
        self.main_splitter.setHandleWidth(8)
        root.addWidget(self.main_splitter, 1)

        # Áp theme glassmorphism
        self._theme_cfg = apply_theme(self, self._theme_cfg)

        # Đồng bộ toàn bộ chuỗi hiển thị theo ngôn ngữ UI hiện tại
        self._retranslate_ui()

    def _toggle_ui_language(self):
        """Chuyển ngôn ngữ giao diện giữa Tiếng Việt ⇄ English (mượt mà, không đóng cửa sổ)."""
        try:
            toggle_language()
            # _retranslate_ui được gọi tự động qua listener trong set_language
        except Exception as e:
            logger.warning("Lỗi chuyển ngôn ngữ: %s", e)

    def _update_window_title(self):
        """Cập nhật tiêu đề cửa sổ theo ngôn ngữ ngôn ngữ học + hậu tố Ngữ pháp."""
        try:
            cfg = self._cfg()
            base = f"AnkiTool Multi-Lang V17.0 — {cfg['label']}"
            if self._is_grammar:
                base += t("grammar_suffix")
            self.setWindowTitle(base)
        except Exception as e:
            logger.warning("Lỗi cập nhật tiêu đề: %s", e)

    def _repopulate_filter_combo(self):
        """Điền lại các mục lọc thẻ theo ngôn ngữ UI hiện tại (giữ nguyên lựa chọn)."""
        try:
            current = self.cbo_filter.currentText() if hasattr(self, 'cbo_filter') else ""
            items = [
                t("cbo_filter_all"), t("cbo_filter_new"), t("cbo_filter_update"),
                t("cbo_filter_conflict"), t("cbo_filter_diff"),
            ]
            self.cbo_filter.blockSignals(True)
            self.cbo_filter.clear()
            self.cbo_filter.addItems(items)
            if current in items:
                self.cbo_filter.setCurrentText(current)
            self.cbo_filter.blockSignals(False)
        except Exception as e:
            logger.warning("Lỗi repopulate filter combo: %s", e)

    def _retranslate_ui(self):
        """Cập nhật toàn bộ chuỗi hiển thị theo ngôn ngữ UI hiện tại (live refresh)."""
        try:
            # Toolbar
            self.lbl_brand.setText(t("brand_label"))
            self.btn_theme.setText(t("btn_theme"))
            self.btn_theme.setToolTip(t("btn_theme_tip"))
            self.btn_lang_toggle.setText(t("btn_lang_toggle"))
            self.btn_lang_toggle.setToolTip(t("btn_lang_toggle_tip"))
            self.btn_snap_max.setText(t("btn_snap_max"))
            self.btn_snap_max.setToolTip(t("btn_snap_max_tip"))
            self.lbl_tip.setText(t("lbl_tip"))

            # Selectors
            self.lang_grp.setTitle(self._cfg()["label"])
            self.mode_grp.setTitle(t("mode_grp_title"))
            self.btn_mode_vocab.setText(t("btn_mode_vocab"))
            self.btn_mode_grammar.setText(t("btn_mode_grammar"))
            self.lbl_deck.setText(t("deck_label"))
            self.btn_refresh_deck.setToolTip(t("btn_refresh_deck_tip"))
            self.btn_manage_deck.setText(t("deck_manage_btn"))
            self.btn_manage_deck.setToolTip(t("btn_manage_deck_tip"))
            self.btn_load.setText(t("open_file_btn"))
            self.btn_sample.setText(t("sample_json_btn"))
            self.btn_history.setText(t("btn_history"))
            self.btn_history.setToolTip(t("btn_history_tip"))

            # AI group
            self.ai_grp.setTitle(t("ai_group_title"))
            self.btn_ai_settings.setText(t("ai_settings_btn"))
            self.btn_ai_clear_text.setText(t("ai_clear_text_btn"))
            self.btn_ai_extract.setText(t("ai_extract_btn"))
            self.btn_ai_batch.setText(t("ai_batch_btn"))
            self.btn_ai_batch.setToolTip(t("btn_ai_batch_tip"))
            self.btn_ai_chat.setText(t("ai_chat_btn"))
            self.btn_ai_chat.setToolTip(t("btn_ai_chat_tip"))
            self.btn_ai_stop.setText(t("ai_stop_btn"))
            self.btn_ai_stop.setToolTip(t("btn_ai_stop_tip"))
            self.btn_ai_attach.setText(t("btn_ai_attach"))
            self.btn_ai_attach.setToolTip(t("btn_ai_attach_tip"))
            self.btn_ai_attach_clear.setText(t("btn_ai_attach_clear"))
            self.btn_ai_attach_clear.setToolTip(t("btn_ai_attach_clear_tip"))
            self.lbl_instruction.setText(t("ai_instruction_label"))
            self.ai_instruction.setPlaceholderText(t("ai_instruction_placeholder"))
            self.lbl_json_label.setText(t("json_input_label"))

            # Filters
            self.filter_grp.setTitle(t("filter_group_title"))
            self.lbl_topic.setText(t("filter_topic_label"))
            self.txt_topic.setPlaceholderText(t("filter_topic_placeholder"))
            self.lbl_audio.setText(t("filter_audio_label"))
            self.chk_audio_vocab.setText(t("filter_audio_vocab"))
            self.chk_audio_ex1.setText(t("filter_audio_ex1"))
            self.chk_audio_ex2.setText(t("filter_audio_ex2"))
            self.btn_verify.setText(t("btn_verify"))
            self.btn_verify.setToolTip(t("btn_verify_tip"))
            self.btn_rebuild.setText(t("btn_rebuild"))
            self.btn_rebuild.setToolTip(t("btn_rebuild_tip"))
            self.btn_diff_meaning.setText(t("btn_diff_meaning"))
            self.btn_diff_meaning.setToolTip(t("btn_diff_meaning_tip"))

            # Voice
            self.voice_grp.setTitle(t("voice_group_title"))
            self.lbl_voice.setText(t("voice_label"))
            self.lbl_speed.setText(t("voice_speed_label"))
            self.lbl_study_mode.setText(t("study_mode_label"))
            self.btn_preview_voice.setText(t("voice_preview_btn"))
            self.spin_speed.setToolTip(t("spin_speed_tip"))
            self.chk_audio_vocab.setToolTip(t("voice_tooltip"))
            self.chk_audio_ex1.setToolTip(t("voice_tooltip"))
            self.chk_audio_ex2.setToolTip(t("voice_tooltip"))

            # Preview area
            self.lbl_preview_title.setText(t("preview_label"))
            self.txt_search.setPlaceholderText(t("search_placeholder"))
            self._repopulate_filter_combo()
            self.cbo_filter.setToolTip(t("cbo_filter_tip"))
            self.btn_select_all.setText(t("btn_select_all"))
            self.btn_select_all.setToolTip(t("btn_select_all_tip"))
            self.btn_select_none.setText(t("btn_select_none"))
            self.btn_select_none.setToolTip(t("btn_select_none_tip"))
            self.lbl_rng_from.setText(t("rng_from_label"))
            self.lbl_rng_to.setText(t("rng_to_label"))
            self.lbl_rng_hint.setText(t("rng_hint"))
            self.spin_start.setToolTip(t("rng_tip"))
            self.spin_end.setToolTip(t("rng_tip"))
            self.btn_import.setText(t("btn_import"))
            self.btn_cancel.setText(t("btn_cancel"))
            self.btn_cancel_order.setText(t("btn_cancel_order"))
            self.btn_cancel_order.setToolTip(t("btn_cancel_order_tip"))

            # Counts theo dữ liệu hiện tại
            self.lbl_raw.setText(t("filter_raw_count", count=len(self.raw_data)))
            self.lbl_ready.setText(t("preview_ready", count=len(self.prepared_data)))
            # Dựng lại danh sách thẻ để cập nhật các hậu tố (Nghĩa khác/Cập nhật/Trùng mờ)
            if hasattr(self, 'preview_list') and self.prepared_data:
                self._rebuild_preview()
            else:
                self._update_selection_label()
            self._update_window_title()
        except Exception as e:
            logger.warning("Lỗi retranslate UI: %s", e)

    def _open_theme_dialog(self):
        """Mở hộp thoại tùy chỉnh giao diện glassmorphism"""
        dlg = ThemeDialog(self)
        dlg.exec()

    def _open_deck_manager(self):
        """Mở dialog quản lý Parent/Sub Deck (tạo/sửa/xóa, đồng bộ tức thì)."""
        dlg = DeckManagerDialog(self)
        dlg.exec()
        # Sau khi đóng dialog, làm mới deck_chooser để phản ánh thay đổi
        self._refresh_deck_chooser()

    def _refresh_deck_chooser(self):
        """Làm mới danh sách deck trong deck_chooser từ Anki collection."""
        try:
            current = self.deck_chooser.currentText()
            names = mw.col.decks.all_names()
            self.deck_chooser.blockSignals(True)
            self.deck_chooser.clear()
            self.deck_chooser.addItems(names)
            if current in names:
                self.deck_chooser.setCurrentText(current)
            self.deck_chooser.blockSignals(False)
        except Exception as e:
            logger.warning("Lỗi làm mới deck_chooser: %s", e)

    def _apply_lang_button_styles(self):
        """Áp dụng style chuẩn quốc kỳ cho nút ngôn ngữ"""
        default_style = """
        QPushButton {
            padding: 8px 14px;
            font-weight: bold;
            font-size: 13px;
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
            """,
            "korean": """
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ffffff, stop:1 #f5f5f5);
                    color: #c60c30;
                    border: 2px solid #c60c30;
                    font-size: 15px;
                }
            """
        }

        for key, btn in self.btn_lang.items():
            style = default_style + selected_styles.get(key, "")
            btn.setStyleSheet(style)

    def _select_lang(self, lang_key):
        if lang_key != self._current_lang:
            # Lưu trạng thái luồng hiện tại trước khi chuyển ngôn ngữ
            self._save_current_flow()
        self._current_lang = lang_key
        # Lưu ngôn ngữ đang chọn để selector Overview hiển thị đúng label mode
        try:
            mw.col.conf[CONF_LANG_KEY] = lang_key
        except Exception:
            pass
        self._on_lang_changed()

    def _on_lang_changed(self):
        cfg = self._cfg()
        for k, btn in self.btn_lang.items():
            btn.setChecked(k == self._current_lang)

        self._apply_lang_button_styles()

        # Cập nhật tiêu đề group box ngôn ngữ + tiêu đề cửa sổ
        self.lang_grp.setTitle(cfg["label"])
        self._update_window_title()

        self.lbl_level.setText(cfg["level_label"])
        self.cbo_level.clear()
        self.cbo_level.addItems(cfg["level_choices"])

        tooltip_text = t("voice_tooltip")
        self.chk_audio_vocab.setToolTip(tooltip_text)
        self.chk_audio_ex1.setToolTip(tooltip_text)
        self.chk_audio_ex2.setToolTip(tooltip_text)

        self.raw_data = []
        self.prepared_data = []
        self.preview_list.clear()
        self.btn_import.setEnabled(False)
        self.json_input.clear()
        self.btn_diff_meaning.setEnabled(False)

        # Bỏ file tham khảo cũ khi đổi ngôn ngữ / chế độ
        self._ai_attached_files = []
        if hasattr(self, 'lbl_ai_files'):
            self.lbl_ai_files.setText("")

        # Cập nhật placeholder theo chế độ
        if self._is_grammar:
            self.ai_text_input.setPlaceholderText(t("ai_input_placeholder_grammar"))
        else:
            self.ai_text_input.setPlaceholderText(t("ai_input_placeholder_vocab"))

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

        # Đồng bộ dropdown chế độ học với cấu hình hiện tại
        if hasattr(self, 'cbo_study_mode'):
            self._sync_study_mode_combo()

        # Khôi phục text + file kẹp cho luồng (ngôn ngữ + mode) đang hiển thị
        self._restore_current_flow()

        # Đồng bộ toàn bộ chuỗi hiển thị theo ngôn ngữ UI hiện tại
        self._retranslate_ui()

    def _on_voice_changed(self, index):
        lang = self._cfg()["lang_code"]
        voices = get_voice_options(lang)
        if 0 <= index < len(voices):
            set_selected_voice(lang, voices[index]["id"])

    def _on_speed_changed(self, value):
        lang = self._cfg()["lang_code"]
        set_default_speed(lang, round(value, 2))

    def _sync_study_mode_combo(self):
        """Đồng bộ dropdown mode với cấu hình hiện tại."""
        try:
            lang = self._current_lang
            # Nhãn theo ngôn ngữ UI (vi: "1. Nhật→Việt" / en: "1. Japanese→English")
            lbl = study_mode_labels(lang)
            current = get_study_mode()
            self.cbo_study_mode.blockSignals(True)
            self.cbo_study_mode.clear()
            for k in STUDY_MODES:
                self.cbo_study_mode.addItem(lbl.get(k, k), k)
            idx = self.cbo_study_mode.findData(current)
            self.cbo_study_mode.setCurrentIndex(idx if idx >= 0 else 0)
            self.cbo_study_mode.blockSignals(False)
        except Exception as e:
            logger.warning("Lỗi đồng bộ mode combo: %s", e)

    def _on_study_mode_changed(self, index):
        """Lưu chế độ học đã chọn vào config (đồng bộ với Study now Onigiri)."""
        try:
            data = self.cbo_study_mode.itemData(index)
            if data:
                set_study_mode(data)
        except Exception as e:
            logger.warning("Lỗi lưu study mode: %s", e)

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
        self.btn_preview_voice.setText(t("voice_preview_btn"))
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
                    tooltip(t("tooltip_audio_preview_fail"))
        else:
            tooltip(t("tooltip_audio_gen_fail"))

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
}''',
            "korean": '''{
  "front": "먹다",
  "romanization": "meokda",
  "meaning": "ăn",
  "sino_vietnamese": "",
  "topik_level": "TOPIK I",
  "topic": "Động từ",
  "example": "아침에 밥을 먹어요.",
  "example_romanization": "achime babeul meogeoyo.",
  "example_vn": "Buổi sáng tôi ăn cơm.",
  "example_2": "친구와 함께 저녁을 먹었어요.",
  "example_2_romanization": "chin-guwa hamkke jeonyeogeul meogeosseoyo.",
  "example_2_vn": "Tôi đã ăn tối cùng bạn bè."
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
}''',
            "korean": '''{
  "pattern": "~아/어요",
  "romanization": "a/eoyo",
  "meaning": "dạng lịch sự thân mật (hiện tại)",
  "topik_level": "TOPIK I",
  "topic": "Kết thúc câu",
  "usage": "Động từ/tính từ + 아요/어요",
  "explanation": "Dạng kết thúc câu lịch sự thông dụng nhất trong giao tiếp.",
  "example": "지금 학교에 가요.",
  "example_romanization": "jigeum hakgyoe gayo.",
  "example_vn": "Bây giờ tôi đi học.",
  "example_2": "밥을 맛있게 먹어요.",
  "example_2_romanization": "babeul masitge meogeoyo.",
  "example_2_vn": "Tôi ăn cơm ngon lành."
}'''
        }

        raw = samples[self._current_lang]
        if self._is_grammar:
            raw = grammar_samples[self._current_lang]

        if isinstance(raw, dict):
            # Multiple sub-samples: show a combo to choose
            sub_keys = list(raw.keys())
            dlg = QDialog(self)
            dlg.setWindowTitle(t("sample_json_title", label=self._cfg()["label"]))
            dlg.setMinimumWidth(600)
            vl = QVBoxLayout(dlg)

            top_bar = QHBoxLayout()
            top_bar.addWidget(QLabel(t("choose_type_label")))
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

            btn_copy = QPushButton(t("btn_copy_close"))
            btn_copy.clicked.connect(lambda: (
                QApplication.clipboard().setText(te.toPlainText()),
                dlg.accept()
            ))
            vl.addWidget(btn_copy)
            dlg.exec()
        else:
            dlg = QDialog(self)
            dlg.setWindowTitle(t("sample_json_title", label=self._cfg()["label"]))
            dlg.setMinimumWidth(600)
            vl = QVBoxLayout(dlg)
            te = QPlainTextEdit()
            te.setReadOnly(True)
            te.setPlainText(raw)
            te.setStyleSheet("font-family:monospace;font-size:13px;")
            vl.addWidget(te)

            btn_copy = QPushButton(t("btn_copy_close"))
            btn_copy.clicked.connect(lambda: (
                QApplication.clipboard().setText(te.toPlainText()),
                dlg.accept()
            ))
            vl.addWidget(btn_copy)
            dlg.exec()

    def _load_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("file_dialog_title"), "", t("file_dialog_filter")
        )
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.json_input.setPlainText(f.read())
            except Exception as e:
                showInfo(t("err_file_read", error=e))

    def _schedule_analyze(self):
        """Debounced analyze — chỉ parse JSON khi user ngừng gõ 500ms."""
        self._analyze_timer.start()

    def _analyze_content(self):
        raw = self.json_input.toPlainText().strip()
        if not raw:
            self.raw_data = []
        else:
            self.raw_data = safe_parse_json(raw)

        self.lbl_raw.setText(t("filter_raw_count", count=len(self.raw_data)))

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

        # ── Build lookup: front_lower → notes (tránh N+1 query) ──
        front_to_notes = {}
        meaning_to_notes = {}
        if mid:
            try:
                all_nids = mw.col.find_notes(mid_filter)
                for nid in all_nids:
                    try:
                        note = mw.col.get_note(nid)
                        f = str(note.get(front_field, "")).strip().lower()
                        if f:
                            front_to_notes.setdefault(f, []).append(note)
                        m = str(note.get("Meaning", "")).strip().lower()
                        if m:
                            meaning_to_notes.setdefault(m, []).append(note)
                    except Exception:
                        continue
            except Exception:
                pass

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

            exact_notes = front_to_notes.get(front.lower(), [])
            if exact_notes:
                old = exact_notes[0]
                exact_ids = [old.id]
                updatable = self._find_updatable_fields(old, item)
                if updatable:
                    action, target_nid = "update", exact_ids[0]
                    cnt["update"] += 1
                else:
                    # 📘 Ngữ pháp: cùng pattern + KHÁC nghĩa → thẻ MỚI (biến thể cách dùng)
                    if getattr(self, '_is_grammar', False):
                        try:
                            _gm_existing_meaning = old["Meaning"].strip()
                        except Exception:
                            _gm_existing_meaning = ""
                        if _gm_existing_meaning and meaning and _gm_existing_meaning.lower() != meaning.lower():
                            cnt["new"] += 1
                            self._add_to_queue(item, "add", None, [], cnt)
                            continue
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
                same_mean = meaning_to_notes.get(meaning.lower(), [])
                if same_mean:
                    action = "add_partial"
                    cnt["partial"] += 1

            if action in ("add", "add_partial"):
                cnt["new"] += 1
            self._add_to_queue(item, action, target_nid, updatable, cnt, conflict_info)

        self.btn_diff_meaning.setEnabled(cnt["dup_diff"] > 0)
        self.lbl_ready.setText(
            f"✨ {cnt['new']} mới   🔄 {cnt['update']} cập nhật   "
            f"⚠️ {cnt['partial']} trùng mờ   🔍 {cnt['dup_diff']} nghĩa khác   ❌ {cnt['dup']} bỏ qua"
        )
        # Dựng lại danh sách thẻ chờ xuất xưởng (có tìm kiếm + lọc + checkbox)
        self._rebuild_preview()

    def _add_to_queue(self, item, action, nid, updatable, cnt, conflict_info=None):
        """Thêm thẻ vào hàng chờ xuất xưởng (prepared_data).
        Danh sách hiển thị được dựng lại ở cuối _verify_batch_impl qua _rebuild_preview()."""
        self.prepared_data.append({
            "item": item, "action": action,
            "nid": nid, "update_fields": updatable,
            "conflict_info": conflict_info,
        })

    # ═══════════════════════════════════════════════════════
    #  TÌM KIẾM / LỌC / CHỌN THẺ CHỜ XUẤT XƯỞNG
    # ═══════════════════════════════════════════════════════
    def _rebuild_preview(self):
        """Dựng lại danh sách thẻ chờ xuất xưởng theo tìm kiếm + bộ lọc.
        Mỗi dòng: checkbox + số thứ tự (theo danh sách đang hiển thị) + từ + nghĩa + ghi chú."""
        search = self.txt_search.text().strip().lower()
        filt = self.cbo_filter.currentText()
        action_map = {
            t("cbo_filter_all"): None,
            t("cbo_filter_new"): "add",
            t("cbo_filter_update"): "update",
            t("cbo_filter_conflict"): "add_partial",
            t("cbo_filter_diff"): "dup_diff",
        }
        want_action = action_map.get(filt)
        cfg = self._cfg()
        dk = cfg["detect_key"]

        # Lưu trạng thái check theo index để giữ qua mỗi lần dựng lại
        checked = set()
        for row in range(self.preview_list.count()):
            it = self.preview_list.item(row)
            if it.checkState() == Qt.CheckState.Checked:
                idx = it.data(Qt.ItemDataRole.UserRole)
                if idx is not None:
                    checked.add(idx)

        self._visible_indices = []
        for i, d in enumerate(self.prepared_data):
            item = d["item"]
            action = d["action"]
            front = str(item.get(dk, item.get('front', ''))).strip()
            meaning = str(item.get('meaning', '')).strip()
            if want_action and action != want_action:
                continue
            if search and search not in front.lower() and search not in meaning.lower():
                continue
            self._visible_indices.append(i)

        self.preview_list.blockSignals(True)
        self.preview_list.clear()
        for pos, idx in enumerate(self._visible_indices, start=1):
            d = self.prepared_data[idx]
            item = d["item"]
            action = d["action"]
            updatable = d.get("update_fields", [])
            ci = d.get("conflict_info")
            front = str(item.get(dk, item.get('front', ''))).strip()
            icon = {"add": "✨", "add_partial": "⚠️", "update": "🔄", "dup_diff": "🔍"}.get(action, "✨")
            if action == "dup_diff" and ci:
                suffix = t("preview_suffix_dup_diff",
                           new=item.get('meaning', ''), old=ci.get('existing_meaning', ''))
            elif action == "update" and updatable:
                suffix = t("preview_suffix_update", fields=", ".join(updatable))
            elif action == "add_partial":
                suffix = t("preview_suffix_partial")
            else:
                suffix = ""
            li = QListWidgetItem(f"{icon} {pos}: {front} — {item.get('meaning','')}{suffix}")
            li.setFlags(li.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            li.setCheckState(Qt.CheckState.Checked if idx in checked else Qt.CheckState.Unchecked)
            li.setData(Qt.ItemDataRole.UserRole, idx)
            self.preview_list.addItem(li)
        self.preview_list.blockSignals(False)

        # Khóa khoảng số theo số thẻ đang hiển thị
        # (bật cờ để không kích hoạt tự động tích chọn khi đang dựng lại danh sách)
        self._updating_range = True
        try:
            vis_count = len(self._visible_indices)
            if vis_count == 0:
                self.spin_start.setRange(1, 1)
                self.spin_end.setRange(1, 1)
                self.spin_start.setValue(1)
                self.spin_end.setValue(1)
            else:
                self.spin_start.setRange(1, vis_count)
                self.spin_end.setRange(1, vis_count)
                if self.spin_start.value() > vis_count:
                    self.spin_start.setValue(vis_count)
                if self.spin_end.value() > vis_count:
                    self.spin_end.setValue(vis_count)
                if self.spin_start.value() > self.spin_end.value():
                    self.spin_end.setValue(self.spin_start.value())
        finally:
            self._updating_range = False

        self.btn_import.setEnabled(len(self.prepared_data) > 0)
        self.btn_cancel_order.setEnabled(len(self.prepared_data) > 0)
        self._update_selection_label()

    def _on_range_changed(self):
        """Khi đổi khoảng 'Từ số … đến' → tự động tích chọn các thẻ trong khoảng đó."""
        if getattr(self, '_updating_range', False):
            return
        if not hasattr(self, 'preview_list'):
            return
        start = self.spin_start.value()
        end = self.spin_end.value()
        self.preview_list.blockSignals(True)
        for row in range(self.preview_list.count()):
            checked = (start <= row + 1 <= end)
            self.preview_list.item(row).setCheckState(
                Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            )
        self.preview_list.blockSignals(False)
        self._update_selection_label()

    def _update_selection_label(self):
        """Cập nhật nhãn số thẻ đã chọn."""
        if not hasattr(self, 'lbl_sel'):
            return
        n_checked = 0
        for row in range(self.preview_list.count()):
            if self.preview_list.item(row).checkState() == Qt.CheckState.Checked:
                n_checked += 1
        vis = len(getattr(self, '_visible_indices', []))
        self.lbl_sel.setText(t("lbl_sel_count", selected=n_checked, total=vis))

    def _select_all_visible(self):
        """Tích chọn tất cả thẻ đang hiển thị."""
        self.preview_list.blockSignals(True)
        for row in range(self.preview_list.count()):
            self.preview_list.item(row).setCheckState(Qt.CheckState.Checked)
        self.preview_list.blockSignals(False)
        self._update_selection_label()

    def _select_none_visible(self):
        """Bỏ chọn tất cả thẻ đang hiển thị."""
        self.preview_list.blockSignals(True)
        for row in range(self.preview_list.count()):
            self.preview_list.item(row).setCheckState(Qt.CheckState.Unchecked)
        self.preview_list.blockSignals(False)
        self._update_selection_label()

    def _get_export_indices(self):
        """Trả về các index (trong prepared_data) sẽ xuất xưởng.
        Ưu tiên các thẻ được tích chọn; nếu không chọn thẻ nào → dùng khoảng Từ-đến
        (theo danh sách đang hiển thị sau khi lọc)."""
        visible = getattr(self, '_visible_indices', None)
        if visible is None:
            visible = list(range(len(self.prepared_data)))
        checked = []
        for row in range(self.preview_list.count()):
            it = self.preview_list.item(row)
            if it.checkState() == Qt.CheckState.Checked:
                idx = it.data(Qt.ItemDataRole.UserRole)
                if idx is not None:
                    checked.append(idx)
        if checked:
            return sorted(set(checked))
        start = max(1, self.spin_start.value()) - 1
        end = min(len(visible), self.spin_end.value())
        if end < start:
            end = start
        return visible[start:end]

    def _remove_factory_indices(self, indices):
        """Xóa các thẻ (theo index trong prepared_data) khỏi xưởng (prepared_data + raw_data),
        rồi dựng lại danh sách và lưu trạng thái."""
        indices = sorted(set(indices))
        removed_items = []
        for i in sorted(indices, reverse=True):
            if 0 <= i < len(self.prepared_data):
                removed_items.append(self.prepared_data[i]["item"])
                del self.prepared_data[i]
        for it in removed_items:
            try:
                self.raw_data.remove(it)
            except ValueError:
                pass
        self.lbl_raw.setText(t("filter_raw_count", count=len(self.raw_data)))
        self.lbl_ready.setText(t("preview_ready", count=len(self.prepared_data)))
        self._rebuild_preview()
        self._save_current_flow()

    def _cancel_order(self):
        """Hủy hàng: xóa toàn bộ hoặc xóa các thẻ đã chọn khỏi xưởng.
        Thẻ chỉ bị xóa khi người dùng chủ động bấm nút này — không bị mất khi đóng cửa sổ."""
        if not self.prepared_data:
            tooltip("ℹ️ Xưởng trống — không có thẻ để hủy.")
            return
        export_indices = self._get_export_indices()
        n_sel = len(export_indices)
        box = QMessageBox(self)
        box.setWindowTitle("🧹 Hủy Hàng")
        box.setText(
            f"Xưởng hiện có {len(self.prepared_data)} thẻ chờ xuất xưởng.\n\n"
            f"☑️ Đã chọn: {n_sel} thẻ.\n\n"
            "Chọn thao tác xóa — chỉ xóa khỏi XƯỞNG, không ảnh hưởng đến Anki:"
        )
        btn_selected = box.addButton("🗑️ Xóa các thẻ đã chọn", QMessageBox.ButtonRole.ActionRole)
        btn_all = box.addButton("🧹 Xóa toàn bộ", QMessageBox.ButtonRole.ActionRole)
        btn_cancel = box.addButton("Hủy", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(btn_cancel)
        box.exec()
        clicked = box.clickedButton()
        if clicked == btn_selected:
            if n_sel == 0:
                tooltip("⚠️ Chưa chọn thẻ nào. Hãy tích chọn thẻ hoặc chỉnh khoảng Từ-đến.")
                return
            self._remove_factory_indices(export_indices)
            self.lbl_status.setText(f"🗑️ Đã xóa {n_sel} thẻ đã chọn khỏi xưởng.")
        elif clicked == btn_all:
            self._remove_factory_indices(list(range(len(self.prepared_data))))
            self.lbl_status.setText(t("status_cleared_factory"))

    def _show_diff_meaning_report(self):
        """Hiển thị dialog báo cáo các từ vựng có cùng mặt chữ nhưng khác nghĩa,
        cho phép người dùng chọn từ nào được phép thêm vào."""
        cfg = self._cfg()
        changed = show_diff_meaning_dialog(self, self.prepared_data, cfg)
        if not changed:
            return

        # Đếm lại
        remaining_dup_diff = sum(1 for d in self.prepared_data if d["action"] == "dup_diff")
        self.btn_diff_meaning.setEnabled(remaining_dup_diff > 0)
        self.lbl_ready.setText(t("preview_ready", count=len(self.prepared_data)))
        # Dựng lại danh sách theo bộ lọc/tìm kiếm hiện tại
        self._rebuild_preview()

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

        export_indices = self._get_export_indices()
        batch = [self.prepared_data[i] for i in export_indices]
        if not batch:
            tooltip("⚠️ Không có thẻ nào được chọn để xuất xưởng.")
            return

        # Lưu lại các index đã xuất để cập nhật lại xưởng sau khi import xong
        self._last_export_indices = list(export_indices)

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
        self.lbl_status.setText(t("status_done"))

        idxs = sorted(set(getattr(self, '_last_export_indices', None) or []))
        # Ghi nhận vào lịch sử import
        try:
            deck_name = self.deck_chooser.currentText()
            if report.get('added', 0) > 0:
                imported_items = [
                    self.prepared_data[i]["item"] for i in idxs
                    if 0 <= i < len(self.prepared_data)
                    and self.prepared_data[i]["action"] in ("add", "add_partial")
                ]
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

        # Cập nhật lại xưởng: xóa các thẻ đã xuất xưởng → danh sách giảm dần
        self._last_export_indices = None
        self._remove_factory_indices(idxs)

        msg = (
            f"🚀 XUẤT XƯỞNG V17.0 THÀNH CÔNG! [{self._cfg()['label']}]\n"
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
        # Không xóa thẻ khỏi xưởng khi import lỗi
        self._last_export_indices = None

    def _cancel_import(self):
        if self.import_worker and self.import_worker.isRunning():
            self.import_worker.stop()
            self.lbl_status.setText(t("status_stopping"))
            self.btn_cancel.setEnabled(False)

    def _drop_extra_combo_cards(self, mid, keep_count):
        """Migration combo: xóa các card thừa (ord >= keep_count) của model,
        giữ nguyên card mode chính (ord 0) + lịch sử học."""
        try:
            nids = mw.col.find_notes(f'"mid:{mid}"')
            if not nids:
                return
            card_ids = []
            for nid in nids:
                try:
                    card_ids.extend(
                        mw.col.db.list(
                            "select id from cards where nid=? and ord>=?",
                            nid, keep_count
                        )
                    )
                except Exception:
                    continue
            if card_ids:
                mw.col.remCards(card_ids)
                logger.info("Migration combo: xóa %d card thừa (model %s)", len(card_ids), mid)
        except Exception as e:
            logger.warning("Migration combo cards: %s", e)

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
            # Đảm bảo đủ field trước khi save (model cũ có thể thiếu field)
            existing = {f['name'] for f in m['flds']}

            def _ensure_fields(field_set):
                added = 0
                for fn in field_set:
                    if fn and fn not in existing:
                        mm.add_field(m, mm.new_field(fn))
                        existing.add(fn)
                        added += 1
                return added

            _ensure_fields(cfg["all_fields"])
            _ensure_fields(self._collect_template_fields(tmpls))
            for i in range(tmpl_count):
                if i < len(m['tmpls']):
                    # Mức 2: build_qfmt/build_afmt tự APPEND field tuỳ chỉnh (custom fields)
                    m['tmpls'][i]['qfmt'] = _build_qfmt(cfg, tmpls, i * 2)
                    m['tmpls'][i]['afmt'] = _build_afmt(cfg, tmpls, i * 2 + 1)
                else:
                    t = mm.new_template(cfg["template_names"][i])
                    t['qfmt'] = _build_qfmt(cfg, tmpls, i * 2)
                    t['afmt'] = _build_afmt(cfg, tmpls, i * 2 + 1)
                    mm.add_template(m, t)
            # Remove extra templates if model has more than needed
            had_extra = len(m['tmpls']) > tmpl_count
            while len(m['tmpls']) > tmpl_count:
                mm.remove_template(m, m['tmpls'][-1])
            mm.save(m)
            # Migration combo: xóa card thừa sau khi giảm template
            if had_extra and not self._is_grammar:
                self._drop_extra_combo_cards(m['id'], tmpl_count)
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

    @staticmethod
    def _collect_template_fields(tmpls):
        """Trích xuất mọi field name được tham chiếu trong template HTML.

        Hỗ trợ {{Field}}, {{#Field}}...{{/Field}}, {{^Field}}, {{type:Field}}.
        Đảm bảo model cũ luôn có đủ field khi migrate sang card combo.
        """
        fields = set()
        for fn in tmpls:
            try:
                html = fn()
            except Exception:
                continue
            for m in re.finditer(r"\{\{([#^/]?)([^{}\n]+?)\}\}", html):
                raw = m.group(2).strip()
                if raw.startswith("type:"):
                    raw = raw.split(":", 1)[1].strip()
                if raw and raw not in ("FrontSide", "Tags", "Deck", "Subdeck", "Card", "Type"):
                    fields.add(raw)
        return fields

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

            def _ensure_fields(field_set):
                """Thêm field còn thiếu vào model, cập nhật lại tập existing."""
                added = 0
                for fn in field_set:
                    if fn and fn not in existing:
                        mm.add_field(m, mm.new_field(fn))
                        existing.add(fn)
                        added += 1
                return added

            # 1) Đủ field cấu hình (json_field_map/all_fields)
            _ensure_fields(cfg["all_fields"])
            # 2) Đủ field template tham chiếu (model cũ có thể thiếu → CardTypeError khi save)
            _ensure_fields(self._collect_template_fields(tmpls))
            m['css'] = css
            had_extra = len(m['tmpls']) > tmpl_count
            for i in range(tmpl_count):
                if i < len(m['tmpls']):
                    # Mức 2: build_qfmt/build_afmt tự APPEND field tuỳ chỉnh (custom fields)
                    m['tmpls'][i]['qfmt'] = _build_qfmt(cfg, tmpls, i * 2)
                    m['tmpls'][i]['afmt'] = _build_afmt(cfg, tmpls, i * 2 + 1)
                else:
                    t = mm.new_template(cfg["template_names"][i])
                    t['qfmt'] = _build_qfmt(cfg, tmpls, i * 2)
                    t['afmt'] = _build_afmt(cfg, tmpls, i * 2 + 1)
                    mm.add_template(m, t)
            # Migration combo: đổi tên template đầu thành "Tổng hợp (5 chế độ)"
            if had_extra and not self._is_grammar and len(cfg["template_names"]) > 0:
                try:
                    m['tmpls'][0]['name'] = cfg["template_names"][0]
                except Exception:
                    pass
            # Remove extra templates if model has more than needed
            while len(m['tmpls']) > tmpl_count:
                mm.remove_template(m, m['tmpls'][-1])
            mm.save(m)
            # Migration combo: xóa card thừa sau khi giảm template
            if had_extra and not self._is_grammar:
                self._drop_extra_combo_cards(m['id'], tmpl_count)
            return m

        m = mm.new(name)
        for fn in cfg["all_fields"]:
            mm.add_field(m, mm.new_field(fn))
        for i in range(tmpl_count):
            t = mm.new_template(cfg["template_names"][i])
            t['qfmt'] = _build_qfmt(cfg, tmpls, i * 2)
            t['afmt'] = _build_afmt(cfg, tmpls, i * 2 + 1)
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
        """Xóa text input, file kẹp và reset trạng thái (lưu luồng rỗng)"""
        self.ai_text_input.clear()
        self.lbl_ai_status.setText("")
        self.lbl_ai_status.setStyleSheet("color:rgba(234,240,246,0.7);font-size:11px;font-weight:normal;")
        self._ai_attached_files = []
        self._ai_attached_paths = []
        self.lbl_ai_files.setText("")
        self._save_current_flow()

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
        self.lbl_ai_status.setText(t("status_reading_file"))
        mw.app.processEvents()

        new_files = []
        ok_paths = []
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
            ok_paths.append(p)
            combined_parts.append(f"===== 📄 FILE: {name} =====\n{text}")

        if not new_files:
            self.lbl_ai_status.setText("")
            showInfo(t("status_no_file_content", errors="\n".join(errors)))
            return

        self._ai_attached_files.extend(new_files)
        self._ai_attached_paths.extend(ok_paths)

        # Đưa nội dung file vào ô AI để làm tài liệu tham khảo
        combined = "\n\n".join(combined_parts)
        current = self.ai_text_input.toPlainText()
        if current.strip():
            self.ai_text_input.setPlainText(current.rstrip() + "\n\n" + combined)
        else:
            self.ai_text_input.setPlainText(combined)

        self._update_ai_files_label()
        self.lbl_ai_status.setText("")
        self._save_current_flow()

        if errors:
            tooltip(f"📎 Đã kẹp {len(new_files)} file.\n⚠️ Không đọc được:\n" + "\n".join(errors))
        else:
            tooltip(f"✅ Đã kẹp {len(new_files)} file làm tài liệu tham khảo!")

    def _clear_ai_files(self):
        """🧹 Bỏ toàn bộ file đã kẹp và xóa nội dung ô AI (lưu luồng rỗng)."""
        self._ai_attached_files = []
        self._ai_attached_paths = []
        self.ai_text_input.clear()
        self.lbl_ai_files.setText("")
        self._save_current_flow()
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
        self.lbl_ai_status.setText(t("status_scanning_deck"))
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
            self.lbl_ai_status.setText(t("status_calling_ai"))
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

        self.lbl_ai_status.setText(t("batch_status_error", error=error_msg[:80]))
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
                label = t("item_label_grammar_short") if self._is_grammar else t("item_label_vocab_short")
                self.lbl_ai_status.setText(t("status_batch_done", count=len(vocab_list), label=label))
                self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")
                # Đổ JSON vào text input để hiển thị trong xưởng
                import json as _json
                json_str = _json.dumps(vocab_list, indent=2, ensure_ascii=False)
                self.json_input.setPlainText(json_str)
                self.raw_data = list(vocab_list)
                self.lbl_raw.setText(t("filter_raw_count", count=len(self.raw_data)))
                # Mở preview dialog để người dùng xem và chỉnh sửa
                self._show_ai_preview(vocab_list)
            else:
                self.lbl_ai_status.setText(t("status_batch_empty"))
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

        # Bảo vệ context: cắt theo max_chars trong Cài Đặt AI (mặc định 45k), không cứng 30k
        _chat_cfg = get_api_config()
        _MAX_CHAT_CHARS = int(_chat_cfg.get("max_chars", 45000) or 45000)
        _MAX_CHAT_CHARS = max(10000, min(45000, _MAX_CHAT_CHARS))
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

        self.lbl_ai_status.setText(t("status_connecting_elapsed", elapsed="00:00", estimate=est_text))
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
        status_text = t("status_chat_done", elapsed=elapsed)
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
        self.lbl_ai_status.setText(t("status_chat_error", elapsed=elapsed, error=error_msg[:60]))
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
        self.lbl_ai_status.setText(t("status_stopped_ai", elapsed=elapsed))
        self.lbl_ai_status.setStyleSheet("color:#e67e22;font-size:11px;font-weight:bold;")
        tooltip(t("tooltip_stopped_ai"))

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

            self.lbl_ai_status.setText(t("status_poured_vocab", count=len(dlg.accepted_vocab)))
            self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")
            showInfo(t("msg_chat_poured", count=len(dlg.accepted_vocab)))

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
            grammar=self._is_grammar,
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

        self.lbl_ai_status.setText(t("status_poured_vocab", count=len(final_list)))
        self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")

        showInfo(t("msg_extract_poured", count=len(final_list)))

    # ═══════════════════════════════════════════════════════
    #  LỊCH SỬ AI — Xem lại & đưa vào xưởng để import lại
    # ═══════════════════════════════════════════════════════
    def _open_history_browser(self):
        """Mở dialog xem lịch sử từ vựng đã lưu (AI/import) và đưa lại vào xưởng."""
        from ui.history_dialog import HistoryBrowserDialog

        dlg = HistoryBrowserDialog(parent=self, current_lang=self._current_lang)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.accepted_items:
            self._load_history_to_factory(dlg.accepted_lang, dlg.accepted_items)

    def _load_history_to_factory(self, lang, items):
        """Đưa các từ đã chọn từ lịch sử vào xưởng (json_input + kho hàng) để kiểm định lại."""
        if not items:
            return
        if lang and lang in ("japanese", "chinese", "korean") and lang != self._current_lang:
            self._current_lang = lang
            self._on_lang_changed()
        json_str = json.dumps(items, indent=2, ensure_ascii=False)
        self.json_input.setPlainText(json_str)
        self._analyze_content()
        # Đảm bảo kho hàng đúng theo item đã chọn (an toàn nếu JSON parse lệch)
        self.raw_data = list(items)
        self.lbl_raw.setText(t("filter_raw_count", count=len(self.raw_data)))
        self.lbl_ai_status.setText(t("status_pulled_history", count=len(items)))
        self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")
        tooltip(t("tooltip_pulled_history", count=len(items)))


# ═══════════════════════════════════════════════════════════
#  REVIEWER HOOKS (wired → hooks/reviewer.py) + OVERVIEW MODE
# ═══════════════════════════════════════════════════════════
register_hooks()
register_overview_hooks()


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════
def start_smart_factory():
    mw.factory_dialog = AnkiSmartFactory(mw)
    mw.factory_dialog.show()


action = QAction("🌐 AnkiTool Multi-Lang V17.0", mw)
action.setShortcut(QKeySequence("Ctrl+Shift+I"))
qconnect(action.triggered, start_smart_factory)
mw.form.menuTools.addAction(action)

