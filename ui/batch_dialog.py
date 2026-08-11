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


class BatchWordListDialog(QDialog):
    """
    Dialog cho phép người dùng paste danh sách từ vựng lớn,
    cấu hình batch processing, và xem tiến trình.
    """

    def __init__(self, lang="japanese", existing_words=None, parent=None, grammar=False):
        super().__init__(parent)
        self.grammar = grammar
        item_label = "Cấu Trúc Ngữ Pháp" if grammar else "Từ Vựng"
        self.setWindowTitle(f"🚀 Xử Lý Danh Sách {item_label} Lớn — Batch AI")
        self.setMinimumSize(800, 650)
        self.resize(900, 750)
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

        self._setup_ui()
        self._update_estimate()

    def _setup_ui(self):
        vl = QVBoxLayout(self)

        # ── Header ──────────────────────────────────────────
        header = QHBoxLayout()
        lang_label = {
            "japanese": "🇯🇵 Tiếng Nhật",
            "chinese": "🇨🇳 Tiếng Trung",
            "korean": "🇰🇷 Tiếng Hàn",
        }.get(self.lang, "🇯🇵 Tiếng Nhật")
        item_label = "Cấu Trúc Ngữ Pháp" if self.grammar else "Từ Vựng"
        header.addWidget(QLabel(
            f"<h3>🚀 Xử Lý Danh Sách {item_label} Lớn ({lang_label})</h3>"
            + ("<p style='color:#555;font-size:11px;'>"
               "Paste danh sách cấu trúc ngữ pháp cần xử lý. AI sẽ làm giàu từng cấu trúc với nghĩa, công thức, cách dùng, ví dụ.</p>"
               if self.grammar else
               "<p style='color:#555;font-size:11px;'>"
               "Paste danh sách từ cần xử lý. AI sẽ làm giàu từng từ với đầy đủ nghĩa, phát âm, ví dụ, chủ đề.</p>")
        ))
        header.addStretch()
        vl.addLayout(header)

        # ── Format Guide ────────────────────────────────────
        if self.grammar:
            guide = QLabel(
                "<div style='background:#eaf2f8;border:1px solid #3498db;border-radius:8px;padding:12px;margin:8px 0;'>"
                "<b>📋 Format hỗ trợ (mỗi dòng 1 cấu trúc):</b><br>"
                "• <code>〜てもいい</code> — chỉ cấu trúc<br>"
                "• <code>〜てもいい : được phép</code> — cấu trúc + nghĩa<br>"
                "• <code>〜てもいい : được phép : N5</code> — + cấp độ<br>"
                "• JSON array: <code>[{{\"pattern\":\"〜てもいい\",\"meaning\":\"được phép\"}},...]</code><br>"
                "<b>💡 Tip:</b> Bạn có thể paste hàng trăm cấu trúc. "
                "AI sẽ tự động chia batch và xử lý tuần tự."
                "</div>"
            )
        else:
            guide = QLabel(
                "<div style='background:#eaf2f8;border:1px solid #3498db;border-radius:8px;padding:12px;margin:8px 0;'>"
                "<b>📋 Format hỗ trợ (mỗi dòng 1 từ):</b><br>"
                "• <code>食べる</code> — chỉ từ<br>"
                "• <code>食べる : ăn</code> — từ + nghĩa<br>"
                "• <code>食べる : ăn : N5</code> — từ + nghĩa + cấp độ<br>"
                "• <code>食べる, たべる, ăn, N5</code> — CSV<br>"
                "• JSON array: <code>[{{\"front\":\"食べる\",\"meaning\":\"ăn\"}},...]</code><br>"
                "<b>💡 Tip:</b> Bạn có thể paste hàng trăm, thậm chí hàng nghìn từ. "
                "AI sẽ tự động chia batch và xử lý tuần tự."
                "</div>"
            )
        guide.setWordWrap(True)
        vl.addWidget(guide)

        # ── Text Input ──────────────────────────────────────
        if self.grammar:
            vl.addWidget(QLabel("<b>📝 Danh sách cấu trúc ngữ pháp:</b>"))
        else:
            vl.addWidget(QLabel("<b>📝 Danh sách từ vựng:</b>"))
        self.txt_input = QTextEdit()
        if self.grammar:
            self.txt_input.setPlaceholderText(
                "Paste danh sách cấu trúc ngữ pháp vào đây...\n\n"
                "Ví dụ:\n"
                "〜てもいい : được phép : N5\n"
                "〜そうです : nghe nói / có vẻ : N4\n"
                "〜ことにする : quyết định : N4\n"
                "...\n"
            )
        else:
            self.txt_input.setPlaceholderText(
                "Paste danh sách từ vựng vào đây...\n\n"
                "Ví dụ:\n"
                "食べる : ăn : N5\n"
                "飲む : uống : N5\n"
                "勉強する : học : N5\n"
                "...\n"
            )
        self.txt_input.setMinimumHeight(200)
        self.txt_input.textChanged.connect(self._update_estimate)
        vl.addWidget(self.txt_input)

        # ── Settings ────────────────────────────────────────
        settings_grp = QGroupBox("⚙️ Cấu hình xử lý")
        settings_layout = QHBoxLayout()

        # Batch size
        settings_layout.addWidget(QLabel("Số từ/batch:"))
        self.spin_batch = QSpinBox()
        self.spin_batch.setRange(30, 100)
        self.spin_batch.setValue(80)
        self.spin_batch.setToolTip("Số từ mỗi lần gửi AI. Nhỏ hơn = chất lượng cao hơn nhưng chậm hơn.")
        self.spin_batch.valueChanged.connect(self._update_estimate)
        settings_layout.addWidget(self.spin_batch)

        settings_layout.addSpacing(20)

        # Custom instruction
        settings_layout.addWidget(QLabel("Yêu cầu thêm:"))
        self.txt_instruction = QTextEdit()
        self.txt_instruction.setPlaceholderText("VD: Chỉ lấy từ N3 trở lên, tập trung vào chủ đề kinh doanh...")
        self.txt_instruction.setMaximumHeight(40)
        self.txt_instruction.setMinimumHeight(35)
        settings_layout.addWidget(self.txt_instruction, 1)

        settings_grp.setLayout(settings_layout)
        vl.addWidget(settings_grp)

        # ── Deck Organization ───────────────────────────────
        deck_grp = QGroupBox("📦 Tổ chức Deck (tự động)")
        deck_layout = QHBoxLayout()

        self.chk_auto_deck = QCheckBox("🤖 AI tự đề xuất & tạo Parent/Sub Deck")
        self.chk_auto_deck.setToolTip(
            "Sau khi xử lý từ vựng, AI sẽ phân tích tất cả từ và đề xuất "
            "cấu trúc deck (parent deck + sub decks) theo chủ đề, cấp độ."
        )
        self.chk_auto_deck.setChecked(True)
        deck_layout.addWidget(self.chk_auto_deck)

        self.chk_create_decks = QCheckBox("📁 Tự động tạo deck trong Anki")
        self.chk_create_decks.setToolTip("Tự động tạo các deck được đề xuất trong Anki.")
        self.chk_create_decks.setChecked(False)
        deck_layout.addWidget(self.chk_create_decks)

        deck_layout.addStretch()
        deck_grp.setLayout(deck_layout)
        vl.addWidget(deck_grp)

        # ── Estimate ────────────────────────────────────────
        self.lbl_estimate = QLabel(
            "<div style='background:#fef9e7;border:1px solid #f39c12;border-radius:8px;"
            "padding:10px;color:#7d6608;'>"
            "📊 <b>Ước tính:</b> Nhập danh sách từ ở trên để xem ước tính.</div>"
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

        btn_close = QPushButton("❌ Đóng")
        btn_close.setStyleSheet(
            "padding:10px 20px;background:#95a5a6;color:white;"
            "font-weight:bold;border-radius:8px;"
        )
        btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(btn_close)

        btn_layout.addStretch()

        self.btn_stop = QPushButton("⏹ Dừng")
        self.btn_stop.setStyleSheet(
            "padding:10px 20px;background:#e74c3c;color:white;"
            "font-weight:bold;border-radius:8px;"
        )
        self.btn_stop.clicked.connect(self._stop_processing)
        self.btn_stop.setVisible(False)
        btn_layout.addWidget(self.btn_stop)

        self.btn_process = QPushButton("🚀 Xử Lý Với AI")
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
                "📊 <b>Ước tính:</b> Nhập danh sách từ ở trên để xem ước tính.</div>"
            )
            return

        # Parse để đếm số từ
        words = parse_word_list(text, self.lang)
        word_count = len(words)
        batch_size = self.spin_batch.value()
        estimate = estimate_batch_cost(word_count, self.lang, batch_size)

        self.lbl_estimate.setText(
            f"<div style='background:#fef9e7;border:1px solid #f39c12;border-radius:8px;"
            f"padding:10px;color:#7d6608;'>"
            f"📊 <b>Ước tính:</b> {estimate['total_words']} từ → "
            f"~{estimate['estimated_batches']} batch "
            f"({batch_size} từ/batch) | "
            f"~${estimate['estimated_cost_usd']:.4f} USD | "
            f"~{estimate['estimated_time_seconds']}s | "
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
            tooltip("⚠️ Vui lòng nhập danh sách từ vựng.")
            return

        # Disable UI
        self._set_ui_enabled(False)
        self.btn_process.setVisible(False)
        self.btn_stop.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.lbl_status.setText("⏳ Đang chuẩn bị...")

        # Start thread
        from workers.batch_workers import BatchProcessThread

        self._batch_thread = BatchProcessThread(
            raw_text=text,
            lang=self.lang,
            custom_instruction=self.txt_instruction.toPlainText().strip(),
            existing_words=self.existing_words,
            batch_size=self.spin_batch.value(),
            grammar=self.grammar,
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
        label = "cấu trúc ngữ pháp" if self.grammar else "từ vựng"
        self.lbl_status.setText(f"✅ Hoàn tất! {len(vocab_list)} {label} đã được AI xử lý.")

        # Nếu chọn auto organize deck
        if self.chk_auto_deck.isChecked() and vocab_list:
            self._start_deck_organization(vocab_list)
        else:
            self._finish_processing()

    def _start_deck_organization(self, vocab_list):
        """Bắt đầu AI tổ chức deck"""
        self.lbl_status.setText("🧠 AI đang phân tích và tổ chức deck...")
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

        msg = f"✅ Đã phân tích xong! {total_parents} parent deck, {total_subs} sub deck."
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
            f"✅ Đã tạo {len(created_decks)} deck trong Anki!\n"
            + "\n".join(f"📁 {name}" for name in list(created_decks.keys())[:10])
            + ("\n..." if len(created_decks) > 10 else "")
        )
        tooltip(f"✅ Đã tạo {len(created_decks)} deck!")
        self._finish_processing()

    def _on_error(self, error_msg):
        """Xử lý lỗi"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.lbl_status.setText(f"❌ Lỗi: {error_msg}")
        self.lbl_status.setStyleSheet("color:#e74c3c;font-size:11px;padding:4px;")
        self._finish_processing()

    def _finish_processing(self):
        """Khôi phục UI sau khi hoàn tất"""
        self._set_ui_enabled(True)
        self.btn_process.setVisible(True)
        self.btn_stop.setVisible(False)
        if self.result_vocab:
            label = "cấu trúc" if self.grammar else "từ"
            self.btn_process.setText(f"✅ Hoàn tất ({len(self.result_vocab)} {label}) — Xem Kết Quả")
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
        self.lbl_status.setText("⏹️ Đã dừng xử lý.")
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
