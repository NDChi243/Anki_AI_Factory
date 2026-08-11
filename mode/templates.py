"""
Japanese card templates.
"""

from .shared import _WB_JS_BODY, _HW_JS_BODY, WB_POOLS, _COMBO_MODE_JS

# ═══════════════════════════════════════════════════════════
#  JAPANESE TEMPLATES
# ═══════════════════════════════════════════════════════════
def tmpl_ja_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="furi">{{Furigana}}</div><div class="kanji">{{Front}}</div></div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '</div>'
    )

def tmpl_ja_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="furi">{{Furigana}}</div><div class="kanji">{{Front}}</div></div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '<div class="ir">'
          '<span class="mn">{{Meaning}}</span>'
          '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
          '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
          '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
            '<div class="ej">{{Example}}</div><div class="ea">{{Example Audio}}</div>'
            '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
          '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
            '<div class="ej">{{Example2}}</div><div class="ea">{{Example2 Audio}}</div>'
            '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )

def tmpl_ja_vn_q():
    return (
        '<div class="fqw">'
        '<div class="fql">Từ vựng tiếng Nhật là gì?</div>'
        '<div class="fqm">{{Meaning}}</div>'
        '<div style="margin-top:24px;font-size:15px;color:var(--muted);">'
          '<div class="typewrite">{{type:Front}}</div>'
        '</div></div>'
    )

def tmpl_ja_vn_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb">'
          '<div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Đáp án</div>'
          '<div class="furi">{{Furigana}}</div><div class="kanji">{{Front}}</div>'
        '</div>'
        '<div class="ir">'
          '<span class="mn">{{Meaning}}</span>'
          '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
          '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
          '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
            '<div class="ej">{{Example}}</div><div class="ea">{{Example Audio}}</div>'
            '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
          '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
            '<div class="ej">{{Example2}}</div><div class="ea">{{Example2 Audio}}</div>'
            '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )

def tmpl_ja_wb_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="wb-wrap">'
        '<div class="wb-meaning">{{Meaning}}</div>'
        '{{#Sino-Vietnamese}}<div class="wb-sub">{{Sino-Vietnamese}}</div>{{/Sino-Vietnamese}}'
        '<div class="wb-label">✍️ Ghép chữ thành từ tiếng Nhật</div>'
        '<div class="wb-ans-area" id="wb-ans"></div>'
        '<div class="wb-bank-area" id="wb-bank"></div>'
        '<div class="wb-actions">'
        '<button class="wb-btn-clear" onclick="wbClear()">✕ Xóa</button>'
        '<button class="wb-btn-check" onclick="wbCheck()">✓ Kiểm tra</button>'
        '</div>'
        '<div class="wb-result" id="wb-result"></div>'
        '</div></div>'
        '<script>var _wbWord="{{Front}}",_wbPool=' + WB_POOLS["japanese"] + ';' + _WB_JS_BODY + '</script>'
    )

def tmpl_ja_wb_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="furi">{{Furigana}}</div><div class="kanji">{{Front}}</div></div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
        '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div><div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div><div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )

def tmpl_ja_pron_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb" style="padding-bottom:4px;">'
        '<div class="kanji" style="margin-top:12px;">{{Front}}</div>'
        '<div style="font-size:13px;color:var(--muted);margin-top:8px;">{{Meaning}}</div>'
        '</div>'
        '<div class="pron-wrap">'
        '<div class="pron-lbl">Nhập Furigana (hiragana)</div>'
        '<div class="az"><div class="typewrite">{{type:Furigana}}</div></div>'
        '</div>'
        '</div>'
    )

def tmpl_ja_pron_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="furi">{{Furigana}}</div><div class="kanji">{{Front}}</div></div>'
        '<div class="az"><div class="typewrite">{{type:Furigana}}</div></div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
        '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '</div>'
    )

# ═══════════════════════════════════════════════════════════


# JAPANESE LETTER-GAP
def tmpl_ja_lg_q():
    return (
        '<div id="lg-word-src" style="display:none">{{Front}}</div>'
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="lg-wrap">'
          '<span class="lg-diff-badge" id="lg-diff"></span>'
          '{{#Furigana}}<div style="font-size:14px;color:var(--muted);margin-bottom:6px;">{{Furigana}}</div>{{/Furigana}}'
          '<div class="lg-display" id="lg-display"></div>'
          '<div class="lg-hint" id="lg-hint"></div>'
          '<div class="lg-clue">💡 Nghĩa: <b>{{Meaning}}</b></div>'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Front}}</div></div>'
        '</div>'
    )

def tmpl_ja_lg_a():
    return (
        '<div id="lg-word-src" style="display:none">{{Front}}</div>'
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="furi">{{Furigana}}</div><div class="kanji">{{Front}}</div></div>'
        '<div class="az">{{type:Front}}</div>'
        '<div class="ir">'
          '<span class="mn">{{Meaning}}</span>'
          '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
          '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
          '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
            '<div class="ej">{{Example}}</div><div class="ea">{{Example Audio}}</div>'
            '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
          '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
            '<div class="ej">{{Example2}}</div><div class="ea">{{Example2 Audio}}</div>'
            '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )

# ═══════════════════════════════════════════════════════════
#  CHINESE TEMPLATES
# ═══════════════════════════════════════════════════════════
def tmpl_zh_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '</div>'
    )

def tmpl_zh_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '<div class="ir">'
          '<span class="mn">{{Meaning}}</span>'
          '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
          '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
          '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
            '<div class="ej">{{Example}}</div>'
            '{{#Example Pinyin}}<div class="ep">{{Example Pinyin}}</div>{{/Example Pinyin}}'
            '<div class="ea">{{Example Audio}}</div>'
            '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
          '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
            '<div class="ej">{{Example2}}</div>'
            '{{#Example2 Pinyin}}<div class="ep">{{Example2 Pinyin}}</div>{{/Example2 Pinyin}}'
            '<div class="ea">{{Example2 Audio}}</div>'
            '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )

def tmpl_zh_vn_q():
    return (
        '<div class="fqw">'
        '<div class="fql">Từ vựng tiếng Trung là gì?</div>'
        '<div class="fqm">{{Meaning}}</div>'
        '<div style="margin-top:24px;font-size:15px;color:var(--muted);">'
          '<div class="typewrite">{{type:Front}}</div>'
        '</div></div>'
    )

def tmpl_zh_vn_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb">'
          '<div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Đáp án</div>'
          '<div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
          '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="ir">'
          '<span class="mn">{{Meaning}}</span>'
          '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
          '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
          '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
            '<div class="ej">{{Example}}</div>'
            '{{#Example Pinyin}}<div class="ep">{{Example Pinyin}}</div>{{/Example Pinyin}}'
            '<div class="ea">{{Example Audio}}</div>'
            '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
          '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
            '<div class="ej">{{Example2}}</div>'
            '{{#Example2 Pinyin}}<div class="ep">{{Example2 Pinyin}}</div>{{/Example2 Pinyin}}'
            '<div class="ea">{{Example2 Audio}}</div>'
            '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )

def tmpl_zh_wb_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="wb-wrap">'
        '<div class="wb-meaning">{{Meaning}}</div>'
        '{{#Sino-Vietnamese}}<div class="wb-sub">{{Sino-Vietnamese}}</div>{{/Sino-Vietnamese}}'
        '<div class="wb-label">✍️ Ghép chữ thành từ tiếng Trung</div>'
        '<div class="wb-ans-area" id="wb-ans"></div>'
        '<div class="wb-bank-area" id="wb-bank"></div>'
        '<div class="wb-actions">'
        '<button class="wb-btn-clear" onclick="wbClear()">✕ Xóa</button>'
        '<button class="wb-btn-check" onclick="wbCheck()">✓ Kiểm tra</button>'
        '</div>'
        '<div class="wb-result" id="wb-result"></div>'
        '</div></div>'
        '<script>var _wbWord="{{Front}}",_wbPool=' + WB_POOLS["chinese"] + ';' + _WB_JS_BODY + '</script>'
    )

def tmpl_zh_wb_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
        '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div>'
        '{{#Example Pinyin}}<div class="ep">{{Example Pinyin}}</div>{{/Example Pinyin}}'
        '<div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div>'
        '{{#Example2 Pinyin}}<div class="ep">{{Example2 Pinyin}}</div>{{/Example2 Pinyin}}'
        '<div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )

def tmpl_zh_pron_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb" style="padding-bottom:4px;">'
        '<div class="hanzi" style="margin-top:12px;">{{Front}}</div>'
        '<div style="font-size:13px;color:var(--muted);margin-top:8px;">{{Meaning}}</div>'
        '</div>'
        '<div class="pron-wrap">'
        '<div class="pron-lbl">Nhập Pinyin</div>'
        '<div class="az"><div class="typewrite">{{type:Pinyin}}</div></div>'
        '</div>'
        '</div>'
    )

def tmpl_zh_pron_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Pinyin}}</div></div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
        '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '</div>'
    )

# CHINESE LETTER-GAP
def tmpl_zh_lg_q():
    return (
        '<div id="lg-word-src" style="display:none">{{Front}}</div>'
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="lg-wrap">'
          '<span class="lg-diff-badge" id="lg-diff"></span>'
          '{{#Pinyin}}<div style="font-size:14px;color:var(--muted);margin-bottom:6px;">{{Pinyin}}</div>{{/Pinyin}}'
          '<div class="lg-display" id="lg-display"></div>'
          '<div class="lg-hint" id="lg-hint"></div>'
          '<div class="lg-clue">💡 Nghĩa: <b>{{Meaning}}</b></div>'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Front}}</div></div>'
        '</div>'
    )

def tmpl_zh_lg_a():
    return (
        '<div id="lg-word-src" style="display:none">{{Front}}</div>'
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="az">{{type:Front}}</div>'
        '<div class="ir">'
          '<span class="mn">{{Meaning}}</span>'
          '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
          '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
          '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
            '<div class="ej">{{Example}}</div>'
            '{{#Example Pinyin}}<div class="ep">{{Example Pinyin}}</div>{{/Example Pinyin}}'
            '<div class="ea">{{Example Audio}}</div>'
            '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
          '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
            '<div class="ej">{{Example2}}</div>'
            '{{#Example2 Pinyin}}<div class="ep">{{Example2 Pinyin}}</div>{{/Example2 Pinyin}}'
            '<div class="ea">{{Example2 Audio}}</div>'
            '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )


# ═══════════════════════════════════════════════════════════
#  GRAMMAR TEMPLATES (Ngữ pháp)
# ═══════════════════════════════════════════════════════════
def tmpl_ja_g_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '{{#Reading}}<div class="furi">{{Reading}}</div>{{/Reading}}'
        '<div class="kanji">{{Pattern}}</div>'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '</div>'
    )

def tmpl_ja_g_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '{{#Reading}}<div class="furi">{{Reading}}</div>{{/Reading}}'
        '<div class="kanji">{{Pattern}}</div>'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Usage}}<span class="sv">{{Usage}}</span>{{/Usage}}'
        '</div>'
        '{{#Explanation}}<div class="es"><div class="esl">Cách dùng</div>'
        '<div class="ec"><div class="ev" style="font-style:normal;color:var(--text);">{{Explanation}}</div></div>'
        '</div>{{/Explanation}}'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div><div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div><div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )

def tmpl_ja_g_rev_q():
    return (
        '<div class="fqw">'
        '<div class="fql">Cấu trúc ngữ pháp nào?</div>'
        '<div class="fqm">{{Meaning}}</div>'
        '{{#Usage}}<div class="wb-sub" style="margin-top:8px;">{{Usage}}</div>{{/Usage}}'
        '<div style="margin-top:24px;font-size:15px;color:var(--muted);">'
        '<div class="typewrite">{{type:Pattern}}</div>'
        '</div></div>'
    )

def tmpl_ja_g_rev_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '<div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Đáp án</div>'
        '{{#Reading}}<div class="furi">{{Reading}}</div>{{/Reading}}'
        '<div class="kanji">{{Pattern}}</div>'
        '</div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Usage}}<span class="sv">{{Usage}}</span>{{/Usage}}'
        '</div>'
        '{{#Explanation}}<div class="es"><div class="esl">Cách dùng</div>'
        '<div class="ec"><div class="ev" style="font-style:normal;color:var(--text);">{{Explanation}}</div></div>'
        '</div>{{/Explanation}}'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div><div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div><div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )

def tmpl_zh_g_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '{{#Pinyin}}<div class="pinyin">{{Pinyin}}</div>{{/Pinyin}}'
        '<div class="hanzi">{{Pattern}}</div>'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '</div>'
    )

def tmpl_zh_g_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '{{#Pinyin}}<div class="pinyin">{{Pinyin}}</div>{{/Pinyin}}'
        '<div class="hanzi">{{Pattern}}</div>'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Usage}}<span class="sv">{{Usage}}</span>{{/Usage}}'
        '</div>'
        '{{#Explanation}}<div class="es"><div class="esl">Cách dùng</div>'
        '<div class="ec"><div class="ev" style="font-style:normal;color:var(--text);">{{Explanation}}</div></div>'
        '</div>{{/Explanation}}'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div>'
        '{{#Example Pinyin}}<div class="ep">{{Example Pinyin}}</div>{{/Example Pinyin}}'
        '<div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div>'
        '{{#Example2 Pinyin}}<div class="ep">{{Example2 Pinyin}}</div>{{/Example2 Pinyin}}'
        '<div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )

def tmpl_zh_g_rev_q():
    return (
        '<div class="fqw">'
        '<div class="fql">Cấu trúc ngữ pháp nào?</div>'
        '<div class="fqm">{{Meaning}}</div>'
        '{{#Usage}}<div class="wb-sub" style="margin-top:8px;">{{Usage}}</div>{{/Usage}}'
        '<div style="margin-top:24px;font-size:15px;color:var(--muted);">'
        '<div class="typewrite">{{type:Pattern}}</div>'
        '</div></div>'
    )

def tmpl_zh_g_rev_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '<div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Đáp án</div>'
        '{{#Pinyin}}<div class="pinyin">{{Pinyin}}</div>{{/Pinyin}}'
        '<div class="hanzi">{{Pattern}}</div>'
        '</div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Usage}}<span class="sv">{{Usage}}</span>{{/Usage}}'
        '</div>'
        '{{#Explanation}}<div class="es"><div class="esl">Cách dùng</div>'
        '<div class="ec"><div class="ev" style="font-style:normal;color:var(--text);">{{Explanation}}</div></div>'
        '</div>{{/Explanation}}'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div>'
        '{{#Example Pinyin}}<div class="ep">{{Example Pinyin}}</div>{{/Example Pinyin}}'
        '<div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div>'
        '{{#Example2 Pinyin}}<div class="ep">{{Example2 Pinyin}}</div>{{/Example2 Pinyin}}'
        '<div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )

# ═══════════════════════════════════════════════════════════
#  COMBO TEMPLATES — GỘP 5 CHẾ ĐỘ VÀO 1 CARD DUY NHẤT
#  (1 từ = 1 card; deck đếm đúng số từ vựng, không nhân 5)
# ═══════════════════════════════════════════════════════════

# ── Mode bar chung cho cả front & back ──────────────────────
def _combo_mode_bar_japanese():
    return (
        '<div class="mode-bar" id="combo-mode-bar">'
        '<button class="mode-btn active" data-mode="qa">1. Nhật→Việt</button>'
        '<button class="mode-btn" data-mode="vn">2. Việt→Nhật</button>'
        '<button class="mode-btn" data-mode="wb">3. Ghép chữ</button>'
        '<button class="mode-btn" data-mode="pron">4. Furigana</button>'
        '<button class="mode-btn" data-mode="lg">5. Ẩn chữ</button>'
        '</div>'
    )


def _combo_mode_bar_chinese():
    return (
        '<div class="mode-bar" id="combo-mode-bar">'
        '<button class="mode-btn active" data-mode="qa">1. Trung→Việt</button>'
        '<button class="mode-btn" data-mode="vn">2. Việt→Trung</button>'
        '<button class="mode-btn" data-mode="wb">3. Ghép chữ</button>'
        '<button class="mode-btn" data-mode="pron">4. Pinyin</button>'
        '<button class="mode-btn" data-mode="lg">5. Ẩn chữ</button>'
        '</div>'
    )


def _combo_data_block(japanese=True):
    if japanese:
        return (
            '<div id="combo-data" style="display:none">'
            '<span id="combo-front">{{Front}}</span>'
            '<span id="combo-meaning">{{Meaning}}</span>'
            '<span id="combo-pron">{{Furigana}}</span>'
            '</div>'
        )
    return (
        '<div id="combo-data" style="display:none">'
        '<span id="combo-front">{{Front}}</span>'
        '<span id="combo-meaning">{{Meaning}}</span>'
        '<span id="combo-pron">{{Pinyin}}</span>'
        '</div>'
    )


def _combo_answer_common():
    """Đáp án đầy đủ dùng chung (hiển thị trong back)."""
    return (
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
        '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div><div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div><div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div>'
    )


def _combo_answer_common_zh():
    """Đáp án đầy đủ tiếng Trung (dùng trong back)."""
    return (
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
        '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div>'
        '{{#Example Pinyin}}<div class="ep">{{Example Pinyin}}</div>{{/Example Pinyin}}'
        '<div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div>'
        '{{#Example2 Pinyin}}<div class="ep">{{Example2 Pinyin}}</div>{{/Example2 Pinyin}}'
        '<div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div>'
    )


def tmpl_ja_combo_q():
    """Front gộp 5 mode — Nhật."""
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">{{Topic}}</span></div>'
        + _combo_mode_bar_japanese()
        + _combo_data_block(japanese=True)
        # Mode qa — Nhật→Việt (type answer chuẩn Anki)
        + '<div class="mode-panel" id="mode-panel-qa">'
        '<div class="vb"><div class="furi">{{Furigana}}</div><div class="kanji">{{Front}}</div></div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '</div>'
        # Mode vn — Việt→Nhật (tự kiểm tra bằng JS)
        + '<div class="mode-panel" id="mode-panel-vn" style="display:none">'
        '<div class="fqw"><div class="fql">Từ vựng tiếng Nhật là gì?</div><div class="fqm">{{Meaning}}</div></div>'
        '<div class="combo-check">'
        '<input id="vn-input" type="text" placeholder="Gõ từ tiếng Nhật..."/>'
        '<button id="vn-check" type="button">✓ Kiểm tra</button>'
        '</div>'
        '<div class="combo-res" id="vn-result"></div>'
        '</div>'
        # Mode wb — Ghép chữ
        + '<div class="mode-panel" id="mode-panel-wb" style="display:none">'
        '<div class="wb-wrap">'
        '<div class="wb-meaning">{{Meaning}}</div>'
        '{{#Sino-Vietnamese}}<div class="wb-sub">{{Sino-Vietnamese}}</div>{{/Sino-Vietnamese}}'
        '<div class="wb-label">✍️ Ghép chữ thành từ tiếng Nhật</div>'
        '<div class="wb-ans-area" id="wb-ans"></div>'
        '<div class="wb-bank-area" id="wb-bank"></div>'
        '<div class="wb-actions">'
        '<button class="wb-btn-clear" onclick="wbClear()">✕ Xóa</button>'
        '<button class="wb-btn-check" onclick="wbCheck()">✓ Kiểm tra</button>'
        '</div>'
        '<div class="wb-result" id="wb-result"></div>'
        '</div>'
        '</div>'
        # Mode pron — Furigana (tự kiểm tra bằng JS)
        + '<div class="mode-panel" id="mode-panel-pron" style="display:none">'
        '<div class="vb" style="padding-bottom:4px;">'
        '<div class="kanji" style="margin-top:12px;">{{Front}}</div>'
        '<div style="font-size:13px;color:var(--muted);margin-top:8px;">{{Meaning}}</div>'
        '</div>'
        '<div class="combo-check">'
        '<input id="pron-input" type="text" placeholder="Nhập Furigana (hiragana)..."/>'
        '<button id="pron-check" type="button">✓ Kiểm tra</button>'
        '</div>'
        '<div class="combo-res" id="pron-result"></div>'
        '</div>'
        # Mode lg — Ẩn chữ
        + '<div class="mode-panel" id="mode-panel-lg" style="display:none">'
        '<div id="lg-word-src" style="display:none">{{Front}}</div>'
        '<div class="lg-wrap">'
        '<span class="lg-diff-badge" id="lg-diff"></span>'
        '{{#Furigana}}<div style="font-size:14px;color:var(--muted);margin-bottom:6px;">{{Furigana}}</div>{{/Furigana}}'
        '<div class="lg-display" id="lg-display"></div>'
        '<div class="lg-hint" id="lg-hint"></div>'
        '<div class="lg-clue">💡 Nghĩa: <b>{{Meaning}}</b></div>'
        '</div>'
        '</div>'
        + '<script>var _wbWord="{{Front}}",_wbPool=' + WB_POOLS["japanese"] + ';' + _WB_JS_BODY + '</script>'
        + '<script>' + _COMBO_MODE_JS + '</script>'
        + '</div>'
    )


def tmpl_ja_combo_a():
    """Back gộp 5 mode — Nhật (hiển thị đáp án theo mode)."""
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{JLPT Level}}</span><span class="topic">{{Topic}}</span></div>'
        + _combo_mode_bar_japanese()
        + _combo_data_block(japanese=True)
        # Mode qa — đáp án đầy đủ + type result
        + '<div class="mode-panel" id="mode-panel-qa">'
        '<div class="vb"><div class="furi">{{Furigana}}</div><div class="kanji">{{Front}}</div></div>'
        '<div class="az">{{type:Meaning}}</div>'
        + _combo_answer_common()
        + '</div>'
        # Mode vn — đáp án = từ
        + '<div class="mode-panel" id="mode-panel-vn" style="display:none">'
        '<div class="vb">'
        '<div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Đáp án</div>'
        '<div class="furi">{{Furigana}}</div><div class="kanji">{{Front}}</div>'
        '</div>'
        + _combo_answer_common()
        + '</div>'
        # Mode wb — đáp án = từ
        + '<div class="mode-panel" id="mode-panel-wb" style="display:none">'
        '<div class="vb"><div class="furi">{{Furigana}}</div><div class="kanji">{{Front}}</div></div>'
        + _combo_answer_common()
        + '</div>'
        # Mode pron — đáp án = Furigana
        + '<div class="mode-panel" id="mode-panel-pron" style="display:none">'
        '<div class="vb"><div class="furi">{{Furigana}}</div><div class="kanji">{{Front}}</div></div>'
        '<div class="ir"><span class="mn">{{Furigana}}</span><span class="au">{{Vocab Audio}}</span></div>'
        '</div>'
        # Mode lg — đáp án = từ đầy đủ
        + '<div class="mode-panel" id="mode-panel-lg" style="display:none">'
        '<div class="vb"><div class="furi">{{Furigana}}</div><div class="kanji">{{Front}}</div></div>'
        + _combo_answer_common()
        + '</div>'
        + '<script>' + _COMBO_MODE_JS + '</script>'
        + '</div>'
    )


def tmpl_zh_combo_q():
    """Front gộp 5 mode — Trung."""
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        + _combo_mode_bar_chinese()
        + _combo_data_block(japanese=False)
        # Mode qa
        + '<div class="mode-panel" id="mode-panel-qa">'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '</div>'
        # Mode vn
        + '<div class="mode-panel" id="mode-panel-vn" style="display:none">'
        '<div class="fqw"><div class="fql">Từ vựng tiếng Trung là gì?</div><div class="fqm">{{Meaning}}</div></div>'
        '<div class="combo-check">'
        '<input id="vn-input" type="text" placeholder="Gõ từ tiếng Trung..."/>'
        '<button id="vn-check" type="button">✓ Kiểm tra</button>'
        '</div>'
        '<div class="combo-res" id="vn-result"></div>'
        '</div>'
        # Mode wb
        + '<div class="mode-panel" id="mode-panel-wb" style="display:none">'
        '<div class="wb-wrap">'
        '<div class="wb-meaning">{{Meaning}}</div>'
        '{{#Sino-Vietnamese}}<div class="wb-sub">{{Sino-Vietnamese}}</div>{{/Sino-Vietnamese}}'
        '<div class="wb-label">✍️ Ghép chữ thành từ tiếng Trung</div>'
        '<div class="wb-ans-area" id="wb-ans"></div>'
        '<div class="wb-bank-area" id="wb-bank"></div>'
        '<div class="wb-actions">'
        '<button class="wb-btn-clear" onclick="wbClear()">✕ Xóa</button>'
        '<button class="wb-btn-check" onclick="wbCheck()">✓ Kiểm tra</button>'
        '</div>'
        '<div class="wb-result" id="wb-result"></div>'
        '</div>'
        '</div>'
        # Mode pron — Pinyin
        + '<div class="mode-panel" id="mode-panel-pron" style="display:none">'
        '<div class="vb" style="padding-bottom:4px;">'
        '<div class="hanzi" style="margin-top:12px;">{{Front}}</div>'
        '<div style="font-size:13px;color:var(--muted);margin-top:8px;">{{Meaning}}</div>'
        '</div>'
        '<div class="combo-check">'
        '<input id="pron-input" type="text" placeholder="Nhập Pinyin..."/>'
        '<button id="pron-check" type="button">✓ Kiểm tra</button>'
        '</div>'
        '<div class="combo-res" id="pron-result"></div>'
        '</div>'
        # Mode lg
        + '<div class="mode-panel" id="mode-panel-lg" style="display:none">'
        '<div id="lg-word-src" style="display:none">{{Front}}</div>'
        '<div class="lg-wrap">'
        '<span class="lg-diff-badge" id="lg-diff"></span>'
        '{{#Pinyin}}<div style="font-size:14px;color:var(--muted);margin-bottom:6px;">{{Pinyin}}</div>{{/Pinyin}}'
        '<div class="lg-display" id="lg-display"></div>'
        '<div class="lg-hint" id="lg-hint"></div>'
        '<div class="lg-clue">💡 Nghĩa: <b>{{Meaning}}</b></div>'
        '</div>'
        '</div>'
        + '<script>var _wbWord="{{Front}}",_wbPool=' + WB_POOLS["chinese"] + ';' + _WB_JS_BODY + '</script>'
        + '<script>' + _COMBO_MODE_JS + '</script>'
        + '</div>'
    )


def tmpl_zh_combo_a():
    """Back gộp 5 mode — Trung."""
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        + _combo_mode_bar_chinese()
        + _combo_data_block(japanese=False)
        # Mode qa
        + '<div class="mode-panel" id="mode-panel-qa">'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="az">{{type:Meaning}}</div>'
        + _combo_answer_common_zh()
        + '</div>'
        # Mode vn
        + '<div class="mode-panel" id="mode-panel-vn" style="display:none">'
        '<div class="vb">'
        '<div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Đáp án</div>'
        '<div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        + _combo_answer_common_zh()
        + '</div>'
        # Mode wb
        + '<div class="mode-panel" id="mode-panel-wb" style="display:none">'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        + _combo_answer_common_zh()
        + '</div>'
        # Mode pron
        + '<div class="mode-panel" id="mode-panel-pron" style="display:none">'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div></div>'
        '<div class="ir"><span class="mn">{{Pinyin}}</span><span class="au">{{Vocab Audio}}</span></div>'
        '</div>'
        # Mode lg
        + '<div class="mode-panel" id="mode-panel-lg" style="display:none">'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        + _combo_answer_common_zh()
        + '</div>'
        + '<script>' + _COMBO_MODE_JS + '</script>'
        + '</div>'
    )


# ═══════════════════════════════════════════════════════════
#  KOREAN TEMPLATES
# ═══════════════════════════════════════════════════════════

# ── Mode bar cho card combo tiếng Hàn ──────────────────────
def _combo_mode_bar_korean():
    return (
        '<div class="mode-bar" id="combo-mode-bar">'
        '<button class="mode-btn active" data-mode="qa">1. Hàn→Việt</button>'
        '<button class="mode-btn" data-mode="vn">2. Việt→Hàn</button>'
        '<button class="mode-btn" data-mode="wb">3. Ghép chữ</button>'
        '<button class="mode-btn" data-mode="pron">4. Romanization</button>'
        '<button class="mode-btn" data-mode="lg">5. Ẩn chữ</button>'
        '</div>'
    )


def _combo_data_block_korean():
    """Dữ liệu ẩn cho JS combo — pron = Romanization."""
    return (
        '<div id="combo-data" style="display:none">'
        '<span id="combo-front">{{Front}}</span>'
        '<span id="combo-meaning">{{Meaning}}</span>'
        '<span id="combo-pron">{{Romanization}}</span>'
        '</div>'
    )


def _combo_answer_common_ko():
    """Đáp án đầy đủ tiếng Hàn (dùng trong back)."""
    return (
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
        '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div>'
        '{{#Example Romanization}}<div class="ep">{{Example Romanization}}</div>{{/Example Romanization}}'
        '<div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div>'
        '{{#Example2 Romanization}}<div class="ep">{{Example2 Romanization}}</div>{{/Example2 Romanization}}'
        '<div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div>'
    )


def tmpl_ko_combo_q():
    """Front gộp 5 mode — Hàn."""
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{TOPIK Level}}</span><span class="topic">{{Topic}}</span></div>'
        + _combo_mode_bar_korean()
        + _combo_data_block_korean()
        # Mode qa — Hàn→Việt (type answer chuẩn Anki)
        + '<div class="mode-panel" id="mode-panel-qa">'
        '<div class="vb"><div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '</div>'
        # Mode vn — Việt→Hàn (tự kiểm tra bằng JS)
        + '<div class="mode-panel" id="mode-panel-vn" style="display:none">'
        '<div class="fqw"><div class="fql">Từ vựng tiếng Hàn là gì?</div><div class="fqm">{{Meaning}}</div></div>'
        '<div class="combo-check">'
        '<input id="vn-input" type="text" placeholder="Gõ từ tiếng Hàn..."/>'
        '<button id="vn-check" type="button">✓ Kiểm tra</button>'
        '</div>'
        '<div class="combo-res" id="vn-result"></div>'
        '</div>'
        # Mode wb — Ghép chữ
        + '<div class="mode-panel" id="mode-panel-wb" style="display:none">'
        '<div class="wb-wrap">'
        '<div class="wb-meaning">{{Meaning}}</div>'
        '{{#Sino-Vietnamese}}<div class="wb-sub">{{Sino-Vietnamese}}</div>{{/Sino-Vietnamese}}'
        '<div class="wb-label">✍️ Ghép chữ thành từ tiếng Hàn</div>'
        '<div class="wb-ans-area" id="wb-ans"></div>'
        '<div class="wb-bank-area" id="wb-bank"></div>'
        '<div class="wb-actions">'
        '<button class="wb-btn-clear" onclick="wbClear()">✕ Xóa</button>'
        '<button class="wb-btn-check" onclick="wbCheck()">✓ Kiểm tra</button>'
        '</div>'
        '<div class="wb-result" id="wb-result"></div>'
        '</div>'
        '</div>'
        # Mode pron — Romanization (tự kiểm tra bằng JS)
        + '<div class="mode-panel" id="mode-panel-pron" style="display:none">'
        '<div class="vb" style="padding-bottom:4px;">'
        '<div class="hanzi" style="margin-top:12px;">{{Front}}</div>'
        '<div style="font-size:13px;color:var(--muted);margin-top:8px;">{{Meaning}}</div>'
        '</div>'
        '<div class="combo-check">'
        '<input id="pron-input" type="text" placeholder="Nhập Romanization..."/>'
        '<button id="pron-check" type="button">✓ Kiểm tra</button>'
        '</div>'
        '<div class="combo-res" id="pron-result"></div>'
        '</div>'
        # Mode lg — Ẩn chữ
        + '<div class="mode-panel" id="mode-panel-lg" style="display:none">'
        '<div id="lg-word-src" style="display:none">{{Front}}</div>'
        '<div class="lg-wrap">'
        '<span class="lg-diff-badge" id="lg-diff"></span>'
        '{{#Romanization}}<div style="font-size:14px;color:var(--muted);margin-bottom:6px;">{{Romanization}}</div>{{/Romanization}}'
        '<div class="lg-display" id="lg-display"></div>'
        '<div class="lg-hint" id="lg-hint"></div>'
        '<div class="lg-clue">💡 Nghĩa: <b>{{Meaning}}</b></div>'
        '</div>'
        '</div>'
        + '<script>var _wbWord="{{Front}}",_wbPool=' + WB_POOLS["korean"] + ';' + _WB_JS_BODY + '</script>'
        + '<script>' + _COMBO_MODE_JS + '</script>'
        + '</div>'
    )


def tmpl_ko_combo_a():
    """Back gộp 5 mode — Hàn."""
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{TOPIK Level}}</span><span class="topic">{{Topic}}</span></div>'
        + _combo_mode_bar_korean()
        + _combo_data_block_korean()
        # Mode qa
        + '<div class="mode-panel" id="mode-panel-qa">'
        '<div class="vb"><div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        '<div class="az">{{type:Meaning}}</div>'
        + _combo_answer_common_ko()
        + '</div>'
        # Mode vn
        + '<div class="mode-panel" id="mode-panel-vn" style="display:none">'
        '<div class="vb">'
        '<div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Đáp án</div>'
        '<div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div>'
        '</div>'
        + _combo_answer_common_ko()
        + '</div>'
        # Mode wb
        + '<div class="mode-panel" id="mode-panel-wb" style="display:none">'
        '<div class="vb"><div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        + _combo_answer_common_ko()
        + '</div>'
        # Mode pron
        + '<div class="mode-panel" id="mode-panel-pron" style="display:none">'
        '<div class="vb"><div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        '<div class="ir"><span class="mn">{{Romanization}}</span><span class="au">{{Vocab Audio}}</span></div>'
        '</div>'
        # Mode lg
        + '<div class="mode-panel" id="mode-panel-lg" style="display:none">'
        '<div class="vb"><div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        + _combo_answer_common_ko()
        + '</div>'
        + '<script>' + _COMBO_MODE_JS + '</script>'
        + '</div>'
    )


# ── Grammar templates tiếng Hàn ────────────────────────────
def tmpl_ko_g_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{TOPIK Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '{{#Romanization}}<div class="pinyin">{{Romanization}}</div>{{/Romanization}}'
        '<div class="hanzi">{{Pattern}}</div>'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '</div>'
    )


def tmpl_ko_g_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{TOPIK Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '{{#Romanization}}<div class="pinyin">{{Romanization}}</div>{{/Romanization}}'
        '<div class="hanzi">{{Pattern}}</div>'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Usage}}<span class="sv">{{Usage}}</span>{{/Usage}}'
        '</div>'
        '{{#Explanation}}<div class="es"><div class="esl">Cách dùng</div>'
        '<div class="ec"><div class="ev" style="font-style:normal;color:var(--text);">{{Explanation}}</div></div>'
        '</div>{{/Explanation}}'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div>'
        '{{#Example Romanization}}<div class="ep">{{Example Romanization}}</div>{{/Example Romanization}}'
        '<div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div>'
        '{{#Example2 Romanization}}<div class="ep">{{Example2 Romanization}}</div>{{/Example2 Romanization}}'
        '<div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )


def tmpl_ko_g_rev_q():
    return (
        '<div class="fqw">'
        '<div class="fql">Cấu trúc ngữ pháp nào?</div>'
        '<div class="fqm">{{Meaning}}</div>'
        '{{#Usage}}<div class="wb-sub" style="margin-top:8px;">{{Usage}}</div>{{/Usage}}'
        '<div style="margin-top:24px;font-size:15px;color:var(--muted);">'
        '<div class="typewrite">{{type:Pattern}}</div>'
        '</div></div>'
    )


def tmpl_ko_g_rev_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{TOPIK Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '<div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Đáp án</div>'
        '{{#Romanization}}<div class="pinyin">{{Romanization}}</div>{{/Romanization}}'
        '<div class="hanzi">{{Pattern}}</div>'
        '</div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Usage}}<span class="sv">{{Usage}}</span>{{/Usage}}'
        '</div>'
        '{{#Explanation}}<div class="es"><div class="esl">Cách dùng</div>'
        '<div class="ec"><div class="ev" style="font-style:normal;color:var(--text);">{{Explanation}}</div></div>'
        '</div>{{/Explanation}}'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div>'
        '{{#Example Romanization}}<div class="ep">{{Example Romanization}}</div>{{/Example Romanization}}'
        '<div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div>'
        '{{#Example2 Romanization}}<div class="ep">{{Example2 Romanization}}</div>{{/Example2 Romanization}}'
        '<div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )


# LANG_TEMPLATES Registry — mỗi ngôn ngữ chỉ 1 cặp template gộp (1 card/từ)
LANG_TEMPLATES = {
    "japanese": (
        tmpl_ja_combo_q, tmpl_ja_combo_a,
    ),
    "chinese": (
        tmpl_zh_combo_q, tmpl_zh_combo_a,
    ),
    "korean": (
        tmpl_ko_combo_q, tmpl_ko_combo_a,
    ),
}


# LANG_GRAMMAR_TEMPLATES Registry — Note Type ngữ pháp riêng
LANG_GRAMMAR_TEMPLATES = {
    "japanese": (
        tmpl_ja_g_q, tmpl_ja_g_a,
        tmpl_ja_g_rev_q, tmpl_ja_g_rev_a,
    ),
    "chinese": (
        tmpl_zh_g_q, tmpl_zh_g_a,
        tmpl_zh_g_rev_q, tmpl_zh_g_rev_a,
    ),
    "korean": (
        tmpl_ko_g_q, tmpl_ko_g_a,
        tmpl_ko_g_rev_q, tmpl_ko_g_rev_a,
    ),
}
