"""
AI Workers — Background threads for AI extract, AI chat, and audio preview.
"""

import os

from aqt import mw
from aqt.qt import QThread, pyqtSignal

from utils.logger import get_logger
from utils.i18n import t
from utils.ai_extractor import (
    extract_vocabulary_long_text,
    extract_grammar_long_text,
    chat_with_ai,
)

logger = get_logger()


class PreviewThread(QThread):
    """Thread preview giọng đọc Edge TTS."""

    done = pyqtSignal(str)  # filepath hoặc ""

    def __init__(self, text, voice_id, lang, speed=1.0):
        super().__init__()
        self.text = text
        self.voice_id = voice_id
        self.lang = lang
        self.speed = speed

    def run(self):
        try:
            from audio.tts import get_audio_edge_tts, _install_edge_tts
            from audio.engine import speed_to_edge_rate
            if not _install_edge_tts():
                self.done.emit("")
                return
            rate = speed_to_edge_rate(self.speed)
            tag = get_audio_edge_tts(self.text, self.voice_id, self.lang, rate=rate)
            if tag:
                filename = tag.replace("[sound:", "").replace("]", "")
                filepath = os.path.join(mw.col.media.dir(), filename)
                self.done.emit(filepath if os.path.exists(filepath) else "")
            else:
                self.done.emit("")
        except Exception as e:
            logger.warning("Preview error: %s", e)
            self.done.emit("")


class AiExtractThread(QThread):
    """Thread gọi AI trích xuất từ vựng."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, text, lang, custom_instruction="", existing_words=None, grammar=False):
        super().__init__()
        self.text = text
        self.lang = lang
        self.custom_instruction = custom_instruction
        self.existing_words = existing_words or []
        self.grammar = grammar

    def run(self):
        try:
            if self.existing_words:
                label = t("item_label_grammar_lower") if self.grammar else "words"
                self.progress.emit(t("status_deck_avoid", count=len(self.existing_words), label=label))

            if self.grammar:
                self.progress.emit(t("worker_progress_grammar"))
                result_list = extract_grammar_long_text(
                    self.text,
                    self.lang,
                    self.custom_instruction,
                    existing_patterns=self.existing_words,
                    progress_callback=lambda msg: self.progress.emit(msg),
                )
                empty_msg = t("empty_grammar")
            else:
                self.progress.emit(t("worker_progress_vocab"))
                result_list = extract_vocabulary_long_text(
                    self.text,
                    self.lang,
                    self.custom_instruction,
                    existing_words=self.existing_words,
                    progress_callback=lambda msg: self.progress.emit(msg),
                )
                empty_msg = t("empty_vocab")

            if not result_list:
                self.error.emit(empty_msg)
                return

            self.finished.emit(result_list)

        except Exception as e:
            self.error.emit(str(e))


class AiChatThread(QThread):
    """Thread gọi AI chat."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, message, lang, conversation_history=None):
        super().__init__()
        self.message = message
        self.lang = lang
        self.conversation_history = conversation_history
        self._is_running = True

    def run(self):
        try:
            self.progress.emit(t("worker_progress_context"))
            result = chat_with_ai(
                user_message=self.message,
                lang=self.lang,
                conversation_history=self.conversation_history,
                progress_callback=lambda msg: self.progress.emit(msg),
            )

            if not self._is_running:
                return

            if result.get("error"):
                self.error.emit(result["error"])
                return

            self.finished.emit(result)

        except Exception as e:
            if self._is_running:
                self.error.emit(str(e))

    def stop(self):
        self._is_running = False
