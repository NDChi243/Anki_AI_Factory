"""
UI package — Dialogs and widgets for AnkiTool.
"""

from .ai_dialogs import AiChatDialog
from .ai_settings import show_ai_settings_dialog
from .verify_dialog import show_diff_meaning_dialog
from .ai_preview import show_ai_preview_dialog
from .batch_dialog import BatchWordListDialog
from .deck_manager_dialog import DeckManagerDialog
from .history_dialog import HistoryBrowserDialog
from .prompt_editor import show_prompt_editor_dialog

__all__ = [
    "AiChatDialog",
    "show_ai_settings_dialog",
    "show_diff_meaning_dialog",
    "show_ai_preview_dialog",
    "BatchWordListDialog",
    "DeckManagerDialog",
    "HistoryBrowserDialog",
    "show_prompt_editor_dialog",
]
