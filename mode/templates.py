"""
Japanese card templates.
"""

from .shared import _WB_JS_BODY, _HW_JS_BODY, WB_POOLS

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

# LANG_TEMPLATES Registry
LANG_TEMPLATES = {
    "japanese": (
        tmpl_ja_q, tmpl_ja_a, tmpl_ja_vn_q, tmpl_ja_vn_a,
        tmpl_ja_wb_q, tmpl_ja_wb_a,
        tmpl_ja_pron_q, tmpl_ja_pron_a,
        tmpl_ja_lg_q, tmpl_ja_lg_a,
    ),
    "chinese": (
        tmpl_zh_q, tmpl_zh_a, tmpl_zh_vn_q, tmpl_zh_vn_a,
        tmpl_zh_wb_q, tmpl_zh_wb_a,
        tmpl_zh_pron_q, tmpl_zh_pron_a,
        tmpl_zh_lg_q, tmpl_zh_lg_a,
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
}
