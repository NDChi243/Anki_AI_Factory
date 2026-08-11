"""
Language package — supports Japanese, Chinese & Korean.
"""

from .japanese import LANG_CONFIG as _JA, GRAMMAR_CONFIG as _JA_G
from .chinese import LANG_CONFIG as _ZH, GRAMMAR_CONFIG as _ZH_G
from .korean import LANG_CONFIG as _KO, GRAMMAR_CONFIG as _KO_G

LANG_CONFIG = {
    "japanese": _JA,
    "chinese":  _ZH,
    "korean":   _KO,
}

# Cấu hình Note Type NGỮ PHÁP riêng cho từng ngôn ngữ
LANG_GRAMMAR_CONFIG = {
    "japanese": _JA_G,
    "chinese":  _ZH_G,
    "korean":   _KO_G,
}

LANG_KEYS = list(LANG_CONFIG.keys())

LANG_SELECTOR_INFO = [
    ("japanese", "🇯🇵 日本語", "JP"),
    ("chinese",  "🇨🇳 中文",   "CN"),
    ("korean",   "🇰🇷 한국어", "KR"),
]
