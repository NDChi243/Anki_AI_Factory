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

    # ── Main Window Toolbar ──────────────────────────────
    "brand_label": {
        "vi": "🧊 AnkiTool Glass",
        "en": "🧊 AnkiTool Glass",
    },
    "btn_theme": {
        "vi": "🎨 Giao diện",
        "en": "🎨 Theme",
    },
    "btn_theme_tip": {
        "vi": "Tùy chỉnh giao diện glassmorphism (theme, màu nhấn, độ trong, cỡ chữ, bo góc)",
        "en": "Customize glassmorphism theme (theme, accent color, glass level, font size, corner radius)",
    },
    "btn_snap_max": {
        "vi": "⛶ Phóng to",
        "en": "⛶ Maximize",
    },
    "btn_snap_max_tip": {
        "vi": "Phóng to toàn màn hình",
        "en": "Maximize to full screen",
    },
    "lbl_tip": {
        "vi": "💡 Kéo phân cách giữa 2 cột",
        "en": "💡 Drag divider between 2 columns",
    },

    # ── Main Window Selectors ────────────────────────────
    "lang_grp_title": {
        "vi": "🌐 Ngôn ngữ",
        "en": "🌐 Language",
    },
    "mode_grp_title": {
        "vi": "📚 Loại Thẻ",
        "en": "📚 Card Type",
    },
    "btn_mode_vocab": {
        "vi": "📖 Từ vựng",
        "en": "📖 Vocabulary",
    },
    "btn_mode_grammar": {
        "vi": "📘 Ngữ pháp",
        "en": "📘 Grammar",
    },
    "btn_lang_toggle": {
        "vi": "🌐 EN",
        "en": "🌐 VI",
    },
    "btn_lang_toggle_tip": {
        "vi": "Chuyển ngôn ngữ giao diện: Tiếng Việt ⇄ English",
        "en": "Switch UI language: Vietnamese ⇄ English",
    },
    "btn_refresh_deck_tip": {
        "vi": "Làm mới danh sách deck từ Anki",
        "en": "Refresh deck list from Anki",
    },
    "btn_manage_deck_tip": {
        "vi": "Tạo, đổi tên, xóa Parent/Sub Deck ngay trong add-on.\nMọi thay đổi được đồng bộ tức thì vào Anki.",
        "en": "Create, rename, delete Parent/Sub Decks right in the add-on.\nAll changes sync instantly to Anki.",
    },
    "btn_history": {
        "vi": "📚 Lịch Sử AI",
        "en": "📚 AI History",
    },
    "btn_history_tip": {
        "vi": "Xem lại lịch sử từ vựng đã lưu (AI trích xuất / import) — xem được ngay cả sau khi đóng Factory.\nTích chọn các từ cần và bấm 'Đưa Vào Xưởng' để Kiểm Định & xuất xưởng lại.",
        "en": "Review saved vocabulary history (AI extract / import) — viewable even after closing the Factory.\nCheck the words you need and click 'Pull Into Factory' to Verify & export again.",
    },
    "btn_ai_batch_tip": {
        "vi": "Xử lý danh sách từ vựng LỚN (hàng trăm/hàng nghìn từ).\nAI sẽ làm giàu từng từ + tự động tổ chức Parent/Sub Deck theo chủ đề.",
        "en": "Process LARGE vocabulary lists (hundreds/thousands of words).\nAI enriches each word + auto-organizes Parent/Sub Decks by topic.",
    },
    "btn_ai_chat_tip": {
        "vi": "Gửi câu hỏi/yêu cầu đến AI. AI sẽ làm việc thông minh với hệ thống Anki,\nchỉ truy vấn những gì cần thiết, không quét toàn bộ database.",
        "en": "Send questions/requests to AI. AI works smartly with the Anki system,\nonly querying what's needed, not scanning the whole database.",
    },
    "btn_ai_stop_tip": {
        "vi": "Dừng yêu cầu AI đang chạy",
        "en": "Stop the running AI request",
    },
    "btn_ai_attach": {
        "vi": "📎 Kẹp File",
        "en": "📎 Attach File",
    },
    "btn_ai_attach_tip": {
        "vi": "Đính kèm file tài liệu tham khảo (TXT/MD/DOCX/PDF/XLSX/CSV).\nAI sẽ đọc nội dung file để trích xuất từ vựng / ngữ pháp.\nLưu ý: DeepSeek chỉ nhận TEXT → add-on tự trích text từ file tại máy.",
        "en": "Attach reference document file (TXT/MD/DOCX/PDF/XLSX/CSV).\nAI reads the file content to extract vocabulary / grammar.\nNote: DeepSeek only accepts TEXT → the add-on extracts text from the file locally.",
    },
    "btn_ai_attach_clear": {
        "vi": "🧹 Bỏ File",
        "en": "🧹 Remove File",
    },
    "btn_ai_attach_clear_tip": {
        "vi": "Bỏ toàn bộ file đã kẹp và xóa nội dung trong ô AI",
        "en": "Remove all attached files and clear the AI input",
    },
    "btn_verify_tip": {
        "vi": "Kiểm định lô hàng — kiểm tra trùng lặp, cập nhật, từ mới",
        "en": "Verify the batch — check duplicates, updates, new words",
    },
    "btn_rebuild_tip": {
        "vi": "Tái tạo / cập nhật Model Note (template, CSS, fields)",
        "en": "Rebuild / update the Note Model (template, CSS, fields)",
    },
    "btn_diff_meaning_tip": {
        "vi": "Xem các từ vựng có cùng mặt chữ nhưng khác nghĩa để xác nhận thêm",
        "en": "View words with the same spelling but different meanings to confirm adding",
    },
    "btn_select_all": {
        "vi": "✅ Chọn Tất Cả",
        "en": "✅ Select All",
    },
    "btn_select_all_tip": {
        "vi": "Tích chọn tất cả thẻ đang hiển thị (theo bộ lọc)",
        "en": "Select all visible cards (per filter)",
    },
    "btn_select_none": {
        "vi": "☐ Bỏ Chọn",
        "en": "☐ Select None",
    },
    "btn_select_none_tip": {
        "vi": "Bỏ chọn tất cả thẻ đang hiển thị",
        "en": "Deselect all visible cards",
    },
    "lbl_sel_count": {
        "vi": "☑️ Đã chọn: {selected}/{total} thẻ",
        "en": "☑️ Selected: {selected}/{total} cards",
    },
    "btn_cancel_order": {
        "vi": "🧹 Hủy Hàng (Xóa Thẻ Trong Xưởng)",
        "en": "🧹 Cancel Order (Clear Factory Cards)",
    },
    "btn_cancel_order_tip": {
        "vi": "Chỉ xóa thẻ KHỎI XƯỞNG (danh sách chờ xuất xưởng) — không ảnh hưởng tới Anki.\nThẻ trong xưởng được lưu lại ngay cả khi đóng cửa sổ; chỉ mất khi bấm Hủy Hàng.",
        "en": "Only removes cards FROM THE FACTORY (pending export list) — doesn't affect Anki.\nFactory cards are saved even when the window closes; they're only lost when you click Cancel Order.",
    },
    "cbo_filter_all": {
        "vi": "📂 Tất cả",
        "en": "📂 All",
    },
    "cbo_filter_new": {
        "vi": "✨ Mới",
        "en": "✨ New",
    },
    "cbo_filter_update": {
        "vi": "🔄 Cập nhật",
        "en": "🔄 Update",
    },
    "cbo_filter_conflict": {
        "vi": "⚠️ Trùng mờ",
        "en": "⚠️ Partial match",
    },
    "cbo_filter_diff": {
        "vi": "🔍 Nghĩa khác",
        "en": "🔍 Diff meaning",
    },
    "cbo_filter_tip": {
        "vi": "Lọc nhanh theo loại thẻ sau khi Kiểm Định",
        "en": "Quick filter by card type after Verify",
    },
    "rng_from_label": {
        "vi": "🔢 Từ số:",
        "en": "🔢 From #:",
    },
    "rng_to_label": {
        "vi": "đến:",
        "en": "to:",
    },
    "rng_hint": {
        "vi": "(đổi khoảng = tự tích chọn)",
        "en": "(changing range auto-selects)",
    },
    "rng_tip": {
        "vi": "Thay đổi khoảng sẽ TỰ ĐỘNG tích chọn các thẻ trong khoảng đó",
        "en": "Changing the range AUTO-selects the cards in that range",
    },
    "study_mode_label": {
        "vi": "🎯 Mode:",
        "en": "🎯 Mode:",
    },
    "voice_tooltip": {
        "vi": "🎤 Sử dụng Edge TTS Online (cần internet, fallback gTTS)",
        "en": "🎤 Uses Edge TTS Online (needs internet, falls back to gTTS)",
    },
    "ai_input_placeholder_vocab": {
        "vi": "📝 Dán văn bản vào đây (300-800 ký tự là tối ưu nhất, ~50-100 từ). Hỗ trợ tiếng Nhật, Trung & Hàn.",
        "en": "📝 Paste text here (300-800 chars optimal, ~50-100 words). Supports Japanese, Chinese & Korean.",
    },
    "ai_input_placeholder_grammar": {
        "vi": "📝 Dán văn bản để trích xuất NGỮ PHÁP (cấu trúc, cách dùng, công thức, ví dụ)...",
        "en": "📝 Paste text to extract GRAMMAR (patterns, usage, formulas, examples)...",
    },

    # ── Main Window Status / Tooltips ────────────────────
    "status_history_count": {
        "vi": "📚 Lịch sử: {count} từ vựng đã có",
        "en": "📚 History: {count} existing vocabulary",
    },
    "status_cleared_factory": {
        "vi": "🧹 Đã xóa toàn bộ thẻ trong xưởng.",
        "en": "🧹 Cleared all cards in the factory.",
    },
    "status_done": {
        "vi": "✅ Hoàn tất!",
        "en": "✅ Done!",
    },
    "status_stopping": {
        "vi": "⏸️ Đang dừng...",
        "en": "⏸️ Stopping...",
    },
    "status_reading_file": {
        "vi": "📖 Đang đọc nội dung file... (lần đầu có thể tự cài thư viện đọc file)",
        "en": "📖 Reading file content... (first time may auto-install file reading libs)",
    },
    "status_no_file_content": {
        "vi": "⚠️ Không đọc được nội dung file nào.\n\n{errors}",
        "en": "⚠️ Could not read any file content.\n\n{errors}",
    },
    "status_batch_done": {
        "vi": "✅ Batch: {count} {label} đã xử lý!",
        "en": "✅ Batch: {count} {label} processed!",
    },
    "status_batch_empty": {
        "vi": "⚠️ Batch: Không có kết quả",
        "en": "⚠️ Batch: No results",
    },
    "status_connecting_elapsed": {
        "vi": "⏱ {elapsed} | Dự kiến: {estimate} | Đang kết nối...",
        "en": "⏱ {elapsed} | ETA: {estimate} | Connecting...",
    },
    "status_chat_done": {
        "vi": "✅ Hoàn tất sau {elapsed}!",
        "en": "✅ Finished after {elapsed}!",
    },
    "status_chat_error": {
        "vi": "❌ Lỗi sau {elapsed}: {error}",
        "en": "❌ Error after {elapsed}: {error}",
    },
    "status_stopped_ai": {
        "vi": "⏹ Đã dừng sau {elapsed}",
        "en": "⏹ Stopped after {elapsed}",
    },
    "tooltip_stopped_ai": {
        "vi": "⏹ Đã dừng yêu cầu AI.",
        "en": "⏹ Stopped the AI request.",
    },
    "status_poured_vocab": {
        "vi": "✅ Đã đổ {count} từ vựng vào xưởng!",
        "en": "✅ Poured {count} vocabulary into the factory!",
    },
    "status_pulled_history": {
        "vi": "📥 Đã đưa {count} từ từ lịch sử vào xưởng!",
        "en": "📥 Pulled {count} words from history into the factory!",
    },
    "tooltip_pulled_history": {
        "vi": "📥 Đã đưa {count} từ vào xưởng. Bấm 'Kiểm Định' để kiểm tra & xuất xưởng.",
        "en": "📥 Pulled {count} words into the factory. Click 'Verify' to check & export.",
    },
    "tooltip_switched_grammar": {
        "vi": "📘 Đã chuyển sang Ngữ pháp",
        "en": "📘 Switched to Grammar",
    },
    "tooltip_switched_vocab": {
        "vi": "📖 Đã chuyển sang Từ vựng",
        "en": "📖 Switched to Vocabulary",
    },
    "grammar_suffix": {
        "vi": " (Ngữ pháp)",
        "en": " (Grammar)",
    },

    # ── AI Chat Dialog ───────────────────────────────────
    "chat_header_title": {
        "vi": "💬 Trợ Lý AI Anki",
        "en": "💬 Anki AI Assistant",
    },
    "chat_header_sub": {
        "vi": "AI làm việc thông minh, chỉ truy vấn dữ liệu cần thiết",
        "en": "AI works smartly, only queries needed data",
    },
    "chat_error_html": {
        "vi": "<b>❌ Lỗi:</b><br>{error}",
        "en": "<b>❌ Error:</b><br>{error}",
    },
    "chat_vocab_group": {
        "vi": "📝 AI Đề Xuất {count} Từ Vựng",
        "en": "📝 AI Suggested {count} Vocabulary",
    },
    "chat_vocab_hint": {
        "vi": "AI đã trích xuất từ vựng từ phản hồi. Bạn có thể <b>đổ vào xưởng</b> để import vào Anki.",
        "en": "AI extracted vocabulary from the reply. You can <b>pour it into the factory</b> to import into Anki.",
    },
    "chat_close": {
        "vi": "❌ Đóng",
        "en": "❌ Close",
    },
    "chat_accept": {
        "vi": "✅ Đổ {count} Từ Vựng Vào Xưởng",
        "en": "✅ Pour {count} Vocabulary Into Factory",
    },
    "chat_copy": {
        "vi": "📋 Copy Phản Hồi",
        "en": "📋 Copy Reply",
    },
    "chat_copied_tip": {
        "vi": "✅ Đã copy phản hồi!",
        "en": "✅ Reply copied!",
    },
    "chat_no_reply": {
        "vi": "Không có phản hồi.",
        "en": "No reply.",
    },

    # ── AI Preview Dialog ────────────────────────────────
    "item_label_vocab": {
        "vi": "Từ Vựng",
        "en": "Vocabulary",
    },
    "item_label_grammar": {
        "vi": "Cấu Trúc Ngữ Pháp",
        "en": "Grammar Pattern",
    },
    "item_label_vocab_lower": {
        "vi": "từ vựng",
        "en": "vocabulary",
    },
    "item_label_grammar_lower": {
        "vi": "cấu trúc ngữ pháp",
        "en": "grammar pattern",
    },
    "item_label_grammar_short": {
        "vi": "cấu trúc",
        "en": "structure",
    },
    "item_label_vocab_short": {
        "vi": "từ",
        "en": "word",
    },
    "preview_header_html": {
        "vi": "🤖 AI đã trích xuất <span style='color:#e67e22;'>{count} {item}</span>",
        "en": "🤖 AI extracted <span style='color:#e67e22;'>{count} {item}</span>",
    },
    "preview_hint": {
        "vi": "<p style='color:#555;'>✏️ <b>Click đúp</b> vào ô để sửa. Chọn thẻ và dùng nút bên dưới để <b>Xóa</b> hoặc <b>Tái Tạo</b> từng thẻ. Có thể <b>Shift/Ctrl+Click</b> để chọn nhiều thẻ.</p>",
        "en": "<p style='color:#555;'>✏️ <b>Double-click</b> a cell to edit. Select cards and use the buttons below to <b>Delete</b> or <b>Regenerate</b> each card. Use <b>Shift/Ctrl+Click</b> to select multiple cards.</p>",
    },
    "btn_accept_all": {
        "vi": "✅ CHẤP NHẬN TẤT CẢ → Đổ Vào Xưởng",
        "en": "✅ ACCEPT ALL → Pour Into Factory",
    },
    "btn_edit_selected": {
        "vi": "✏️ Sửa Thẻ Đã Chọn",
        "en": "✏️ Edit Selected Cards",
    },
    "btn_delete_selected": {
        "vi": "🗑 Xóa Thẻ Đã Chọn",
        "en": "🗑 Delete Selected Cards",
    },
    "btn_regenerate": {
        "vi": "🔄 Tái Tạo Thẻ Đã Chọn",
        "en": "🔄 Regenerate Selected Cards",
    },
    "btn_regenerate_all": {
        "vi": "🔁 Tái Tạo Tất Cả",
        "en": "🔁 Regenerate All",
    },
    "btn_cancel_modal": {
        "vi": "❌ Hủy Bỏ",
        "en": "❌ Cancel",
    },
    "tooltip_select_to_delete": {
        "vi": "⚠️ Vui lòng chọn ít nhất một thẻ để xóa.",
        "en": "⚠️ Please select at least one card to delete.",
    },
    "tooltip_select_to_edit": {
        "vi": "⚠️ Vui lòng chọn một thẻ để sửa.",
        "en": "⚠️ Please select a card to edit.",
    },
    "tooltip_select_to_regen": {
        "vi": "⚠️ Vui lòng chọn ít nhất một thẻ để tái tạo.",
        "en": "⚠️ Please select at least one card to regenerate.",
    },
    "tooltip_no_source_text": {
        "vi": "⚠️ Không tìm thấy văn bản gốc để tái tạo.",
        "en": "⚠️ No source text found to regenerate.",
    },
    "tooltip_deleted": {
        "vi": "✅ Đã xóa {count} thẻ.",
        "en": "✅ Deleted {count} cards.",
    },
    "edit_dlg_title": {
        "vi": "✏️ Sửa Thẻ #{row}",
        "en": "✏️ Edit Card #{row}",
    },
    "btn_cancel_short": {
        "vi": "❌ Hủy",
        "en": "❌ Cancel",
    },
    "btn_save": {
        "vi": "💾 Lưu",
        "en": "💾 Save",
    },
    "tooltip_updated_card": {
        "vi": "✅ Đã cập nhật thẻ #{row}",
        "en": "✅ Updated card #{row}",
    },
    "regen_instr_grammar": {
        "vi": "CHỈ tái tạo các CẤU TRÚC NGỮ PHÁP sau (giữ nguyên pattern, cải thiện nghĩa + cách dùng + ví dụ):\n",
        "en": "ONLY regenerate the following GRAMMAR PATTERNS (keep pattern, improve meaning + usage + examples):\n",
    },
    "regen_instr_vocab": {
        "vi": "CHỈ tái tạo các từ sau đây (giữ nguyên mặt chữ, cải thiện nghĩa + ví dụ):\n",
        "en": "ONLY regenerate the following words (keep spelling, improve meaning + examples):\n",
    },
    "status_regen_done": {
        "vi": "✅ Đã tái tạo {count} thẻ!",
        "en": "✅ Regenerated {count} cards!",
    },
    "tooltip_regen_done": {
        "vi": "✅ Đã tái tạo {count} thẻ thành công!",
        "en": "✅ Successfully regenerated {count} cards!",
    },
    "tooltip_regen_fail": {
        "vi": "⚠️ AI không trả về kết quả tái tạo.",
        "en": "⚠️ AI didn't return regeneration results.",
    },
    "tooltip_regen_error": {
        "vi": "❌ Lỗi tái tạo: {error}",
        "en": "❌ Regeneration error: {error}",
    },
    "regen_all_confirm_title": {
        "vi": "🔁 Xác Nhận Tái Tạo Tất Cả",
        "en": "🔁 Confirm Regenerate All",
    },
    "regen_all_confirm_msg": {
        "vi": "Điều này sẽ gọi lại AI để trích xuất lại toàn bộ {item}.\nTất cả chỉnh sửa hiện tại sẽ bị mất.\n\nBạn có chắc chắn muốn tiếp tục?",
        "en": "This will call AI again to re-extract all {item}.\nAll current edits will be lost.\n\nAre you sure you want to continue?",
    },
    "tooltip_no_source_text2": {
        "vi": "⚠️ Không tìm thấy văn bản gốc.",
        "en": "⚠️ No source text found.",
    },
    "status_regen_all": {
        "vi": "✅ Tái tạo: {count} {item}!",
        "en": "✅ Regenerated: {count} {item}!",
    },
    "tooltip_regen_all": {
        "vi": "✅ Đã tái tạo toàn bộ: {count} {item}!",
        "en": "✅ Regenerated all: {count} {item}!",
    },
    "tooltip_regen_no_result": {
        "vi": "⚠️ AI không trả về kết quả.",
        "en": "⚠️ AI returned no results.",
    },
    "tooltip_regen_all_error": {
        "vi": "❌ Lỗi: {error}",
        "en": "❌ Error: {error}",
    },
    "tooltip_no_grammar_after": {
        "vi": "⚠️ Không có cấu trúc ngữ pháp nào sau khi chỉnh sửa.",
        "en": "⚠️ No grammar patterns after editing.",
    },
    "tooltip_no_vocab_after": {
        "vi": "⚠️ Không có từ vựng nào sau khi chỉnh sửa.",
        "en": "⚠️ No vocabulary after editing.",
    },

    # ── Batch Dialog ─────────────────────────────────────
    "batch_title_vocab": {
        "vi": "🚀 Xử Lý Danh Sách Từ Vựng Lớn — Batch AI",
        "en": "🚀 Large Vocabulary Processing — Batch AI",
    },
    "batch_title_grammar": {
        "vi": "🚀 Xử Lý Danh Sách Cấu Trúc Ngữ Pháp Lớn — Batch AI",
        "en": "🚀 Large Grammar Pattern Processing — Batch AI",
    },
    "batch_header_vocab": {
        "vi": "🚀 Xử Lý Danh Sách Từ Vựng Lớn ({lang})",
        "en": "🚀 Large Vocabulary Processing ({lang})",
    },
    "batch_header_grammar": {
        "vi": "🚀 Xử Lý Danh Sách Cấu Trúc Ngữ Pháp Lớn ({lang})",
        "en": "🚀 Large Grammar Pattern Processing ({lang})",
    },
    "batch_desc_vocab": {
        "vi": "Paste danh sách từ cần xử lý. AI sẽ làm giàu từng từ với đầy đủ nghĩa, phát âm, ví dụ, chủ đề.",
        "en": "Paste the word list to process. AI enriches each word with full meaning, reading, examples, topic.",
    },
    "batch_desc_grammar": {
        "vi": "Paste danh sách cấu trúc ngữ pháp cần xử lý. AI sẽ làm giàu từng cấu trúc với nghĩa, công thức, cách dùng, ví dụ.",
        "en": "Paste the grammar pattern list to process. AI enriches each pattern with meaning, formula, usage, examples.",
    },
    "batch_format_vocab": {
        "vi": "<b>📋 Format hỗ trợ (mỗi dòng 1 từ):</b><br>• <code>食べる</code> — chỉ từ<br>• <code>食べる : ăn</code> — từ + nghĩa<br>• <code>食べる : ăn : N5</code> — từ + nghĩa + cấp độ<br>• <code>食べる, たべる, ăn, N5</code> — CSV<br>• JSON array: <code>[{{\"front\":\"食べる\",\"meaning\":\"ăn\"}},...]</code><br><b>💡 Tip:</b> Bạn có thể paste hàng trăm, thậm chí hàng nghìn từ. AI sẽ tự động chia batch và xử lý tuần tự.",
        "en": "<b>📋 Supported formats (one word per line):</b><br>• <code>食べる</code> — word only<br>• <code>食べる : eat</code> — word + meaning<br>• <code>食べる : eat : N5</code> — word + meaning + level<br>• <code>食べる, たべる, eat, N5</code> — CSV<br>• JSON array: <code>[{{\"front\":\"食べる\",\"meaning\":\"eat\"}},...]</code><br><b>💡 Tip:</b> You can paste hundreds or even thousands of words. AI auto-splits into batches and processes sequentially.",
    },
    "batch_format_grammar": {
        "vi": "<b>📋 Format hỗ trợ (mỗi dòng 1 cấu trúc):</b><br>• <code>〜てもいい</code> — chỉ cấu trúc<br>• <code>〜てもいい : được phép</code> — cấu trúc + nghĩa<br>• <code>〜てもいい : được phép : N5</code> — + cấp độ<br>• JSON array: <code>[{{\"pattern\":\"〜てもいい\",\"meaning\":\"được phép\"}},...]</code><br><b>💡 Tip:</b> Bạn có thể paste hàng trăm cấu trúc. AI sẽ tự động chia batch và xử lý tuần tự.",
        "en": "<b>📋 Supported formats (one pattern per line):</b><br>• <code>〜てもいい</code> — pattern only<br>• <code>〜てもいい : allowed</code> — pattern + meaning<br>• <code>〜てもいい : allowed : N5</code> — + level<br>• JSON array: <code>[{{\"pattern\":\"〜てもいい\",\"meaning\":\"allowed\"}},...]</code><br><b>💡 Tip:</b> You can paste hundreds of patterns. AI auto-splits into batches and processes sequentially.",
    },
    "batch_list_label_grammar": {
        "vi": "<b>📝 Danh sách cấu trúc ngữ pháp:</b>",
        "en": "<b>📝 Grammar pattern list:</b>",
    },
    "batch_list_label_vocab": {
        "vi": "<b>📝 Danh sách từ vựng:</b>",
        "en": "<b>📝 Vocabulary list:</b>",
    },
    "batch_placeholder_grammar": {
        "vi": "Paste danh sách cấu trúc ngữ pháp vào đây...\n\nVí dụ:\n〜てもいい : được phép : N5\n〜そうです : nghe nói / có vẻ : N4\n〜ことにする : quyết định : N4\n...\n",
        "en": "Paste the grammar pattern list here...\n\nExample:\n〜てもいい : allowed : N5\n〜そうです : hearsay / seems : N4\n〜ことにする : decide : N4\n...\n",
    },
    "batch_placeholder_vocab": {
        "vi": "Paste danh sách từ vựng vào đây...\n\nVí dụ:\n食べる : ăn : N5\n飲む : uống : N5\n勉強する : học : N5\n...\n",
        "en": "Paste the vocabulary list here...\n\nExample:\n食べる : eat : N5\n飲む : drink : N5\n勉強する : study : N5\n...\n",
    },
    "batch_settings_grp": {
        "vi": "⚙️ Cấu hình xử lý",
        "en": "⚙️ Processing settings",
    },
    "batch_batch_size_label": {
        "vi": "Số từ/batch:",
        "en": "Words/batch:",
    },
    "batch_batch_size_tip": {
        "vi": "Số từ mỗi lần gửi AI. Nhỏ hơn = chất lượng cao hơn nhưng chậm hơn.",
        "en": "Number of words sent to AI each time. Smaller = higher quality but slower.",
    },
    "batch_instruction_label": {
        "vi": "Yêu cầu thêm:",
        "en": "Extra instruction:",
    },
    "batch_instruction_placeholder": {
        "vi": "VD: Chỉ lấy từ N3 trở lên, tập trung vào chủ đề kinh doanh...",
        "en": "e.g.: Only N3+ words, focus on business topics...",
    },
    "batch_deck_grp": {
        "vi": "📦 Tổ chức Deck (tự động)",
        "en": "📦 Deck Organization (auto)",
    },
    "batch_chk_auto_deck": {
        "vi": "🤖 AI tự đề xuất & tạo Parent/Sub Deck",
        "en": "🤖 AI auto-suggests & creates Parent/Sub Decks",
    },
    "batch_chk_auto_deck_tip": {
        "vi": "Sau khi xử lý từ vựng, AI sẽ phân tích tất cả từ và đề xuất cấu trúc deck (parent deck + sub decks) theo chủ đề, cấp độ.",
        "en": "After processing vocabulary, AI analyzes all words and suggests a deck structure (parent deck + sub decks) by topic, level.",
    },
    "batch_chk_create_decks": {
        "vi": "📁 Tự động tạo deck trong Anki",
        "en": "📁 Auto-create decks in Anki",
    },
    "batch_chk_create_decks_tip": {
        "vi": "Tự động tạo các deck được đề xuất trong Anki.",
        "en": "Auto-create the suggested decks in Anki.",
    },
    "batch_openrouter_grp": {
        "vi": "🐢 Chế độ OpenRouter Free",
        "en": "🐢 OpenRouter Free Mode",
    },
    "batch_chk_slow_mode": {
        "vi": "Chế độ chậm & ổn định (tránh rate limit 20 req/phút)",
        "en": "Slow & stable mode (avoid 20 req/min rate limit)",
    },
    "batch_chk_slow_mode_tip": {
        "vi": "OpenRouter free giới hạn ~20 request/phút.\nBật: tự đặt delay 3.2s/batch + retry mạnh khi gặp 429.\nTắt: nhanh hơn nhưng dễ bị rate limit.",
        "en": "OpenRouter free limits ~20 requests/minute.\nOn: auto delay 3.2s/batch + strong retry on 429.\nOff: faster but prone to rate limiting.",
    },
    "batch_estimate_hint": {
        "vi": "📊 <b>Ước tính:</b> Nhập danh sách từ ở trên để xem ước tính.",
        "en": "📊 <b>Estimate:</b> Enter the word list above to see an estimate.",
    },
    "batch_estimate_line": {
        "vi": "📊 <b>Ước tính:</b> {total} từ → ~{batches} batch ({size} từ/batch) | ~${cost:.4f} USD | ⏱ ~{seconds}s",
        "en": "📊 <b>Estimate:</b> {total} words → ~{batches} batches ({size} words/batch) | ~${cost:.4f} USD | ⏱ ~{seconds}s",
    },
    "batch_estimate_line_slow": {
        "vi": "⏱ ~{seconds}s ({batches} batch × ~{sec} — chế độ chậm OpenRouter)",
        "en": "⏱ ~{seconds}s ({batches} batches × ~{sec} — OpenRouter slow mode)",
    },
    "btn_close": {
        "vi": "❌ Đóng",
        "en": "❌ Close",
    },
    "btn_stop": {
        "vi": "⏹ Dừng",
        "en": "⏹ Stop",
    },
    "btn_process_ai": {
        "vi": "🚀 Xử Lý Với AI",
        "en": "🚀 Process With AI",
    },
    "batch_status_estimate": {
        "vi": "📊 <b>Ước tính:</b> Nhập danh sách từ ở trên để xem ước tính.",
        "en": "📊 <b>Estimate:</b> Enter the word list above to see an estimate.",
    },
    "tooltip_enter_vocab_list": {
        "vi": "⚠️ Vui lòng nhập danh sách từ vựng.",
        "en": "⚠️ Please enter the vocabulary list.",
    },
    "batch_status_preparing": {
        "vi": "⏳ Đang chuẩn bị...",
        "en": "⏳ Preparing...",
    },
    "batch_status_finished": {
        "vi": "✅ Hoàn tất! {count} {label} đã được AI xử lý.",
        "en": "✅ Done! {count} {label} processed by AI.",
    },
    "batch_status_organizing": {
        "vi": "🧠 AI đang phân tích và tổ chức deck...",
        "en": "🧠 AI is analyzing and organizing decks...",
    },
    "batch_status_organized": {
        "vi": "✅ Đã phân tích xong! {parents} parent deck, {subs} sub deck.",
        "en": "✅ Analysis done! {parents} parent decks, {subs} sub decks.",
    },
    "batch_status_decks_created": {
        "vi": "✅ Đã tạo {count} deck trong Anki!\n{names}",
        "en": "✅ Created {count} decks in Anki!\n{names}",
    },
    "tooltip_decks_created": {
        "vi": "✅ Đã tạo {count} deck!",
        "en": "✅ Created {count} decks!",
    },
    "batch_status_error": {
        "vi": "❌ Lỗi: {error}",
        "en": "❌ Error: {error}",
    },
    "batch_status_stopped": {
        "vi": "⏹️ Đã dừng xử lý.",
        "en": "⏹️ Processing stopped.",
    },
    "batch_done_button": {
        "vi": "✅ Hoàn tất ({count} {label}) — Xem Kết Quả",
        "en": "✅ Done ({count} {label}) — View Results",
    },

    # ── History Dialog ───────────────────────────────────
    "history_title": {
        "vi": "📚 Lịch Sử AI — Từ Vựng Đã Lưu",
        "en": "📚 AI History — Saved Vocabulary",
    },
    "history_header": {
        "vi": "📚 Lịch Sử Từ Vựng Đã Lưu (AI / Import)",
        "en": "📚 Saved Vocabulary History (AI / Import)",
    },
    "history_desc": {
        "vi": "Xem lại các từ đã được AI trích xuất hoặc import. Tích chọn rồi bấm <b>📥 Đưa Vào Xưởng</b> để đưa vào xưởng, sau đó bấm <b>Kiểm Định</b> và <b>XUẤT XƯỞNG</b> lại.",
        "en": "Review words extracted by AI or imported. Check the ones you want, click <b>📥 Pull Into Factory</b> to bring them into the factory, then click <b>Verify</b> and <b>EXPORT</b> again.",
    },
    "history_search_placeholder": {
        "vi": "🔍 Tìm theo từ / nghĩa / cấp độ...",
        "en": "🔍 Search by word / meaning / level...",
    },
    "history_lang_all": {
        "vi": "📂 Tất cả",
        "en": "📂 All",
    },
    "history_lang_tip": {
        "vi": "Lọc lịch sử theo ngôn ngữ",
        "en": "Filter history by language",
    },
    "history_list_tip": {
        "vi": "Tích chọn các từ muốn đưa vào xưởng",
        "en": "Check the words you want to pull into the factory",
    },
    "btn_select_all2": {
        "vi": "✅ Chọn Tất Cả",
        "en": "✅ Select All",
    },
    "btn_select_none2": {
        "vi": "☐ Bỏ Chọn",
        "en": "☐ Select None",
    },
    "btn_pull_into_factory": {
        "vi": "📥 Đưa Vào Xưởng",
        "en": "📥 Pull Into Factory",
    },
    "btn_pull_into_factory_tip": {
        "vi": "Đưa các từ đã chọn vào xưởng để Kiểm Định & xuất xưởng lại",
        "en": "Pull selected words into the factory to Verify & export again",
    },
    "history_count_visible": {
        "vi": "📚 {count} từ đang hiển thị",
        "en": "📚 {count} words visible",
    },
    "tooltip_no_selection": {
        "vi": "⚠️ Chưa chọn từ nào. Hãy tích chọn các từ cần đưa vào xưởng.",
        "en": "⚠️ No words selected. Check the words you want to pull into the factory.",
    },

    # ── AI Settings Dialog ───────────────────────────────
    "ai_set_api_key_placeholder": {
        "vi": "sk-... (DeepSeek: vào platform.deepseek.com/api_keys để lấy)",
        "en": "sk-... (DeepSeek: get it at platform.deepseek.com/api_keys)",
    },
    "ai_set_base_placeholder": {
        "vi": "https://api.deepseek.com/v1 (DeepSeek) hoặc https://api.openai.com/v1",
        "en": "https://api.deepseek.com/v1 (DeepSeek) or https://api.openai.com/v1",
    },
    "btn_clear_ai_cache": {
        "vi": "🗑 Xóa Cache AI",
        "en": "🗑 Clear AI Cache",
    },
    "btn_clear_history": {
        "vi": "🗑 Xóa Lịch Sử",
        "en": "🗑 Clear History",
    },
    "btn_edit_prompts": {
        "vi": "✏️ Sửa Prompt / Schema AI",
        "en": "✏️ Edit AI Prompt / Schema",
    },
    "btn_edit_prompts_tip": {
        "vi": "Sửa System Prompt / JSON Schema cho từng ngôn ngữ và chế độ (từ vựng / ngữ pháp).",
        "en": "Edit System Prompt / JSON Schema per language and mode (vocabulary / grammar).",
    },
    "btn_test_connection": {
        "vi": "🧪 Test Kết Nối",
        "en": "🧪 Test Connection",
    },
    "ai_test_success": {
        "vi": "✅ Kết nối thành công!\n\nModel: {model}\nPhản hồi: {reply}",
        "en": "✅ Connection successful!\n\nModel: {model}\nReply: {reply}",
    },

    # ── Verify Dialog ────────────────────────────────────
    "verify_new_box": {
        "vi": "📥 TỪ MỚI (đang nhập)",
        "en": "📥 NEW WORD (entering)",
    },
    "verify_old_box": {
        "vi": "📚 TỪ ĐÃ CÓ (trong Anki)",
        "en": "📚 EXISTING WORD (in Anki)",
    },

    # ── Prompt Editor ────────────────────────────────────
    "prompt_placeholder": {
        "vi": "Bạn là chuyên gia…",
        "en": "You are an expert…",
    },
    "btn_reset_defaults": {
        "vi": "♻️ Reset Mặc Định",
        "en": "♻️ Reset Defaults",
    },
    "btn_save_all": {
        "vi": "💾 Lưu Tất Cả",
        "en": "💾 Save All",
    },

    # ── Deck Manager extras ──────────────────────────────
    "deck_manage_header": {
        "vi": "🗂️ Quản Lý Deck",
        "en": "🗂️ Manage Decks",
    },

    # ── Theme Dialog ─────────────────────────────────────
    "theme_title": {
        "vi": "🎨 Tùy chỉnh giao diện",
        "en": "🎨 Customize theme",
    },
    "theme_header": {
        "vi": "🧊 Glassmorphism — Tùy chỉnh giao diện",
        "en": "🧊 Glassmorphism — Customize theme",
    },
    "theme_live_hint": {
        "vi": "Thay đổi áp dụng ngay (live). Nhấn “Áp dụng & Lưu” để lưu.",
        "en": "Changes apply immediately (live). Click “Apply & Save” to save.",
    },
    "theme_preset_label": {
        "vi": "🎚 Chủ đề:",
        "en": "🎚 Theme:",
    },
    "theme_accent_label": {
        "vi": "🎨 Màu nhấn:",
        "en": "🎨 Accent color:",
    },
    "theme_alpha_label": {
        "vi": "💎 Độ trong của kính:",
        "en": "💎 Glass level:",
    },
    "theme_font_label": {
        "vi": "🔠 Cỡ chữ:",
        "en": "🔠 Font size:",
    },
    "theme_radius_label": {
        "vi": "◻️ Bo góc:",
        "en": "◻️ Corner radius:",
    },
    "theme_preview_grp": {
        "vi": "👁 Xem trước",
        "en": "👁 Preview",
    },
    "btn_button_sample": {
        "vi": "Nút nhấn",
        "en": "Button",
    },
    "btn_success_sample": {
        "vi": "Thành công",
        "en": "Success",
    },
    "btn_ghost_sample": {
        "vi": "Phụ",
        "en": "Ghost",
    },
    "theme_combo_sample": {
        "vi": "Từ vựng",
        "en": "Vocabulary",
    },
    "theme_apply_save": {
        "vi": "✅ Áp dụng & Lưu",
        "en": "✅ Apply & Save",
    },
    "theme_cancel": {
        "vi": "Hủy",
        "en": "Cancel",
    },
    "theme_color_dialog_title": {
        "vi": "Chọn màu nhấn",
        "en": "Choose accent color",
    },
    "theme_applied_tip": {
        "vi": "🎨 Đã áp dụng giao diện mới",
        "en": "🎨 New theme applied",
    },

    # ── Main Window extras ───────────────────────────────
    "spin_speed_tip": {
        "vi": "Tốc độ phát audio mặc định cho thẻ học\n(0.25× = chậm nhất, 4.0× = nhanh nhất)",
        "en": "Default audio playback speed for study cards\n(0.25× = slowest, 4.0× = fastest)",
    },
    "search_placeholder": {
        "vi": "🔍 Tìm theo từ / nghĩa... (lọc trực tiếp)",
        "en": "🔍 Search by word / meaning... (direct filter)",
    },
    "sample_json_title": {
        "vi": "💡 Mẫu JSON — {label}",
        "en": "💡 JSON Sample — {label}",
    },
    "choose_type_label": {
        "vi": "Chọn loại:",
        "en": "Choose type:",
    },
    "btn_copy_close": {
        "vi": "📋 Copy & Đóng",
        "en": "📋 Copy & Close",
    },
    "file_dialog_title": {
        "vi": "Chọn file dữ liệu",
        "en": "Choose data file",
    },
    "file_dialog_filter": {
        "vi": "Dữ liệu (*.json *.txt)",
        "en": "Data (*.json *.txt)",
    },
    "preview_suffix_dup_diff": {
        "vi": "  [🔍 Nghĩa khác: mới='{new}' ← cũ='{old}']",
        "en": "  [🔍 Diff meaning: new='{new}' ← old='{old}']",
    },
    "preview_suffix_update": {
        "vi": "  [Cập nhật: {fields}]",
        "en": "  [Update: {fields}]",
    },
    "preview_suffix_partial": {
        "vi": "  [Trùng mờ — vẫn thêm]",
        "en": "  [Partial match — still adding]",
    },
    "tooltip_audio_preview_fail": {
        "vi": "Không thể phát audio preview.",
        "en": "Cannot play audio preview.",
    },
    "tooltip_audio_gen_fail": {
        "vi": "⚠️ Không thể tạo audio. Kiểm tra kết nối internet và edge-tts.",
        "en": "⚠️ Cannot generate audio. Check internet connection and edge-tts.",
    },
    "tooltip_no_cards_ready": {
        "vi": "⚠️ Chưa có thẻ nào sẵn sàng trong xưởng.",
        "en": "⚠️ No cards ready in the factory.",
    },
    "status_cleared_selected": {
        "vi": "🧹 Đã xóa {count} thẻ đã chọn khỏi xưởng.",
        "en": "🧹 Removed {count} selected cards from the factory.",
    },
    "msg_chat_poured": {
        "vi": "🤖 AI Chat Hoàn Tất!\n\n📊 Đã đổ {count} từ vựng vào khung JSON.\n👉 Nhấn <b>'Kiểm Định Lô Hàng'</b> để kiểm tra và import.",
        "en": "🤖 AI Chat Complete!\n\n📊 Poured {count} vocabulary into the JSON box.\n👉 Click <b>'Verify Batch'</b> to check and import.",
    },
    "msg_extract_poured": {
        "vi": "🤖 AI Trích Xuất Hoàn Tất!\n\n📊 Đã đổ {count} từ vựng vào khung JSON.\n👉 Nhấn <b>'Kiểm Định Lô Hàng'</b> để kiểm tra và import.",
        "en": "🤖 AI Extraction Complete!\n\n📊 Poured {count} vocabulary into the JSON box.\n👉 Click <b>'Verify Batch'</b> to check and import.",
    },
    "dlg_preview_edit": {
        "vi": "🔍 Xem Trước & Chỉnh Sửa — {count} {item}",
        "en": "🔍 Preview & Edit — {count} {item}",
    },
    "btn_select_all_check": {
        "vi": "☑️ Chọn Tất Cả",
        "en": "☑️ Select All",
    },
    "btn_accept_pour": {
        "vi": "✅ CHẤP NHẬN & ĐỔ VÀO XƯỞNG",
        "en": "✅ ACCEPT & POUR INTO FACTORY",
    },

    # ── AI Settings Dialog ───────────────────────────────
    "ai_set_header_title": {
        "vi": "🤖 Cấu hình OpenAI-compatible API",
        "en": "🤖 Configure OpenAI-compatible API",
    },
    "ai_set_header_sub": {
        "vi": "Hỗ trợ: OpenAI, DeepSeek, Ollama, LM Studio, Claude (qua proxy), OpenRouter, v.v.",
        "en": "Supports: OpenAI, DeepSeek, Ollama, LM Studio, Claude (via proxy), OpenRouter, etc.",
    },
    "ai_set_header_tip": {
        "vi": "💡 Mẹo: Bấm nút <b>DeepSeek</b> bên dưới để tự điền Base URL + Model, sau đó chỉ cần nhập API Key từ <a href='https://platform.deepseek.com/api_keys'>platform.deepseek.com/api_keys</a>",
        "en": "💡 Tip: Click the <b>DeepSeek</b> button below to auto-fill Base URL + Model, then just enter the API Key from <a href='https://platform.deepseek.com/api_keys'>platform.deepseek.com/api_keys</a>",
    },
    "ai_set_api_key_label": {
        "vi": "🔑 API Key:",
        "en": "🔑 API Key:",
    },
    "ai_set_show_key": {
        "vi": "👁 Hiện API Key",
        "en": "👁 Show API Key",
    },
    "ai_set_base_label": {
        "vi": "🌐 API Base URL:",
        "en": "🌐 API Base URL:",
    },
    "ai_set_model_label": {
        "vi": "🧠 Model:",
        "en": "🧠 Model:",
    },
    "ai_set_temp_label": {
        "vi": "🌡 Temperature (0-2):",
        "en": "🌡 Temperature (0-2):",
    },
    "ai_set_effort_label": {
        "vi": "🧠 Mức độ suy nghĩ (reasoning_effort):",
        "en": "🧠 Reasoning effort:",
    },
    "ai_set_effort_auto": {
        "vi": "Tự động (không gửi tham số)",
        "en": "Auto (no parameter sent)",
    },
    "ai_set_effort_low": {
        "vi": "Thấp — nhanh, rẻ, ít token",
        "en": "Low — fast, cheap, fewer tokens",
    },
    "ai_set_effort_medium": {
        "vi": "Trung bình",
        "en": "Medium",
    },
    "ai_set_effort_high": {
        "vi": "Cao — sâu, chất lượng tốt, tốn token",
        "en": "High — deep, better quality, more tokens",
    },
    "ai_set_chunk_label": {
        "vi": "📏 Độ dài xử lý mỗi lần gọi (ký tự):",
        "en": "📏 Chars processed per call:",
    },
    "ai_set_preset_grp": {
        "vi": "⚡ Presets",
        "en": "⚡ Presets",
    },
    "ai_set_preset_ollama": {
        "vi": "Ollama (local)",
        "en": "Ollama (local)",
    },
    "ai_set_preset_lm": {
        "vi": "LM Studio (local)",
        "en": "LM Studio (local)",
    },
    "tooltip_cache_cleared": {
        "vi": "✅ Đã xóa toàn bộ cache AI!",
        "en": "✅ All AI cache cleared!",
    },
    "tooltip_history_cleared": {
        "vi": "✅ Đã xóa lịch sử từ vựng!",
        "en": "✅ Vocabulary history cleared!",
    },
    "tooltip_history_clear_fail": {
        "vi": "⚠️ Không thể xóa lịch sử.",
        "en": "⚠️ Could not clear history.",
    },
    "tooltip_saved_config": {
        "vi": "✅ Đã lưu cấu hình AI!",
        "en": "✅ AI config saved!",
    },

    # ── Verify Dialog ────────────────────────────────────
    "verify_edit_label": {
        "vi": "✏️ Chỉnh sửa nhanh (tùy chọn):",
        "en": "✏️ Quick edit (optional):",
    },

    # ── Prompt Editor extras ─────────────────────────────
    "prompt_field_map_tab": {
        "vi": "🗂 Field Map",
        "en": "🗂 Field Map",
    },
    "prompt_system_tab": {
        "vi": "System Prompt",
        "en": "System Prompt",
    },
    "prompt_json_tab": {
        "vi": "JSON Template",
        "en": "JSON Template",
    },

    # ── Verify Dialog ────────────────────────────────────
    "tooltip_no_diff_meaning": {
        "vi": "Không có từ vựng nào thuộc diện 'nghĩa khác' để báo cáo.",
        "en": "No vocabulary falls under 'diff meaning' to report.",
    },
    "verify_title_html": {
        "vi": "🔍 Phát hiện <span style='color:#e67e22;'>{count} từ vựng</span> có cùng mặt chữ nhưng <b>nghĩa khác</b> với từ đã có.",
        "en": "🔍 Found <span style='color:#e67e22;'>{count} vocabulary</span> with the same spelling but <b>different meaning</b> from existing words.",
    },
    "verify_sub_html": {
        "vi": "Chọn những từ bạn muốn <b>cho phép thêm</b> dù trùng mặt chữ. Các từ không chọn sẽ bị loại bỏ.",
        "en": "Select the words you want to <b>allow adding</b> despite duplicate spelling. Unselected words will be removed.",
    },
    "verify_field_spelling": {
        "vi": "Mặt chữ:",
        "en": "Spelling:",
    },
    "verify_field_meaning": {
        "vi": "Nghĩa:",
        "en": "Meaning:",
    },
    "verify_field_level": {
        "vi": "Cấp độ:",
        "en": "Level:",
    },
    "verify_checkbox_label": {
        "vi": "✅ Cho phép thêm từ mới \"{front}\" với nghĩa \"{meaning}\"",
        "en": "✅ Allow adding new word \"{front}\" with meaning \"{meaning}\"",
    },
    "btn_select_all_lower": {
        "vi": "☑️ Chọn tất cả",
        "en": "☑️ Select all",
    },
    "btn_deselect_all_lower": {
        "vi": "☐ Bỏ chọn tất cả",
        "en": "☐ Deselect all",
    },
    "btn_confirm_allow": {
        "vi": "🚀 XÁC NHẬN & CHO QUA",
        "en": "🚀 CONFIRM & ALLOW",
    },

    # ── Prompt Editor ────────────────────────────────────
    "prompt_editor_title": {
        "vi": "✏️ Sửa Prompt, Schema & Field Map AI",
        "en": "✏️ Edit AI Prompt, Schema & Field Map",
    },
    "prompt_editor_header": {
        "vi": "✏️ Prompt, Schema & Field Map AI",
        "en": "✏️ Prompt, Schema & Field Map AI",
    },
    "prompt_editor_sub": {
        "vi": "Chỉnh <b>System Prompt</b>, <b>mẫu JSON</b> và <b>map key → Field Anki</b> cho từng ngôn ngữ. <b>Không cần sửa code.</b>",
        "en": "Edit <b>System Prompt</b>, <b>JSON template</b> and <b>key → Anki Field map</b> per language. <b>No coding needed.</b>",
    },
    "prompt_lang_label": {
        "vi": "🌏 Ngôn ngữ:",
        "en": "🌏 Language:",
    },
    "prompt_json_label": {
        "vi": "📋 Mẫu JSON (schema AI phải tuân theo):",
        "en": "📋 JSON template (schema AI must follow):",
    },
    "prompt_system_label": {
        "vi": "🧠 System Prompt",
        "en": "🧠 System Prompt",
    },
    "prompt_kind_label": {
        "vi": "📦 Loại:",
        "en": "📦 Type:",
    },
    "btn_preview_prompt": {
        "vi": "👁 Xem Prompt Đầy Đủ",
        "en": "👁 View Full Prompt",
    },
    "prompt_fm_key": {
        "vi": "Key JSON (từ template)",
        "en": "JSON Key (from template)",
    },
    "prompt_fm_field": {
        "vi": "Field Anki",
        "en": "Anki Field",
    },
    "prompt_fm_show": {
        "vi": "Hiển thị",
        "en": "Show",
    },

    # ── Worker progress messages ─────────────────────────
    "worker_progress_grammar": {
        "vi": "🤖 Đang gọi AI trích xuất NGỮ PHÁP...",
        "en": "🤖 Calling AI to extract GRAMMAR...",
    },
    "worker_progress_vocab": {
        "vi": "🤖 Đang gọi AI trích xuất từ vựng...",
        "en": "🤖 Calling AI to extract vocabulary...",
    },
    "worker_progress_context": {
        "vi": "🔍 Đang thu thập ngữ cảnh Anki...",
        "en": "🔍 Collecting Anki context...",
    },
    "worker_progress_organize": {
        "vi": "🧠 Đang phân tích từ vựng để tổ chức deck...",
        "en": "🧠 Analyzing vocabulary to organize decks...",
    },
    "worker_progress_create_decks": {
        "vi": "📁 Đang tạo deck trong Anki...",
        "en": "📁 Creating decks in Anki...",
    },
    "worker_progress_empty_deck": {
        "vi": "📚 Deck trống — sẵn sàng gọi AI",
        "en": "📚 Deck empty — ready to call AI",
    },
    "worker_error_no_deck": {
        "vi": "⚠️ AI không đề xuất được cấu trúc deck.",
        "en": "⚠️ AI could not suggest a deck structure.",
    },
    "status_deck_avoid": {
        "vi": "📚 Tránh {count} {label} trong deck...",
        "en": "📚 Avoiding {count} {label} in deck...",
    },
    "empty_grammar": {
        "vi": "⚠️ AI không trích xuất được cấu trúc ngữ pháp nào. Thử văn bản có nội dung rõ ràng hơn.",
        "en": "⚠️ AI could not extract any grammar patterns. Try clearer text.",
    },
    "empty_vocab": {
        "vi": "⚠️ AI không trích xuất được từ vựng nào. Thử văn bản có nội dung rõ ràng hơn.",
        "en": "⚠️ AI could not extract any vocabulary. Try clearer text.",
    },
    "worker_summary_deck": {
        "vi": "📋 Đề xuất: {parents} parent deck, {subs} sub deck",
        "en": "📋 Suggested: {parents} parent decks, {subs} sub decks",
    },

    # ── Study Mode labels (Mode combo + Overview selector) ─
    "lang_src_ja": {
        "vi": "Nhật",
        "en": "Japanese",
    },
    "lang_src_zh": {
        "vi": "中文",
        "en": "Chinese",
    },
    "lang_src_ko": {
        "vi": "한국어",
        "en": "Korean",
    },
    "lang_tgt": {
        "vi": "Việt",
        "en": "English",
    },
    "mode_label_wb": {
        "vi": "Ghép chữ",
        "en": "Word Builder",
    },
    "mode_label_lg": {
        "vi": "Ẩn chữ cái",
        "en": "Letter Gap",
    },
    "mode_label_pron_ja": {
        "vi": "Furigana",
        "en": "Furigana",
    },
    "mode_label_pron_zh": {
        "vi": "Pinyin",
        "en": "Pinyin",
    },
    "mode_label_pron_ko": {
        "vi": "Romanization",
        "en": "Romanization",
    },
    "overview_mode_label": {
        "vi": "🎯 Chế độ học:",
        "en": "🎯 Study mode:",
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
    """Đặt ngôn ngữ mặc định, lưu vào config và thông báo cho các UI listener (live refresh)."""
    global _current_lang
    if lang in SUPPORTED_LANGUAGES:
        _current_lang = lang
        _save_config()
        _notify_language_listeners()
    else:
        raise ValueError(f"Unsupported language: {lang}. Supported: {list(SUPPORTED_LANGUAGES.keys())}")


def get_language() -> str:
    """Lấy ngôn ngữ hiện tại."""
    return _current_lang


def toggle_language() -> str:
    """Chuyển đổi ngôn ngữ giao diện giữa vi ⇄ en (trả về ngôn ngữ mới)."""
    next_lang = "en" if _current_lang == "vi" else "vi"
    set_language(next_lang)
    return next_lang


def study_mode_labels(lang: str) -> dict:
    """Nhãn 5 chế độ học (qa/vn/wb/pron/lg) theo ngôn ngữ học + ngôn ngữ UI hiện tại.

    VD (lang=japanese): vi → "1. Nhật→Việt", en → "1. Japanese→English".
    """
    src = {
        "japanese": t("lang_src_ja"),
        "chinese": t("lang_src_zh"),
        "korean": t("lang_src_ko"),
    }.get(lang, t("lang_src_ja"))
    tgt = t("lang_tgt")
    pron = {
        "japanese": t("mode_label_pron_ja"),
        "chinese": t("mode_label_pron_zh"),
        "korean": t("mode_label_pron_ko"),
    }.get(lang, t("mode_label_pron_ja"))
    return {
        "qa": f"1. {src}→{tgt}",
        "vn": f"2. {tgt}→{src}",
        "wb": f"3. {t('mode_label_wb')}",
        "pron": f"4. {pron}",
        "lg": f"5. {t('mode_label_lg')}",
    }


# ═══════════════════════════════════════════════════════════
#  LANGUAGE CHANGE LISTENERS (live refresh UI)
# ═══════════════════════════════════════════════════════════

_language_listeners = []


def add_language_listener(callback):
    """Đăng ký callback được gọi mỗi khi ngôn ngữ thay đổi (để UI refresh mượt mà)."""
    if callback not in _language_listeners:
        _language_listeners.append(callback)


def remove_language_listener(callback):
    """Hủy đăng ký callback."""
    try:
        _language_listeners.remove(callback)
    except ValueError:
        pass


def _notify_language_listeners():
    """Gọi tất cả listener đã đăng ký (mỗi listener một lần, không chặn luồng chính)."""
    for cb in list(_language_listeners):
        try:
            cb()
        except Exception:
            pass


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
