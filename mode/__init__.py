"""
Japanese card mode package.

Exports the template, CSS, and shared reviewer helpers used by the add-on.
"""

from .css import LANG_CSS, LANG_GRAMMAR_CSS
from .templates import LANG_TEMPLATES, LANG_GRAMMAR_TEMPLATES
from .shared import _HW_CSS, _WB_JS_BODY, _HW_JS_BODY, WB_POOLS, _SHARED_UI_CSS, _SPEED_CTRL_JS, _LG_JS_BODY, _COMBO_MODE_JS

__all__ = [
    "LANG_CSS",
    "LANG_TEMPLATES",
    "LANG_GRAMMAR_CSS",
    "LANG_GRAMMAR_TEMPLATES",
    "_HW_CSS",
    "_WB_JS_BODY",
    "_HW_JS_BODY",
    "WB_POOLS",
    "_SHARED_UI_CSS",
    "_SPEED_CTRL_JS",
    "_LG_JS_BODY",
    "_COMBO_MODE_JS",
]
