"""
Language package — supports Japanese & Chinese.
"""

from .japanese import LANG_CONFIG as _JA, GRAMMAR_CONFIG as _JA_G
from .chinese import LANG_CONFIG as _ZH, GRAMMAR_CONFIG as _ZH_G

LANG_CONFIG = {
    "japanese": _JA,
    "chinese":  _ZH,
}

# Cấu hình Note Type NGỮ PHÁP riêng cho từng ngôn ngữ
LANG_GRAMMAR_CONFIG = {
    "japanese": _JA_G,
    "chinese":  _ZH_G,
}

LANG_KEYS = list(LANG_CONFIG.keys())

LANG_SELECTOR_INFO = [
    ("japanese", "🇯🇵 日本語", "JP"),
    ("chinese",  "🇨🇳 中文",   "CN"),
]
