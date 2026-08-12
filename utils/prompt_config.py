"""
🎛️ Prompt Config — Đưa System Prompt + JSON Template của AI ra ngoài thành file
JSON chỉnh được (utils/ai_prompts.json) → người dùng đổi LUẬT / SCHEMA mà không
cần sửa code. (Đề xuất cải thiện #1 của đánh giá 66/100)

Thiết kế:
- DEFAULT (chân lý cuối cùng) vẫn nằm trong code (utils/ai_extractor.py):
  - _JSON_TEMPLATES / _GRAMMAR_JSON_TEMPLATES: mẫu schema.
  - _SYSTEM_PROMPTS / _GRAMMAR_SYSTEM_PROMPTS: prompt đã interpolate mẫu.
- utils/ai_prompts.json: file GHI ĐÈ lên defaults (gitignored, tự tạo khi người
  dùng Lưu trong editor). Mỗi entry lưu dạng RAW (system_prompt chứa placeholder
  {{JSON_TEMPLATE}}) để việc sửa json_template tự phản ánh vào prompt.
- get_system_prompt() / get_json_template(): trả giá trị HIỆU LỰC (đã merge).
- get_signature(): md5 của phần ghi đè → đưa vào cache key → sửa prompt tự
  invalidate cache (đúng quy tắc vàng #9: "Sửa prompt → bump để invalidate").

Lazy import ai_extractor (trong hàm, không ở top-level) để tránh circular import:
ai_extractor import prompt_config ở top → prompt_config chỉ import ai_extractor
khi có lời gọi hàm (lúc runtime).
"""

import json
import os
import re
import hashlib
import threading

from .logger import get_logger

logger = get_logger()

# Version của cấu trúc prompt config — bump khi thay đổi defaults (cache invalidation)
PROMPT_CONFIG_VERSION = 5

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_prompts.json")

LANGS = ("japanese", "chinese", "korean")
KINDS = ("vocab", "grammar")

# Placeholder đánh dấu chỗ chèn JSON template vào system prompt (dạng RAW)
TEMPLATE_PLACEHOLDER = "{{JSON_TEMPLATE}}"

_lock = threading.Lock()
_overrides_cache = None
_overrides_mtime = None


# ═══════════════════════════════════════════════════════════
#  FILE IO
# ═══════════════════════════════════════════════════════════

def _read_overrides() -> dict:
    """Đọc file ghi đè (nếu có). Trả {} khi thiếu/corrupt."""
    global _overrides_cache, _overrides_mtime
    if not os.path.exists(CONFIG_PATH):
        _overrides_cache = {}
        _overrides_mtime = None
        return {}
    try:
        mtime = os.path.getmtime(CONFIG_PATH)
        if _overrides_cache is not None and mtime == _overrides_mtime:
            return _overrides_cache
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
        _overrides_cache = data
        _overrides_mtime = mtime
        return data
    except Exception as e:
        logger.warning("prompt_config: đọc %s lỗi (%s) → dùng defaults", CONFIG_PATH, e)
        _overrides_cache = {}
        _overrides_mtime = None
        return {}


def _write_overrides(cfg: dict):
    """Ghi file ghi đè với atomic write (tmp → rename) — giống _save_config."""
    global _overrides_cache, _overrides_mtime
    tmp_path = CONFIG_PATH + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, CONFIG_PATH)
        _overrides_cache = dict(cfg)
        _overrides_mtime = os.path.getmtime(CONFIG_PATH)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise


# ═══════════════════════════════════════════════════════════
#  DEFAULTS (lazy từ ai_extractor — không trùng lặp nội dung)
# ═══════════════════════════════════════════════════════════

def _ui_is_english() -> bool:
    """UI đang ở tiếng Anh? (quyết định chọn prompt sinh nghĩa/dịch bằng tiếng Anh)."""
    try:
        from .i18n import get_language
        return get_language() == "en"
    except Exception:
        return False


def _default_json_template(lang: str, kind: str) -> str:
    from . import ai_extractor
    en = _ui_is_english()
    if kind == "grammar":
        table = ai_extractor._GRAMMAR_JSON_TEMPLATES_EN if en else ai_extractor._GRAMMAR_JSON_TEMPLATES
        fallback = ai_extractor._JAPANESE_GRAMMAR_JSON_TEMPLATE_EN if en else ai_extractor._JAPANESE_GRAMMAR_JSON_TEMPLATE
        return table.get(lang, fallback)
    table = ai_extractor._JSON_TEMPLATES_EN if en else ai_extractor._JSON_TEMPLATES
    fallback = ai_extractor._JAPANESE_JSON_TEMPLATE_EN if en else ai_extractor._JAPANESE_JSON_TEMPLATE
    return table.get(lang, fallback)


def _default_system_prompt(lang: str, kind: str) -> str:
    """System prompt mặc định (đã interpolate mẫu)."""
    from . import ai_extractor
    en = _ui_is_english()
    if kind == "grammar":
        table = ai_extractor._GRAMMAR_SYSTEM_PROMPTS_EN if en else ai_extractor._GRAMMAR_SYSTEM_PROMPTS
        fallback = ai_extractor._GRAMMAR_SYSTEM_PROMPTS_EN["japanese"] if en else ai_extractor._GRAMMAR_SYSTEM_PROMPTS["japanese"]
        return table.get(lang, fallback)
    table = ai_extractor._SYSTEM_PROMPTS_EN if en else ai_extractor._SYSTEM_PROMPTS
    fallback = ai_extractor._JAPANESE_SYSTEM_PROMPT_EN if en else ai_extractor._JAPANESE_SYSTEM_PROMPT
    return table.get(lang, fallback)


def _default_system_prompt_raw(lang: str, kind: str) -> str:
    """Chuyển prompt mặc định sang dạng RAW: thay mẫu JSON đúng 1 lần bằng placeholder.

    Vì mẫu JSON xuất hiện đúng 1 lần trong prompt (sau 'MẪU:'), ta dùng str.replace
    để tái dựng an toàn, KHÔNG phải copy-paste lại 250 dòng prompt.
    """
    tpl = _default_json_template(lang, kind)
    raw = _default_system_prompt(lang, kind).replace(tpl, TEMPLATE_PLACEHOLDER)
    return raw


# ═══════════════════════════════════════════════════════════
#  VALIDATION
# ═══════════════════════════════════════════════════════════

def validate_json_template(template: str):
    """Kiểm tra json_template có parse được JSON object không.

    Returns:
        (ok: bool, error: str | None, fields: list[str])
    """
    template = (template or "").strip()
    if not template:
        return False, "Template rỗng.", []
    try:
        data = json.loads(template)
    except Exception as e:
        return False, f"JSON không hợp lệ: {e}", []
    if not isinstance(data, dict):
        return False, "Template phải là một object JSON duy nhất (không phải mảng).", []
    fields = [str(k) for k in data.keys()]
    return True, None, fields


def _extract_fields(template: str):
    ok, err, fields = validate_json_template(template)
    return fields if ok else []


# ═══════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════

def _language_base_config(lang: str, kind: str) -> dict:
    """Config gốc từ Language/*.py (json_field_map, all_fields, model_name...).
    Lazy import — Language là pure data, không cần aqt, không circular.
    """
    from Language import LANG_CONFIG, LANG_GRAMMAR_CONFIG
    return (LANG_GRAMMAR_CONFIG if kind == "grammar" else LANG_CONFIG)[lang]


def _read_field_map_override(lang: str, kind: str) -> dict:
    """Field map người dùng ghi đè (field_map → kind → lang → {key: field})."""
    overrides = _read_overrides()
    fm = (overrides.get("field_map") or {}).get(kind) or {}
    m = fm.get(lang)
    return dict(m) if isinstance(m, dict) else {}


def _read_card_show_override(lang: str, kind: str) -> dict:
    """Vị trí hiển thị field trên thẻ (card_show → kind → lang → {field: side}).
    side ∈ {"front", "back", "both"} (mặc định "back")."""
    overrides = _read_overrides()
    cs = (overrides.get("card_show") or {}).get(kind) or {}
    m = cs.get(lang)
    if not isinstance(m, dict):
        return {}
    out = {}
    for f, s in m.items():
        s = str(s).strip().lower()
        if s in ("front", "back", "both"):
            out[str(f)] = s
    return out


def get_card_show(lang: str, kind: str = "vocab") -> dict:
    """Vị trí hiển thị field tuỳ chỉnh trên thẻ: {field: "front"|"back"|"both"}."""
    return _read_card_show_override(lang, kind)


def get_effective_config() -> dict:
    """Trả cấu hình HIỆU LỰC đầy đủ: defaults + ghi đè (dùng cho UI editor & preview).

    Shape:
        {
          "version": 4,
          "vocab":  {lang: {"json_template", "system_prompt", "system_prompt_raw",
                            "fields", "field_count", "modified",
                            "field_map", "default_field_map", "all_fields"}},
          "grammar": {...}
        }
    """
    overrides = _read_overrides()
    eff = {"version": PROMPT_CONFIG_VERSION, "vocab": {}, "grammar": {}}
    for kind in KINDS:
        for lang in LANGS:
            d_tpl = _default_json_template(lang, kind)
            d_raw = _default_system_prompt_raw(lang, kind)
            ov = (overrides.get(kind) or {}).get(lang) or {}
            # Template hiệu lực
            tpl_ov = ov.get("json_template")
            if tpl_ov and isinstance(tpl_ov, str) and tpl_ov.strip():
                tpl = tpl_ov
            else:
                tpl = d_tpl
            # System prompt RAW hiệu lực (chứa placeholder)
            sp_ov = ov.get("system_prompt")
            if sp_ov and isinstance(sp_ov, str) and sp_ov.strip():
                raw = sp_ov
            else:
                raw = d_raw
            # Interpolate placeholder (nếu không có placeholder thì giữ nguyên)
            sp = raw.replace(TEMPLATE_PLACEHOLDER, tpl)
            fields = _extract_fields(tpl)
            modified = bool(ov)
            # Field map hiệu lực (defaults từ Language/*.py + ghi đè người dùng)
            base = _language_base_config(lang, kind)
            default_map = dict(base.get("json_field_map") or {})
            eff_map = dict(default_map)
            eff_map.update(_read_field_map_override(lang, kind))
            eff[kind][lang] = {
                "json_template": tpl,
                "system_prompt": sp,
                "system_prompt_raw": raw,
                "fields": fields,
                "field_count": len(fields),
                "modified": modified,
                "field_map": eff_map,
                "default_field_map": default_map,
                "all_fields": list(base.get("all_fields") or []),
                "card_show": _read_card_show_override(lang, kind),
            }
    return eff


def get_json_template(lang: str, kind: str = "vocab") -> str:
    """Template JSON hiệu lực cho (lang, kind)."""
    if lang not in LANGS or kind not in KINDS:
        return _default_json_template(lang, kind)
    return get_effective_config()[kind][lang]["json_template"]


def get_system_prompt(lang: str, kind: str = "vocab") -> str:
    """System prompt hiệu lực (đã interpolate template) cho (lang, kind)."""
    if lang not in LANGS or kind not in KINDS:
        return _default_system_prompt(lang, kind)
    return get_effective_config()[kind][lang]["system_prompt"]


def get_fields(lang: str, kind: str = "vocab") -> list:
    """Danh sách field (key) trong template hiệu lực."""
    return get_effective_config()[kind][lang]["fields"]


def get_field_count(lang: str, kind: str = "vocab") -> int:
    return get_effective_config()[kind][lang]["field_count"]


def get_signature() -> str:
    """md5 của phần GHI ĐÈ (overrides) → dùng trong cache key.

    - Đổi prompt mặc định (trong code) → bump PROMPT_CONFIG_VERSION / _PROMPT_VERSION.
    - Đổi prompt của người dùng (sửa file/UI) → signature đổi → cache tự invalidate.
    """
    overrides = _read_overrides()
    try:
        raw = json.dumps(overrides, sort_keys=True, ensure_ascii=False)
    except Exception:
        raw = str(overrides)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def save_config(entries: dict, field_map: dict = None, card_show: dict = None) -> None:
    """Lưu cấu hình ghi đè từ UI editor.

    entries:    {kind: {lang: {"system_prompt": raw, "json_template": tpl}}}
    field_map:  {kind: {lang: {json_key: anki_field}}} (Mức 1 — Field Map Editor)
    card_show:  {kind: {lang: {anki_field: "front"|"back"|"both"}}} (Mức 2 — nơi hiện trên thẻ)
    Chỉ lưu phần cần thiết; bỏ các khóa dẫn xuất (fields/field_count/system_prompt interpolated).
    """
    clean = {"version": PROMPT_CONFIG_VERSION, "vocab": {}, "grammar": {}}
    for kind in KINDS:
        lang_map = (entries or {}).get(kind)
        if not isinstance(lang_map, dict):
            continue
        for lang in LANGS:
            e = lang_map.get(lang)
            if not isinstance(e, dict):
                continue
            entry = {}
            tpl = (e.get("json_template") or "").strip()
            if tpl:
                entry["json_template"] = tpl
            sp = (e.get("system_prompt") or "").strip()
            if sp:
                entry["system_prompt"] = sp
            if entry:
                clean[kind][lang] = entry
    # Field map (Mức 1)
    if field_map:
        clean_fm = {"vocab": {}, "grammar": {}}
        for kind in KINDS:
            lang_map = field_map.get(kind)
            if not isinstance(lang_map, dict):
                continue
            for lang in LANGS:
                m = lang_map.get(lang)
                if not isinstance(m, dict):
                    continue
                inner = {str(k): str(v).strip() for k, v in m.items() if str(k) and str(v).strip()}
                if inner:
                    clean_fm[kind][lang] = inner
        clean["field_map"] = clean_fm
    # Card show (Mức 2 — nơi hiển thị field tuỳ chỉnh trên thẻ)
    if card_show:
        clean_cs = {"vocab": {}, "grammar": {}}
        for kind in KINDS:
            lang_map = card_show.get(kind)
            if not isinstance(lang_map, dict):
                continue
            for lang in LANGS:
                m = lang_map.get(lang)
                if not isinstance(m, dict):
                    continue
                inner = {}
                for f, s in m.items():
                    s = str(s).strip().lower()
                    if s in ("front", "back", "both"):
                        inner[str(f).strip()] = s
                if inner:
                    clean_cs[kind][lang] = inner
        clean["card_show"] = clean_cs
    _write_overrides(clean)
    logger.info("prompt_config: đã lưu cấu hình prompt (+field_map +card_show) (%s)", CONFIG_PATH)


def auto_field_name(json_key: str) -> str:
    """Tự suy field Anki từ json key: english_meaning → English Meaning."""
    name = re.sub(r"[-_]+", " ", str(json_key)).strip()
    return name.title() if name else str(json_key)


def get_field_map(lang: str, kind: str = "vocab", default_field_map: dict = None) -> dict:
    """Field map HIỆU LỰC: {json_key: anki_field} = defaults + ghi đè người dùng."""
    eff = dict(default_field_map or {})
    eff.update(_read_field_map_override(lang, kind))
    return eff


def apply_field_map_to_cfg(cfg: dict, lang: str, kind: str = "vocab") -> dict:
    """Trả bản copy của cfg với json_field_map + all_fields + card_show HIỆU LỰC.

    - json_field_map: defaults (từ Language/*.py) + ghi đè người dùng.
    - all_fields: defaults + MỌI field mới xuất hiện trong field_map hiệu lực
      (để get_or_create_model/_ensure_fields tự tạo field trong Note Type).
    - card_show: vị trí hiển thị field tuỳ chỉnh trên thẻ (Mức 2).
    Đây là điểm bơm duy nhất → mọi nơi dùng self._cfg() đều tự có field mới.
    """
    eff_map = get_field_map(lang, kind, cfg.get("json_field_map") or {})
    all_fields = list(cfg.get("all_fields") or [])
    seen = set(all_fields)
    for fn in eff_map.values():
        fn = str(fn).strip()
        if fn and fn not in seen:
            all_fields.append(fn)
            seen.add(fn)
    out = dict(cfg)
    out["json_field_map"] = eff_map
    out["all_fields"] = all_fields
    out["card_show"] = get_card_show(lang, kind)
    return out


def reset_config() -> None:
    """Xóa file ghi đè → trở về mặc định (trong code)."""
    global _overrides_cache, _overrides_mtime
    with _lock:
        if os.path.exists(CONFIG_PATH):
            try:
                os.remove(CONFIG_PATH)
            except Exception as e:
                logger.warning("prompt_config: không xóa được %s (%s)", CONFIG_PATH, e)
                return False
        _overrides_cache = {}
        _overrides_mtime = None
    logger.info("prompt_config: đã reset về mặc định.")
    return True


def has_overrides() -> bool:
    """Kiểm tra xem có file ghi đè với nội dung không."""
    ov = _read_overrides()
    return bool(ov.get("vocab") or ov.get("grammar"))
