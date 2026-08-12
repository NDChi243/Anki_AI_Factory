"""
Batch Word List Dialog — UI cho việc paste và xử lý danh sách từ vựng lớn qua AI.
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QGroupBox, QSpinBox,
    QCheckBox, QProgressBar, QApplication, Qt,
)
from aqt.utils import tooltip

from utils.batch_processor import estimate_batch_cost, parse_word_list
from utils.ai_extractor import is_openrouter
from utils.i18n import t


class BatchWordListDialog(QDialog):
    """
    Dialog cho phép người dùng paste danh sách từ vựng lớn,
    cấu hình batch processing, và xem tiến trình.
    """

    def __init__(self, lang="japanese", existing_words=None, parent=None, grammar=False):
        super().__init__(parent)
        self.grammar = grammar
        item_label = t("item_label_grammar") if grammar else t("item_label_vocab")
        self.setWindowTitle(
            t("batch_title_grammar") if grammar else t("batch_title_vocab")
        )
        self.setMinimumSize(800, 700)
        self.resize(900, 800)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )

        self.lang = lang
        self.existing_words = existing_words or []
        self.result_vocab = None
        self._batch_thread = None
        self._deck_thread = None
        # Tự phát hiện OpenRouter → mặc định bật chế độ chậm (tránh rate limit 20 req/phút)
        self._is_openrouter = is_openrouter()
        self.slow_mode = self._is_openrouter

        self._setup_ui()
        self._update_estimate()

    def _setup_ui(self):
        vl = QVBoxLayout(self)

        # ── Header ──────────────────────────────────────────
        header = QHBoxLayout()
        lang_label = {
            "japanese": t("lang_japanese"),
            "chinese": t("lang_chinese"),
            "korean": t("lang_korean"),
        }.get(self.lang, t("lang_japanese"))
        item_label = t("item_label_grammar") if self.grammar else t("item_label_vocab")
        header.addWidget(QLabel(
            f"<h3>{t('batch_header_grammar') if self.grammar else t('batch_header_vocab')} ({lang_label})</h3>"
            + (f"<p style='color:#555;font-size:11px;'>{t('batch_desc_grammar')}</p>"
               if self.grammar else
               f"<p style='color:#555;font-size:11px;'>{t('batch_desc_vocab')}</p>")
        ))
        header.addStretch()
        vl.addLayout(header)

        # ── Format Guide ────────────────────────────────────
        if self.grammar:
            guide = QLabel(
                "<div style='background:#eaf2f8;border:1px solid #3498db;border-radius:8px;padding:12px;margin:8px 0;'>"
                f"{t('batch_format_grammar')}</div>"
            )
        else:
            guide = QLabel(
                "<div style='background:#eaf2f8;border:1px solid #3498db;border-radius:8px;padding:12px;margin:8px 0;'>"
                f"{t('batch_format_vocab')}</div>"
            )
        guide.setWordWrap(True)
        vl.addWidget(guide)

        # ── Text Input ──────────────────────────────────────
        if self.grammar:
            vl.addWidget(QLabel(t("batch_list_label_grammar")))
        else:
            vl.addWidget(QLabel(t("batch_list_label_vocab")))
        self.txt_input = QTextEdit()
        if self.grammar:
            self.txt_input.setPlaceholderText(t("batch_placeholder_grammar"))
        else:
            self.txt_input.setPlaceholderText(t("batch_placeholder_vocab"))
        self.txt_input.setMinimumHeight(200)
        self.txt_input.textChanged.connect(self._update_estimate)
        vl.addWidget(self.txt_input)

        # ── Settings ────────────────────────────────────────
        settings_grp = QGroupBox(t("batch_settings_grp"))
        settings_layout = QHBoxLayout()

        # Batch size
        settings_layout.addWidget(QLabel(t("batch_batch_size_label")))
        self.spin_batch = QSpinBox()
        self.spin_batch.setRange(30, 100)
        self.spin_batch.setValue(80)
        self.spin_batch.setToolTip(t("batch_batch_size_tip"))
        self.spin_batch.valueChanged.connect(self._update_estimate)
        settings_layout.addWidget(self.spin_batch)

        settings_layout.addSpacing(20)

        # Custom instruction
        settings_layout.addWidget(QLabel(t("batch_instruction_label")))
        self.txt_instruction = QTextEdit()
        self.txt_instruction.setPlaceholderText(t("batch_instruction_placeholder"))
        self.txt_instruction.setMaximumHeight(40)
        self.txt_instruction.setMinimumHeight(35)
        settings_layout.addWidget(self.txt_instruction, 1)

        settings_grp.setLayout(settings_layout)
        vl.addWidget(settings_grp)

        # ── Deck Organization ───────────────────────────────
        deck_grp = QGroupBox(t("batch_deck_grp"))
        deck_layout = QHBoxLayout()

        self.chk_auto_deck = QCheckBox(t("batch_chk_auto_deck"))
        self.chk_auto_deck.setToolTip(t("batch_chk_auto_deck_tip"))
        self.chk_auto_deck.setChecked(True)
        deck_layout.addWidget(self.chk_auto_deck)

        self.chk_create_decks = QCheckBox(t("batch_chk_create_decks"))
        self.chk_create_decks.setToolTip(t("batch_chk_create_decks_tip"))
        self.chk_create_decks.setChecked(False)
        deck_layout.addWidget(self.chk_create_decks)

        deck_layout.addStretch()
        deck_grp.setLayout(deck_layout)
        vl.addWidget(deck_grp)

        # ── OpenRouter Slow Mode ────────────────────────────
        if self._is_openrouter:
            slow_grp = QGroupBox(t("batch_openrouter_grp"))
            slow_layout = QHBoxLayout()
            self.chk_slow_mode = QCheckBox(t("batch_chk_slow_mode"))
            self.chk_slow_mode.setChecked(True)
            self.chk_slow_mode.setToolTip(t("batch_chk_slow_mode_tip"))
            self.chk_slow_mode.toggled.connect(self._update_estimate)
            slow_layout.addWidget(self.chk_slow_mode)
            slow_layout.addStretch()
            slow_grp.setLayout(slow_layout)
            vl.addWidget(slow_grp)

        # ── Estimate ────────────────────────────────────────
        self.lbl_estimate = QLabel(
            "<div style='background:#fef9e7;border:1px solid #f39c12;border-radius:8px;"
            "padding:10px;color:#7d6608;'>"
            f"{t('batch_estimate_hint')}</div>"
        )
        self.lbl_estimate.setWordWrap(True)
        vl.addWidget(self.lbl_estimate)

        # ── Progress ────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        vl.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("color:#555;font-size:11px;padding:4px;")
        vl.addWidget(self.lbl_status)

        # ── Buttons ─────────────────────────────────────────
        btn_layout = QHBoxLayout()

        btn_close = QPushButton(t("btn_close"))
        btn_close.setStyleSheet(
            "padding:10px 20px;background:#95a5a6;color:white;"
            "font-weight:bold;border-radius:8px;"
        )
        btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(btn_close)

        btn_layout.addStretch()

        self.btn_stop = QPushButton(t("btn_stop"))
        self.btn_stop.setStyleSheet(
            "padding:10px 20px;background:#e74c3c;color:white;"
            "font-weight:bold;border-radius:8px;"
        )
        self.btn_stop.clicked.connect(self._stop_processing)
        self.btn_stop.setVisible(False)
        btn_layout.addWidget(self.btn_stop)

        self.btn_process = QPushButton(t("btn_process_ai"))
        self.btn_process.setStyleSheet(
            "padding:10px 30px;background:#27ae60;color:white;"
            "font-weight:bold;border-radius:8px;font-size:14px;"
        )
        self.btn_process.clicked.connect(self._start_processing)
        btn_layout.addWidget(self.btn_process)

        vl.addLayout(btn_layout)

    def _update_estimate(self):
        """Cập nhật ước tính khi text thay đổi"""
        text = self.txt_input.toPlainText().strip()
        if not text:
            self.lbl_estimate.setText(
                "<div style='background:#fef9e7;border:1px solid #f39c12;border-radius:8px;"
                "padding:10px;color:#7d6608;'>"
                f"{t('batch_estimate_hint')}</div>"
            )
            return

        # Parse để đếm số từ
        words = parse_word_list(text, self.lang)
        word_count = len(words)
        batch_size = self.spin_batch.value()
        estimate = estimate_batch_cost(word_count, self.lang, batch_size)

        # Ước tính thời gian thực tế theo chế độ (OpenRouter slow = 3.2s/batch + thời gian AI phản hồi)
        batches = estimate["estimated_batches"]
        if self._is_openrouter and getattr(self, "chk_slow_mode", None) and self.chk_slow_mode.isChecked():
            delay_per_batch = 3.2
            est_seconds = int(batches * (delay_per_batch + 7))  # 3.2s delay + ~7s AI phản hồi
            time_note = t("batch_estimate_line_slow", seconds=est_seconds, batches=batches, sec=round(delay_per_batch + 7))
        else:
            est_seconds = estimate["estimated_time_seconds"]
            time_note = f"⏱ ~{est_seconds}s"

        self.lbl_estimate.setText(
            f"<div style='background:#fef9e7;border:1px solid #f39c12;border-radius:8px;"
            f"padding:10px;color:#7d6608;'>"
            f"{t('batch_estimate_line', total=estimate['total_words'], batches=batches, size=batch_size, cost=estimate['estimated_cost_usd'], seconds=est_seconds)} | "
            f"~{estimate['estimated_input_tokens']:,} input + "
            f"~{estimate['estimated_output_tokens']:,} output tokens"
            f"</div>"
        )

        # Enable/disable process button
        self.btn_process.setEnabled(word_count > 0)

    def _start_processing(self):
        """Bắt đầu xử lý batch"""
        text = self.txt_input.toPlainText().strip()
        if not text:
            tooltip(t("tooltip_enter_vocab_list"))
            return

        # Disable UI
        self._set_ui_enabled(False)
        self.btn_process.setVisible(False)
        self.btn_stop.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.lbl_status.setText(t("batch_status_preparing"))

        # Start thread — truyền slow_mode nếu checkbox OpenRouter tồn tại
        from workers.batch_workers import BatchProcessThread

        if self._is_openrouter and hasattr(self, "chk_slow_mode"):
            self.slow_mode = self.chk_slow_mode.isChecked()

        self._batch_thread = BatchProcessThread(
            raw_text=text,
            lang=self.lang,
            custom_instruction=self.txt_instruction.toPlainText().strip(),
            existing_words=self.existing_words,
            batch_size=self.spin_batch.value(),
            grammar=self.grammar,
            slow_mode=self.slow_mode,
        )
        self._batch_thread.progress.connect(self._on_progress)
        self._batch_thread.finished.connect(self._on_batch_finished)
        self._batch_thread.error.connect(self._on_error)
        self._batch_thread.start()

    def _on_progress(self, msg):
        self.lbl_status.setText(msg)
        QApplication.processEvents()

    def _on_batch_finished(self, vocab_list):
        """Batch processing hoàn tất"""
        self.result_vocab = vocab_list
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        label = t("item_label_grammar_lower") if self.grammar else t("item_label_vocab_lower")
        self.lbl_status.setText(t("batch_status_finished", count=len(vocab_list), label=label))

        # Nếu chọn auto organize deck
        if self.chk_auto_deck.isChecked() and vocab_list:
            self._start_deck_organization(vocab_list)
        else:
            self._finish_processing()

    def _start_deck_organization(self, vocab_list):
        """Bắt đầu AI tổ chức deck"""
        self.lbl_status.setText(t("batch_status_organizing"))
        self.progress_bar.setRange(0, 0)  # Indeterminate again

        from workers.batch_workers import DeckOrganizerThread

        self._deck_thread = DeckOrganizerThread(
            vocab_list=vocab_list,
            lang=self.lang,
            auto_create=self.chk_create_decks.isChecked(),
        )
        self._deck_thread.progress.connect(self._on_progress)
        self._deck_thread.finished.connect(self._on_deck_organized)
        self._deck_thread.decks_created.connect(self._on_decks_created)
        self._deck_thread.error.connect(self._on_error)
        self._deck_thread.start()

    def _on_deck_organized(self, organization):
        """Deck organization hoàn tất"""
        suggestion = organization.get("suggestion", "")
        total_parents = len(organization.get("decks", []))
        total_subs = sum(len(p.get("sub_decks", [])) for p in organization.get("decks", []))

        msg = t("batch_status_organized", parents=total_parents, subs=total_subs)
        if suggestion:
            msg += f"\n💡 {suggestion}"

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.lbl_status.setText(msg)

        if not self.chk_create_decks.isChecked():
            self._finish_processing()

    def _on_decks_created(self, created_decks):
        """Decks đã được tạo trong Anki"""
        self.lbl_status.setText(
            t("batch_status_decks_created", count=len(created_decks),
              names="\n".join(f"📁 {name}" for name in list(created_decks.keys())[:10])
              + ("\n..." if len(created_decks) > 10 else ""))
        )
        tooltip(t("tooltip_decks_created", count=len(created_decks)))
        self._finish_processing()

    def _on_error(self, error_msg):
        """Xử lý lỗi"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.lbl_status.setText(t("batch_status_error", error=error_msg))
        self.lbl_status.setStyleSheet("color:#e74c3c;font-size:11px;padding:4px;")
        self._finish_processing()

    def _finish_processing(self):
        """Khôi phục UI sau khi hoàn tất"""
        self._set_ui_enabled(True)
        self.btn_process.setVisible(True)
        self.btn_stop.setVisible(False)
        if self.result_vocab:
            label = t("item_label_grammar_short") if self.grammar else t("item_label_vocab_short")
            self.btn_process.setText(t("batch_done_button", count=len(self.result_vocab), label=label))
            self.btn_process.setStyleSheet(
                "padding:10px 30px;background:#3498db;color:white;"
                "font-weight:bold;border-radius:8px;font-size:14px;"
            )
            # Disconnect old, connect new
            try:
                self.btn_process.clicked.disconnect()
            except Exception:
                pass
            self.btn_process.clicked.connect(self.accept)  # Accept dialog → return vocab

    def _stop_processing(self):
        """Dừng xử lý"""
        if self._batch_thread and self._batch_thread.isRunning():
            self._batch_thread.stop()
        if self._deck_thread and self._deck_thread.isRunning():
            self._deck_thread.stop()
        self.lbl_status.setText(t("batch_status_stopped"))
        self._finish_processing()

    def _set_ui_enabled(self, enabled):
        """Enable/disable UI controls"""
        self.txt_input.setEnabled(enabled)
        self.spin_batch.setEnabled(enabled)
        self.txt_instruction.setEnabled(enabled)
        self.chk_auto_deck.setEnabled(enabled)
        self.chk_create_decks.setEnabled(enabled)
        self.btn_process.setEnabled(enabled)

    def get_result_vocab(self):
        """Trả về danh sách từ vựng đã xử lý"""
        return self.result_vocab
