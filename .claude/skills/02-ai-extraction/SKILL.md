---
name: ai-extraction
description: Lõi AI của add-on — utils/ai_extractor.py (2,2xx dòng). Config, encryption, HTTP, cache, prompts (japanese/chinese/korean), extract/chat, history. Đọc khi sửa bất cứ thứ gì liên quan AI.
---

# 🧠 SKILL-02: AI EXTRACTION CORE (`utils/ai_extractor.py`)

> OpenAI-compatible API (DeepSeek/OpenAI/Ollama/LM Studio/OpenRouter/Claude-proxy).
> ⚠️ **Đọc file này theo vùng, KHÔNG đọc trọn 2,2xx dòng.**

## CẤU TRÚC THEO VÙNG (line)

| Vùng | Dòng | Nội dung |
|------|------|----------|
| Encryption API key | 39-96 | `_get_machine_key`:39, `_derive_fernet_key`:46, `_encrypt_api_key`:59, `_decrypt_api_key`:77 (auto-detect `f:`/`x:`/plaintext) |
| HTTP helper | 114-209 | `_pick_ssl_context`:114 (local=no-verify), `_http_post_json`:125 (pool + chunked + retry) |
| Config | 227-321 | `_load_config`:227, `_save_config`:237, `get_api_config`:253, `save_api_config`:284, `_apply_reasoning_effort`:313 |
| Cost tracking | 347-378 | `_calculate_cost`:353, `_format_token_report`:370, `_DEEPSEEK_PRICING`:347 |
| Cache | 385-430 | `_ai_cache_key`:388, `_ai_cache_get`:393, `_ai_cache_set`:408, `clear_cache`:425, `_PROMPT_VERSION`:385 |
| JSON templates + prompts | 480-690 | `_JAPANESE_JSON_TEMPLATE`:480, `_KOREAN_JSON_TEMPLATE`:511, `_SYSTEM_PROMPTS`:544, `_JSON_TEMPLATES`:550, `_JAPANESE_GRAMMAR_JSON_TEMPLATE`:565, `_KOREAN_GRAMMAR_JSON_TEMPLATE`:639, `_GRAMMAR_SYSTEM_PROMPTS`:677, `_GRAMMAR_JSON_TEMPLATES`:683 |
| File extraction | 732-900 | `extract_text_from_file`:732 (txt/md/csv/pdf/docx/xlsx), `extract_text_from_files`:785, `_MAX_EXISTING_SHOWN`:902 (=400), `_format_existing_context`:905 |
| Vocab extract | 948-1095 | `extract_vocabulary_with_ai`:948 (core), `_parse_ai_json_with_comment`:1097 |
| Chat | 1157-1460 | `query_anki_context`:1157, `_build_anki_context_text`:1231, `chat_with_ai`:1320 |
| Long text | 1462-1547 | `extract_vocabulary_long_text`:1462 (chunk → gọi lại core) |
| Grammar extract | 1549-1828 | `extract_grammar_with_ai`:1549, `extract_grammar_long_text`:1704 |
| Import history | 1830-2xxx | `init_import_history`:1830, `add_to_import_history`:1963, `get_import_history`:2036, `search_import_history`:2099, `get_history_summary_text`:2144 |

## API CÔNG KHAI (dùng từ nơi khác)

```python
get_api_config() -> dict          # api_key(decrypted), api_base, model, temperature, max_tokens, max_chars, chunk_size, reasoning_effort
save_api_config(api_key, api_base, model, temperature=0.3, max_chars=45000, chunk_size=8000, reasoning_effort="")
extract_vocabulary_with_ai(text, lang, custom_instruction="", existing_words=None, progress_callback=None, force_refresh=False, token_callback=None) -> list[dict]
extract_vocabulary_long_text(text, lang, custom_instruction="", existing_words=None, chunk_size=None, progress_callback=None, force_refresh=False) -> list[dict]
extract_grammar_with_ai(text, lang, custom_instruction="", existing_patterns=None, progress_callback=None, force_refresh=False, token_callback=None) -> list[dict]
extract_grammar_long_text(text, lang, custom_instruction="", existing_patterns=None, chunk_size=None, progress_callback=None, force_refresh=False) -> list[dict]
chat_with_ai(user_message, lang="japanese", conversation_history=None, progress_callback=None) -> dict{reply, vocab_json, token_info, error}
query_anki_context(user_message, lang="japanese") -> dict   # context Anki thông minh
extract_text_from_file(filepath) -> str    # trích text file đính kèm
extract_text_from_files(filepaths) -> list[(name, text)]
get_json_template(lang) / get_grammar_json_template(lang) -> str
init_import_history(force_rescan=False) / add_to_import_history(vocab_list, lang, deck_name="", source="manual")
get_history_summary_text(lang=None, max_words_for_ai=50) -> str
clear_cache() / clear_import_history()
```

## PHƯƠNG THỨC GỌI API (bắt buộc giữ nguyên)

```python
# GET config → build messages → payload → _http_post_json → parse
cfg = get_api_config()
url = f"{cfg['api_base'].rstrip('/')}/chat/completions"
headers = {"Content-Type":"application/json", "Authorization": f"Bearer {cfg['api_key']}"}
payload = {"model": cfg["model"], "messages": messages, "temperature": cfg.get("temperature",0.3), "max_tokens": cfg.get("max_tokens",8192)}
_apply_reasoning_effort(payload, cfg)          # thêm reasoning_effort nếu cấu hình
_timeout = 600 if "reasoner" in cfg["model"] else 300
body = _http_post_json(url, payload, headers, timeout=_timeout, progress_callback=pc)
```

## CACHE (QUAN TRỌNG — TIẾT KIỆM TOKEN)

- Cache AI kết quả: `utils/ai_cache/`, key = `_ai_cache_key(text, lang, instruction, existing_hash)`.
- **Bump `_PROMPT_VERSION` (`ai_extractor.py:385`) MỖI KHI sửa prompt/chiến lược** → invalidate toàn bộ cache cũ.
- Deck vocab cache nằm ở `utils/deck_cache.py` (incremental 5p + full 30p) — gọi `invalidate_deck_cache()` khi deck thay đổi.
- Import history: `utils/import_history.json` — AI dùng để tránh từ đã import.

## PROMPT & JSON TEMPLATE (nơi hay sửa)

- System prompt vocab: `_SYSTEM_PROMPTS[lang]` (544, gồm japanese/chinese/korean). Grammar: `_GRAMMAR_SYSTEM_PROMPTS[lang]` (677).
- JSON output template: `get_json_template(lang)` / `get_grammar_json_template(lang)` — gửi cho AI làm format chuẩn.
- `_format_existing_context(existing, text, label)` — CHỈ gửi từ trùng với text (tối ưu input), cap `_MAX_EXISTING_SHOWN=400`.
- Giữ prompt GỌN: output yêu cầu explanation ≤2 câu, ví dụ 5-12 từ (kiểm bởi tests/test_token_optimization.py).

## TRAPS (lỗi thường gặp)

1. **JSON output bị cắt** (DeepSeek ~8192 token): chunk mặc định 8k, cap 15k. `_check_truncated_output`:324 cảnh báo. → Đừng tăng chunk >15k.
2. **Reasoner model content rỗng**: fallback lấy `reasoning_content` (1055, 1407). Giữ logic này.
3. **API key encryption**: `save_api_config` mã hóa `f:`/`x:`; `get_api_config` decrypt. Không lưu plaintext mới.
4. **max_chars sàn 10k / chunk sàn 3k** — bị clamp trong `get_api_config` (257-263). Test `test_length_and_reasoning.py` kiểm tra.
5. **Retry/timeout**: `_http_post_json` có retry; model reasoner timeout 600s.

## VERIFY SAU KHI SỬA

```
python -m pytest tests/test_token_optimization.py tests/test_length_and_reasoning.py tests/test_file_extract.py -v
python -m pytest tests/test_grammar.py -v
```
