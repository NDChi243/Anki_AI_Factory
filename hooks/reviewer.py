"""
Hooks package — Reviewer hooks for AnkiTool.
"""

from aqt import gui_hooks

from audio.engine import detect_lang_from_model, get_default_speed
from mode import _SPEED_CTRL_JS, _LG_JS_BODY


def _on_reviewer_question(reviewer):
    """Inject Letter Gap JS khi hiện mặt trước thẻ."""
    try:
        card = reviewer.card
        if card and 'id="lg-display"' in (card.q() or ""):
            reviewer.web.eval(_LG_JS_BODY)
    except Exception:
        pass


def _on_reviewer_answer(reviewer):
    """Inject Speed Control JS khi hiện mặt sau thẻ."""
    # Bước 1: Xác định tốc độ mặc định
    default_spd = 1.0
    try:
        card = reviewer.card
        if card is not None:
            note = card.note()
            if note is not None:
                model = note.model()
                if model is not None:
                    lang = detect_lang_from_model(model['name'])
                    if lang:
                        default_spd = get_default_speed(lang)
    except Exception:
        pass

    # Bước 2: Inject JS tốc độ
    try:
        reviewer.web.eval(f"window._ankiDefaultSpeed={default_spd};" + _SPEED_CTRL_JS)
    except Exception:
        pass


def register_hooks():
    """Đăng ký tất cả reviewer hooks."""
    try:
        gui_hooks.reviewer_did_show_question.append(_on_reviewer_question)
        gui_hooks.reviewer_did_show_answer.append(_on_reviewer_answer)
    except Exception:
        pass
