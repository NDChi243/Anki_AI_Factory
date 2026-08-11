"""
i18n Module — Hỗ trợ đa ngôn ngữ cho AnkiTool.

Cung cấp:
- t(key, lang=None): Lấy chuỗi dịch theo key
- set_language(lang): Đặt ngôn ngữ mặc định
- get_language(): Lấy ngôn ngữ hiện tại
- SUPPORTED_LANGUAGES: Danh sách ngôn ngữ được hỗ trợ

Sử dụng:
    from utils.i18n import t, set_language
    set_language("en")
    print(t("ai_extract"))  # "AI Extract"
"""

import json
import os

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n_config.json")

SUPPORTED_LANGUAGES = {
    "vi": "🇻🇳 Tiếng Việt",
    "en": "🇬🇧 English",
}

_current_lang = "vi"

# ═══════════════════════════════════════════════════════════
#  TRANSLATIONS DATABASE
# ═══════════════════════════════════════════════════════════

_TRANSLATIONS = {
    # ── App / Menu ──────────────────────────────────────
    "app_title": {
        "vi": "AnkiTool Multi-Lang V17.0 — Vocabulary Factory",
        "en": "AnkiTool Multi-Lang V17.0 — Vocabulary Factory",
    },
    "app_short": {
        "vi": "AnkiTool Multi-Lang V17.0",
        "en": "AnkiTool Multi-Lang V17.0",
    },
    "menu_entry": {
        "vi": "🌐 AnkiTool Multi-Lang V17.0",
        "en": "🌐 AnkiTool Multi-Lang V17.0",
    },

    # ── Language Selector ───────────────────────────────
    "lang_japanese": {
        "vi": "🇯🇵 Tiếng Nhật",
        "en": "🇯🇵 Japanese",
    },
    "lang_chinese": {
        "vi": "🇨🇳 Tiếng Trung",
        "en": "🇨🇳 Chinese",
    },
    "lang_korean": {
        "vi": "🇰🇷 Tiếng Hàn",
        "en": "🇰🇷 Korean",
    },

    # ── Deck & File ─────────────────────────────────────
    "deck_label": {
        "vi": "📦 Deck:",
        "en": "📦 Deck:",
    },
    "open_file_btn": {
        "vi": "📁 MỞ FILE (JSON/TXT)",
        "en": "📁 OPEN FILE (JSON/TXT)",
    },
    "sample_json_btn": {
        "vi": "💡 Xem mẫu JSON",
        "en": "💡 View JSON sample",
    },

    # ── AI Section ──────────────────────────────────────
    "ai_group_title": {
        "vi": "🤖 AI Trích Xuất Từ Vựng (OpenAI / DeepSeek / Ollama)",
        "en": "🤖 AI Vocabulary Extraction (OpenAI / DeepSeek / Ollama)",
    },
    "ai_settings_btn": {
        "vi": "⚙️ Cài Đặt API",
        "en": "⚙️ API Settings",
    },
    "ai_clear_text_btn": {
        "vi": "🗑 Xóa Text",
        "en": "🗑 Clear Text",
    },
    "ai_extract_btn": {
        "vi": "🤖 AI Trích Xuất",
        "en": "🤖 AI Extract",
    },
    "ai_batch_btn": {
        "vi": "📋 Batch Từ Vựng",
        "en": "📋 Batch Vocabulary",
    },
    "ai_chat_btn": {
        "vi": "💬 Gửi",
        "en": "💬 Send",
    },
    "ai_stop_btn": {
        "vi": "⏹ Dừng",
        "en": "⏹ Stop",
    },
    "ai_input_placeholder": {
        "vi": "📝 Dán văn bản vào đây (300-800 ký tự là tối ưu nhất, ~50-100 từ). Hỗ trợ tiếng Nhật & tiếng Trung.",
        "en": "📝 Paste text here (300-800 chars optimal, ~50-100 words). Supports Japanese & Chinese.",
    },
    "ai_instruction_placeholder": {
        "vi": "VD: Chỉ lấy từ HSK3+, chủ đề ẩm thực, ưu tiên từ khó...",
        "en": "e.g.: Only HSK3+ words, food topic, prioritize difficult words...",
    },
    "ai_instruction_label": {
        "vi": "💬 Lời nhắn:",
        "en": "💬 Instruction:",
    },

    # ── JSON Input ──────────────────────────────────────
    "json_input_label": {
        "vi": "📝 Dán dữ liệu JSON (hỗ trợ array hoặc multiple objects):",
        "en": "📝 Paste JSON data (supports array or multiple objects):",
    },

    # ── Filter Section ──────────────────────────────────
    "filter_group_title": {
        "vi": "⚙️ Bộ Lọc & Gác Cổng V5+",
        "en": "⚙️ Filter & Gatekeeper V5+",
    },
    "filter_raw_count": {
        "vi": "📊 Kho hàng: {count} mục",
        "en": "📊 Warehouse: {count} items",
    },
    "filter_level_label": {
        "vi": "🎓 Cấp độ:",
        "en": "🎓 Level:",
    },
    "filter_topic_label": {
        "vi": "🔍 Topic:",
        "en": "🔍 Topic:",
    },
    "filter_topic_placeholder": {
        "vi": "Lọc theo topic...",
        "en": "Filter by topic...",
    },
    "filter_audio_label": {
        "vi": "🔊 Auto Audio:",
        "en": "🔊 Auto Audio:",
    },
    "filter_audio_vocab": {
        "vi": "🎵 Vocab",
        "en": "🎵 Vocab",
    },
    "filter_audio_ex1": {
        "vi": "🎵 Ví dụ 1",
        "en": "🎵 Example 1",
    },
    "filter_audio_ex2": {
        "vi": "🎵 Ví dụ 2",
        "en": "🎵 Example 2",
    },

    # ── Action Buttons ──────────────────────────────────
    "btn_verify": {
        "vi": "🌪️ Kiểm Định",
        "en": "🌪️ Verify",
    },
    "btn_rebuild": {
        "vi": "🔨 Tái Tạo Model",
        "en": "🔨 Rebuild Model",
    },
    "btn_diff_meaning": {
        "vi": "🔍 Nghĩa Khác",
        "en": "🔍 Diff Meaning",
    },

    # ── Voice Section ───────────────────────────────────
    "voice_group_title": {
        "vi": "🎤 Chọn Giọng Đọc & Tốc Độ",
        "en": "🎤 Voice & Speed",
    },
    "voice_label": {
        "vi": "Giọng:",
        "en": "Voice:",
    },
    "voice_preview_btn": {
        "vi": "▶ Nghe thử",
        "en": "▶ Preview",
    },
    "voice_speed_label": {
        "vi": "⏩ Tốc độ:",
        "en": "⏩ Speed:",
    },

    # ── Preview List ────────────────────────────────────
    "preview_label": {
        "vi": "📋 Thẻ chờ xuất xưởng (✨ New | 🔄 Update | ⚠️ Trùng mờ):",
        "en": "📋 Cards ready for export (✨ New | 🔄 Update | ⚠️ Partial match):",
    },
    "preview_range_from": {
        "vi": "🔢 Từ:",
        "en": "🔢 From:",
    },
    "preview_range_to": {
        "vi": "đến:",
        "en": "to:",
    },
    "preview_ready": {
        "vi": "✅ Sẵn sàng: {count} thẻ",
        "en": "✅ Ready: {count} cards",
    },

    # ── Import Buttons ──────────────────────────────────
    "btn_import": {
        "vi": "🚀 XUẤT XƯỞNG (IMPORT)",
        "en": "🚀 EXPORT (IMPORT)",
    },
    "btn_cancel": {
        "vi": "⏹️ DỪNG LẠI",
        "en": "⏹️ STOP",
    },

    # ── Dialog Titles ───────────────────────────────────
    "dlg_ai_settings": {
        "vi": "⚙️ Cài Đặt AI — API Key & Model",
        "en": "⚙️ AI Settings — API Key & Model",
    },
    "dlg_ai_preview": {
        "vi": "🔍 Xem Trước & Chỉnh Sửa — {count} Từ Vựng",
        "en": "🔍 Preview & Edit — {count} Vocabulary",
    },
    "dlg_diff_meaning": {
        "vi": "🔍 Báo Cáo Nghĩa Khác — Xác Nhận Thêm Từ Vựng",
        "en": "🔍 Diff Meaning Report — Confirm Adding Vocabulary",
    },
    "dlg_ai_chat": {
        "vi": "💬 AI Chat — Trợ Lý Anki Thông Minh",
        "en": "💬 AI Chat — Smart Anki Assistant",
    },
    "dlg_batch": {
        "vi": "📋 Batch Xử Lý Từ Vựng Lớn",
        "en": "📋 Batch Large Vocabulary Processing",
    },

    # ── Messages ────────────────────────────────────────
    "msg_import_success": {
        "vi": "🚀 XUẤT XƯỞNG V17.0 THÀNH CÔNG! [{lang}]\n──────────────────────────────\n✨ Thêm mới   : {added} thẻ\n🔄 Cập nhật  : {updated} thẻ\n🎵 Audio gen  : {audio} file",
        "en": "🚀 EXPORT V17.0 SUCCESS! [{lang}]\n──────────────────────────────\n✨ New        : {added} cards\n🔄 Updated    : {updated} cards\n🎵 Audio gen  : {audio} files",
    },
    "msg_no_api_key": {
        "vi": "Bạn chưa cấu hình API Key.\n\nNếu dùng DeepSeek/OpenAI/OpenRouter: cần API Key.\nNếu dùng Ollama/LM Studio local: có thể để trống.\n\nMở Cài Đặt AI?",
        "en": "No API Key configured.\n\nFor DeepSeek/OpenAI/OpenRouter: API Key required.\nFor Ollama/LM Studio local: can be empty.\n\nOpen AI Settings?",
    },
    "msg_reasoner_warning": {
        "vi": "⚠️ Bạn đang dùng model '{model}'.\nModel này suy nghĩ rất kỹ trước khi trả lời,\ncó thể mất 3-10 phút. Hãy kiên nhẫn chờ đợi.\n\n💡 Mẹo: Chuyển sang 'deepseek-chat' để nhanh hơn.",
        "en": "⚠️ You are using model '{model}'.\nThis model thinks carefully before responding,\nmay take 3-10 minutes. Please be patient.\n\n💡 Tip: Switch to 'deepseek-chat' for faster results.",
    },
    "msg_history_count": {
        "vi": "📚 Lịch sử: {count} từ vựng đã có",
        "en": "📚 History: {count} existing vocabulary",
    },

    # ── AI Status ───────────────────────────────────────
    "status_scanning_deck": {
        "vi": "🔍 Đang quét deck Anki...",
        "en": "🔍 Scanning Anki deck...",
    },
    "status_calling_ai": {
        "vi": "⏳ Đang gọi AI...",
        "en": "⏳ Calling AI...",
    },
    "status_deck_count": {
        "vi": "📚 Deck có {count} từ → AI sẽ tránh trùng",
        "en": "📚 Deck has {count} words → AI will avoid duplicates",
    },
    "status_connecting": {
        "vi": "Đang kết nối...",
        "en": "Connecting...",
    },
    "status_cancelled": {
        "vi": "⏹ Đã dừng sau {elapsed}",
        "en": "⏹ Stopped after {elapsed}",
    },

    # ── Error Messages ──────────────────────────────────
    "err_no_words": {
        "vi": "⚠️ Không có từ vựng nào sau khi chỉnh sửa.",
        "en": "⚠️ No vocabulary after editing.",
    },
    "err_no_text": {
        "vi": "⚠️ Vui lòng dán văn bản vào ô trên trước.",
        "en": "⚠️ Please paste text in the box above first.",
    },
    "err_file_read": {
        "vi": "Lỗi đọc file: {error}",
        "en": "File read error: {error}",
    },

    # ── Deck Manager ─────────────────────────────────────
    "deck_manage_btn": {
        "vi": "🗂️ Quản Lý Deck",
        "en": "🗂️ Manage Decks",
    },
    "deck_refresh_btn": {
        "vi": "🔄",
        "en": "🔄",
    },
    "deck_manage_title": {
        "vi": "🗂️ Quản Lý Deck — Parent / Sub",
        "en": "🗂️ Deck Manager — Parent / Sub",
    },
    "deck_manage_desc": {
        "vi": "Tạo, đổi tên, xóa Parent/Sub Deck ngay trong add-on. Mọi thay đổi được đồng bộ tức thì vào Anki.",
        "en": "Create, rename, delete Parent/Sub Decks right in the add-on. All changes sync instantly to Anki.",
    },
    "deck_col_name": {
        "vi": "Deck",
        "en": "Deck",
    },
    "deck_col_cards": {
        "vi": "Thẻ",
        "en": "Cards",
    },
    "deck_add_parent": {
        "vi": "➕ Tạo Parent",
        "en": "➕ Add Parent",
    },
    "deck_add_sub": {
        "vi": "📁 Tạo Sub",
        "en": "📁 Add Sub",
    },
    "deck_rename": {
        "vi": "✏️ Đổi tên",
        "en": "✏️ Rename",
    },
    "deck_delete": {
        "vi": "🗑 Xóa",
        "en": "🗑 Delete",
    },
    "deck_refresh": {
        "vi": "🔄 Làm mới",
        "en": "🔄 Refresh",
    },
    "deck_add_parent_title": {
        "vi": "Tạo Parent Deck",
        "en": "Add Parent Deck",
    },
    "deck_add_parent_prompt": {
        "vi": "Tên deck cha:",
        "en": "Parent deck name:",
    },
    "deck_add_sub_title": {
        "vi": "Tạo Sub Deck",
        "en": "Add Sub Deck",
    },
    "deck_add_sub_prompt": {
        "vi": "Tên sub deck (trong '{parent}'):",
        "en": "Sub deck name (inside '{parent}'):",
    },
    "deck_add_sub_tip": {
        "vi": "Tạo sub deck bên trong deck đang chọn",
        "en": "Create a sub deck inside the selected deck",
    },
    "deck_rename_title": {
        "vi": "Đổi Tên Deck",
        "en": "Rename Deck",
    },
    "deck_rename_prompt": {
        "vi": "Tên mới:",
        "en": "New name:",
    },
    "deck_delete_title": {
        "vi": "Xóa Deck",
        "en": "Delete Deck",
    },
    "deck_delete_confirm": {
        "vi": "Xóa deck '{name}' và toàn bộ sub deck + thẻ bên trong?\nHành động này không thể hoàn tác.",
        "en": "Delete deck '{name}' and all sub decks + cards inside?\nThis action cannot be undone.",
    },
    "deck_select_first": {
        "vi": "⚠️ Chọn một deck trước",
        "en": "⚠️ Select a deck first",
    },
    "deck_created": {
        "vi": "✅ Đã tạo deck: {name}",
        "en": "✅ Deck created: {name}",
    },
    "deck_renamed": {
        "vi": "✅ Đã đổi tên: {old} → {new}",
        "en": "✅ Renamed: {old} → {new}",
    },
    "deck_deleted": {
        "vi": "🗑 Đã xóa deck: {name}",
        "en": "🗑 Deck deleted: {name}",
    },
    "deck_count_parents": {
        "vi": "✅ {count} deck cha",
        "en": "✅ {count} parent decks",
    },
}

# ═══════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════

def t(key: str, lang: str = None, **kwargs) -> str:
    """
    Lấy chuỗi dịch theo key.

    Args:
        key: Translation key
        lang: Ngôn ngữ (mặc định: ngôn ngữ hiện tại)
        **kwargs: Tham số format (VD: count=5)

    Returns:
        Chuỗi đã dịch (fallback về key nếu không tìm thấy)

    Example:
        >>> t("filter_raw_count", count=10)
        '📊 Kho hàng: 10 mục'
    """
    if lang is None:
        lang = _current_lang

    entry = _TRANSLATIONS.get(key, {})
    text = entry.get(lang) or entry.get("vi") or key

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass

    return text


def set_language(lang: str):
    """Đặt ngôn ngữ mặc định và lưu vào config."""
    global _current_lang
    if lang in SUPPORTED_LANGUAGES:
        _current_lang = lang
        _save_config()
    else:
        raise ValueError(f"Unsupported language: {lang}. Supported: {list(SUPPORTED_LANGUAGES.keys())}")


def get_language() -> str:
    """Lấy ngôn ngữ hiện tại."""
    return _current_lang


# ═══════════════════════════════════════════════════════════
#  PERSISTENCE
# ═══════════════════════════════════════════════════════════

def _save_config():
    """Lưu ngôn ngữ hiện tại vào file config."""
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"language": _current_lang}, f, indent=2)
    except Exception:
        pass


def _load_config():
    """Tải ngôn ngữ từ file config nếu có."""
    global _current_lang
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                lang = data.get("language", "vi")
                if lang in SUPPORTED_LANGUAGES:
                    _current_lang = lang
    except Exception:
        pass


# Tự động load config khi import module
_load_config()
