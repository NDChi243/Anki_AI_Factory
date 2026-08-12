"""
AI Dialogs — AiChatDialog hiển thị phản hồi AI chat.
"""

import re

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextBrowser, QGroupBox, QTableWidget,
    QTableWidgetItem, QApplication, Qt,
)
from aqt.utils import tooltip

from utils.i18n import t


class AiChatDialog(QDialog):
    """Dialog hiển thị phản hồi chat từ AI, có thể chứa từ vựng JSON"""

    def __init__(self, reply_text="", vocab_json=None, error=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("dlg_ai_chat"))
        self.setMinimumSize(700, 500)
        self.resize(850, 650)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )

        self.accepted_vocab = None
        self._vocab_json = vocab_json

        self._setup_ui(reply_text, error)

    def _setup_ui(self, reply_text, error):
        vl = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel(
            f"<h3>{t('chat_header_title')}</h3>"
            f"<p style='color:#555;font-size:11px;'>{t('chat_header_sub')}</p>"
        ))
        header.addStretch()
        vl.addLayout(header)

        if error:
            # Hiển thị lỗi
            err_lbl = QLabel(
                f"<div style='background:#fde8e8;border:1px solid #e74c3c;"
                f"border-radius:8px;padding:15px;color:#c0392b;'>"
                f"{t('chat_error_html', error=error)}</div>"
            )
            err_lbl.setWordWrap(True)
            vl.addWidget(err_lbl)
        else:
            # Text browser cho reply — màu tường minh để không bị trùng theme
            self.text_browser = QTextBrowser()
            self.text_browser.setOpenExternalLinks(True)
            self.text_browser.setStyleSheet(
                "QTextBrowser {"
                "  font-size: 13px;"
                "  line-height: 1.6;"
                "  background-color: #ffffff;"
                "  color: #1a1a1a;"
                "  border: 1px solid #ddd;"
                "  border-radius: 6px;"
                "  padding: 8px;"
                "}"
            )
            self.text_browser.setHtml(self._format_reply(reply_text))
            vl.addWidget(self.text_browser)

        # Vocab section
        if self._vocab_json and len(self._vocab_json) > 0:
            vocab_grp = QGroupBox(t("chat_vocab_group", count=len(self._vocab_json)))
            vocab_grp.setStyleSheet(
                "QGroupBox{font-weight:bold;font-size:13px;color:#27ae60;"
                "border:2px solid #27ae60;border-radius:8px;padding:10px;margin-top:10px;}"
            )
            vocab_layout = QVBoxLayout()

            lbl_hint = QLabel(
                f"<span style='color:#555;'>{t('chat_vocab_hint')}</span>"
            )
            lbl_hint.setWordWrap(True)
            vocab_layout.addWidget(lbl_hint)

            # Table preview
            table = QTableWidget()
            table.setAlternatingRowColors(True)

            # Xác định cột
            if self._vocab_json[0].get("simplified"):
                columns = ["simplified", "traditional", "pinyin", "meaning", "hsk_level", "topic"]
            else:
                columns = ["front", "furigana", "meaning", "jlptlevel", "topic"]

            display_cols = [c for c in columns if any(c in v for v in self._vocab_json)]

            table.setColumnCount(len(display_cols))
            table.setHorizontalHeaderLabels(display_cols)
            table.setRowCount(len(self._vocab_json))

            for row, item in enumerate(self._vocab_json):
                for col, key in enumerate(display_cols):
                    val = str(item.get(key, ""))
                    table.setItem(row, col, QTableWidgetItem(val))

            table.resizeColumnsToContents()
            table.horizontalHeader().setStretchLastSection(True)
            table.setMaximumHeight(200)
            vocab_layout.addWidget(table)
            vocab_grp.setLayout(vocab_layout)
            vl.addWidget(vocab_grp)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_close = QPushButton(t("chat_close"))
        btn_close.setStyleSheet(
            "padding:10px 20px;background:#95a5a6;color:white;"
            "font-weight:bold;border-radius:8px;"
        )
        btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(btn_close)

        btn_layout.addStretch()

        if self._vocab_json and len(self._vocab_json) > 0:
            btn_accept = QPushButton(t("chat_accept", count=len(self._vocab_json)))
            btn_accept.setStyleSheet(
                "padding:10px 25px;background:#27ae60;color:white;"
                "font-weight:bold;border-radius:8px;font-size:13px;"
            )
            btn_accept.clicked.connect(self._accept_vocab)
            btn_layout.addWidget(btn_accept)

        btn_copy = QPushButton(t("chat_copy"))
        btn_copy.setStyleSheet(
            "padding:10px 16px;background:#3498db;color:white;"
            "font-weight:bold;border-radius:8px;"
        )
        btn_copy.clicked.connect(lambda: (
            QApplication.clipboard().setText(
                self.text_browser.toPlainText() if hasattr(self, 'text_browser') else ""
            ),
            tooltip(t("chat_copied_tip"))
        ))
        btn_layout.addWidget(btn_copy)

        vl.addLayout(btn_layout)

    def _accept_vocab(self):
        """Chấp nhận từ vựng và đóng dialog"""
        self.accepted_vocab = self._vocab_json
        self.accept()

    @staticmethod
    def _format_reply(text: str) -> str:
        """Format reply text thành HTML đẹp"""
        if not text:
            return f"<p style='color:#999;'><i>{t('chat_no_reply')}</i></p>"

        # Escape HTML
        text = text.replace("&", "&").replace("<", "<").replace(">", ">")

        # Format bold (**text**)
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

        # Format code (`text`)
        text = re.sub(r'`([^`]+)`', r'<code style="background:#f0f0f0;padding:2px 6px;border-radius:3px;">\1</code>', text)

        # Format newlines
        text = text.replace("\n", "<br>")

        # Format bullet points
        text = re.sub(r'(?:^|<br>)- (.+?)(?:<br>|$)', r'<br>• \1', text)
        text = re.sub(r'(?:^|<br>)\d+\.\s+(.+?)(?:<br>|$)', r'<br>🔹 \1', text)

        # Wrap
        return (
            f"<div style='font-size:13px;line-height:1.7;color:#333;padding:10px;'>"
            f"{text}</div>"
        )
