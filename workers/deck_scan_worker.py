"""
Deck Scan Worker — Background thread quét deck Anki không chặn UI.
"""

from aqt import mw
from aqt.qt import QThread, pyqtSignal

from utils.ai_extractor import get_existing_vocab_from_deck
from utils.logger import get_logger
from utils.i18n import t

logger = get_logger()


class DeckScanWorker(QThread):
    """Quét deck Anki trong background thread để lấy danh sách từ hiện có."""

    progress = pyqtSignal(str)       # status message
    finished = pyqtSignal(list)       # list of existing words
    error = pyqtSignal(str)           # error message

    def __init__(self, model_name: str, deck_id: int, front_field: str):
        super().__init__()
        self.model_name = model_name
        self.deck_id = deck_id
        self.front_field = front_field

    def run(self):
        try:
            self.progress.emit(t("status_scanning_deck"))
            words = get_existing_vocab_from_deck(
                self.model_name, self.deck_id, self.front_field
            )
            if words:
                self.progress.emit(t("status_deck_count", count=len(words)))
            else:
                self.progress.emit(t("worker_progress_empty_deck"))
            self.finished.emit(words)
        except Exception as e:
            logger.warning("DeckScanWorker error: %s", e)
            self.error.emit(str(e))
