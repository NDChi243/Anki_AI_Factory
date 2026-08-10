"""
Card CSS — Japanese & Chinese with shared base.
"""

from .shared import _HW_CSS, _SHARED_UI_CSS


# ═══════════════════════════════════════════════════════════
#  BASE CSS — Shared between Japanese & Chinese
# ═══════════════════════════════════════════════════════════
_BASE_CSS = '''
.card.nightMode {
    --bg:#141418;--card-bg:#1e1e26;--border:#2e2e3a;--text:#e8e6f0;
    --muted:#888898;--accent:#e05c4b;--accent-soft:#2e1a18;
    --accent2:#4fa3d1;--accent2-soft:#162030;
    --ex-bg:#1a1a22;--ex-border:#333348;--shadow:0 4px 24px rgba(0,0,0,0.4);
}
body{background:var(--bg);margin:0;padding:12px;}
.cw{background:var(--card-bg);border:1px solid var(--border);border-radius:var(--r);box-shadow:var(--shadow);max-width:560px;margin:16px auto;overflow:hidden;}
.ch{padding:6px 18px;display:flex;justify-content:space-between;align-items:center;}
.ch .badge{color:rgba(255,255,255,.92);font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;}
.ch .topic{color:rgba(255,255,255,.72);font-size:12px;}
.vb{text-align:center;padding:28px 24px 16px;}
.az{text-align:center;padding:0 24px 14px;}
.az input{border:2px solid var(--border);border-radius:8px;padding:8px 14px;font-size:17px;background:var(--bg);color:var(--text);outline:none;width:75%;}
.az input:focus{border-color:var(--accent2);}
.ir{display:flex;align-items:center;justify-content:center;gap:18px;padding:12px 24px;border-top:1px solid var(--border);border-bottom:1px solid var(--border);background:var(--accent-soft);flex-wrap:wrap;}
.ir .mn{font-size:22px;font-weight:700;color:var(--accent);}
.ir .sv{font-size:14px;font-weight:700;color:var(--accent2);background:var(--accent2-soft);padding:3px 10px;border-radius:6px;}
.ir .au{font-size:18px;}
.es{padding:16px 20px 20px;}
.esl{font-size:11px;font-weight:700;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;}
.ec{background:var(--ex-bg);border:1px solid var(--ex-border);border-radius:10px;padding:12px 16px;margin-bottom:10px;}
.ec:last-child{margin-bottom:0;}
.en{font-size:10px;font-weight:700;color:var(--muted);letter-spacing:1px;margin-bottom:4px;}
.ej{font-size:18px;font-weight:700;color:var(--text);line-height:1.6;margin-bottom:4px;}
.ea{font-size:15px;margin-bottom:4px;}
.ev{font-size:14px;color:var(--muted);font-style:italic;line-height:1.5;}
.fqw{background:var(--card-bg);border:1px solid var(--border);border-radius:var(--r);box-shadow:var(--shadow);max-width:560px;margin:16px auto;text-align:center;padding:48px 28px;}
.fql{font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;}
.fqm{font-size:38px;font-weight:900;color:var(--text);}
.blank{display:inline-block;min-width:50px;background:#ffe082;border-bottom:2.5px solid #f57c00;padding:0 8px;border-radius:4px;color:transparent;user-select:none;}
.fill-hint{font-size:14px;color:var(--accent);margin:6px 0 2px;padding:8px 14px;background:var(--accent-soft);border-radius:8px;text-align:center;line-height:1.6;}
.fill-word{background:var(--accent-soft);color:var(--accent);border-bottom:2.5px solid var(--accent);padding:0 3px;border-radius:3px;font-weight:700;}
.wb-wrap{padding:16px 20px 20px;}
.wb-meaning{font-size:32px;font-weight:900;color:var(--text);text-align:center;margin-bottom:6px;line-height:1.2;}
.wb-sub{font-size:14px;color:var(--accent2);text-align:center;margin-bottom:4px;}
.wb-label{font-size:11px;font-weight:700;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;text-align:center;margin-bottom:12px;}
.wb-ans-area{display:flex;flex-wrap:wrap;gap:6px;min-height:56px;justify-content:center;align-items:center;border:2px dashed var(--border);border-radius:12px;padding:10px;margin-bottom:12px;background:var(--ex-bg);transition:border-color .2s;}
.wb-bank-area{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;min-height:52px;padding:8px;margin-bottom:10px;}
.wb-tile{min-width:42px;height:42px;padding:0 10px;border:2px solid var(--accent);border-radius:8px;display:inline-flex;align-items:center;justify-content:center;font-size:20px;font-weight:700;cursor:pointer;background:var(--card-bg);color:var(--text);user-select:none;transition:transform .1s,box-shadow .1s;}
.wb-tile:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.15);}
.wb-tile.wb-drag{opacity:.4;}
.wb-tile.wb-ok{border-color:#27ae60;background:#d5f5e3;color:#1a5c35;}
.wb-tile.wb-err{border-color:#e74c3c;background:#fdecea;color:#c0392b;}
.card.nightMode .wb-tile.wb-ok{background:#0a2e18;color:#4ae89a;}
.card.nightMode .wb-tile.wb-err{background:#2e0a0a;color:#ff6b6b;}
.wb-actions{display:flex;gap:10px;justify-content:center;margin:4px 0 8px;}
.wb-btn-clear,.wb-btn-check{padding:9px 22px;border-radius:10px;font-weight:700;font-size:14px;cursor:pointer;border:none;}
.wb-btn-clear{background:var(--border);color:var(--text);}
.wb-btn-check{background:var(--accent);color:#fff;}
.wb-result{text-align:center;font-size:16px;font-weight:700;display:none;padding:8px;border-radius:8px;margin-top:4px;}
.wb-result.wb-ok{color:#27ae60;background:#d5f5e3;}
.wb-result.wb-err{color:#c0392b;background:#fdecea;}
.card.nightMode .wb-result.wb-ok{background:#0a2e18;color:#4ae89a;}
.card.nightMode .wb-result.wb-err{background:#2e0a0a;color:#ff6b6b;}
.pron-wrap{text-align:center;padding:0 24px 16px;}
.pron-lbl{font-size:11px;font-weight:700;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;}
''' + _HW_CSS


# ═══════════════════════════════════════════════════════════
#  JAPANESE CSS
# ═══════════════════════════════════════════════════════════

_JA_THEME = '''
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&family=Noto+Serif+JP:wght@700&display=swap');
:root {
    --bg:#f7f5f0;--card-bg:#ffffff;--border:#e8e2d9;--text:#1a1a2e;
    --muted:#7a7a8a;--accent:#c0392b;--accent-soft:#fdecea;
    --accent2:#2980b9;--accent2-soft:#eaf4fb;
    --ex-bg:#f9f7f4;--ex-border:#d4c5b0;--shadow:0 4px 20px rgba(0,0,0,0.07);--r:16px;
    --flag:"🇯🇵";
}
body{font-family:'Noto Sans JP','Meiryo',sans-serif;}
'''

_JA_SPECIFIC = '''
.furi{font-size:16px;color:var(--muted);letter-spacing:.05em;min-height:22px;margin-bottom:4px;}
.kanji{font-family:'Noto Serif JP',serif;font-size:64px;font-weight:700;color:var(--text);line-height:1.1;}
'''

_JA_EXTRA = '''
body{background:linear-gradient(150deg,#f7f5f0 0%,#fef0f4 100%);}
.ch{background:linear-gradient(135deg,#bc002d 0%,#8b0021 60%,#bc002d 100%);position:relative;}
.ch::before{content:'⛩';font-size:13px;opacity:.45;margin-right:6px;}
.cw{border-left:3px solid #bc002d;}
'''


def css_japanese():
    return _JA_THEME + _BASE_CSS + _JA_SPECIFIC + _JA_EXTRA + _SHARED_UI_CSS


# ═══════════════════════════════════════════════════════════
#  CHINESE CSS
# ═══════════════════════════════════════════════════════════

_ZH_THEME = '''
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&family=Noto+Serif+SC:wght@700&family=Noto+Sans+TC:wght@400;700;900&display=swap');
:root {
    --bg:#f7f7f5;--card-bg:#ffffff;--border:#e0ded8;--text:#1a1a2e;
    --muted:#7a7a8a;--accent:#c0392b;--accent-soft:#fdecea;
    --accent2:#2980b9;--accent2-soft:#eaf4fb;
    --ex-bg:#f9f8f5;--ex-border:#d4c5b0;--shadow:0 4px 20px rgba(0,0,0,0.07);--r:16px;
    --flag:"🇨🇳";
}
body{font-family:'Noto Sans SC','Noto Sans TC','Microsoft YaHei','PingFang SC',sans-serif;}
'''

_ZH_SPECIFIC = '''
.pinyin{font-size:16px;color:var(--muted);letter-spacing:.05em;min-height:22px;margin-bottom:4px;}
.hanzi{font-family:'Noto Serif SC','Noto Sans TC','KaiTi','STKaiti',serif;font-size:64px;font-weight:700;color:var(--text);line-height:1.1;}
.trad{font-size:14px;color:var(--muted);margin-top:6px;font-style:italic;}
.ep{font-size:13px;color:var(--accent2);margin-bottom:4px;}
'''

_ZH_EXTRA = '''
body{background:linear-gradient(150deg,#f7f7f5 0%,#fef5f2 100%);}
.ch{background:linear-gradient(135deg,#de2910 0%,#a3150a 60%,#de2910 100%);position:relative;}
.ch::before{content:'🐉';font-size:13px;opacity:.45;margin-right:6px;}
.cw{border-left:3px solid #de2910;}
'''


def css_chinese():
    return _ZH_THEME + _BASE_CSS + _ZH_SPECIFIC + _ZH_EXTRA + _SHARED_UI_CSS


# LANG_CSS Registry
LANG_CSS = {
    "japanese": css_japanese,
    "chinese":  css_chinese,
}


# ═══════════════════════════════════════════════════════════
#  GRAMMAR CSS — Note Type ngữ pháp (dùng chung 2 ngôn ngữ)
# ═══════════════════════════════════════════════════════════
_GRAMMAR_EXTRA = '''
.ch{background:linear-gradient(135deg,#34495e 0%,#22313f 60%,#34495e 100%);}
.ch::before{content:'📘';font-size:13px;opacity:.5;margin-right:6px;}
.cw{border-left:3px solid #34495e;}
.kanji,.hanzi{font-size:44px;}
'''


def css_japanese_grammar():
    return _JA_THEME + _BASE_CSS + _JA_SPECIFIC + _GRAMMAR_EXTRA + _SHARED_UI_CSS


def css_chinese_grammar():
    return _ZH_THEME + _BASE_CSS + _ZH_SPECIFIC + _GRAMMAR_EXTRA + _SHARED_UI_CSS


# LANG_GRAMMAR_CSS Registry
LANG_GRAMMAR_CSS = {
    "japanese": css_japanese_grammar,
    "chinese":  css_chinese_grammar,
}
