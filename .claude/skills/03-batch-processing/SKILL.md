---
name: batch-processing
description: Xử lý danh sách từ vựng LỚN qua AI — utils/batch_processor.py (969 dòng). Parse, smart grouping, batch AI calls, deck organization. Đọc khi sửa Batch dialog / hai-pass AI.
---

# 🚀 SKILL-03: BATCH PROCESSING (`utils/batch_processor.py`)

> Chiến lược: SMART CHUNKING (30-80 từ/batch) → TWO-PASS AI (Pass1 enrich vocab, Pass2 organize decks) → RATE LIMITING → CACHE từng batch (14 ngày).

## HẰNG SỐ (đầu file, dòng 37-43)

| Hằng | Giá trị | Dòng |
|------|---------|------|
| `DEFAULT_BATCH_SIZE` | 80 | 37 |
| `MAX_WORDS_PER_REQUEST` | 100 | 38 |
| `MIN_DELAY_BETWEEN_BATCHES` | 1.5s | 39 |
| `MAX_RETRIES` | 3 | 40 |
| `RETRY_BASE_DELAY` | 2.0s | 41 |
| `CACHE_TTL` | 14 ngày | 43 |

## API CÔNG KHAI

```python
parse_word_list(raw_text, lang="japanese") -> list[{front, meaning, level, topic}]
smart_group_words(words, batch_size=80) -> list[list]           # nhóm theo level/topic, sort
process_large_word_list(raw_text, lang, custom_instruction="", existing_words=None,
                        batch_size=80, progress_callback=None, should_abort=None, grammar=False) -> list[dict]
organize_decks_with_ai(vocab_list, lang, progress_callback=None) -> dict{suggestion, decks:[{parent, sub_decks}]}
create_decks_from_organization(organization, vocab_list, lang, progress_callback=None) -> dict{deck_name: deck_id}
estimate_batch_cost(word_count, lang, batch_size=80) -> dict    # ước tính USD + thời gian
# internal: _build_batch_user_prompt:210, _call_ai_for_batch:304, _batch_cache_key:411/_get:419/_set:435, _fallback_deck_organization:773
```

## DATA FLOW (`process_large_word_list` — dòng 457)

```
1. parse_word_list → words
2. Lọc từ trùng existing_words (lowercase)
3. smart_group_words → batches
4. Với mỗi batch:
   - check _batch_cache_get (grammar-aware)
   - _call_ai_for_batch → AI enrich (system prompt vocab/grammar + JSON template)
   - Lọc trùng (seen_fronts + existing_set)
   - _batch_cache_set
   - Nếu >=3 lỗi → raise RuntimeError dừng
   - sleep(MIN_DELAY_BETWEEN_BATCHES) giữa batch (rate limit)
5. Trả all_vocab
```

## DECK ORGANIZATION (Pass 2, dòng 648)

- `organize_decks_with_ai`: gửi `word_summaries` (front|meaning|level|topic) — sampling nếu >500 từ, `MAX_WORDS_FOR_ORG=500`.
- Prompt system: `_DECK_ORGANIZER_SYSTEM_PROMPT` (614). Output JSON: `{suggestion, decks:[{parent, sub_decks:[{name, description, word_count, words}]}]}`.
- **Fallback quan trọng**: mọi lỗi → `_fallback_deck_organization` (773) nhóm theo topic→level. KHÔNG được để crash.
- `create_decks_from_organization` (860): tạo parent/sub bằng `mw.col.decks.id(name)`; parent tên `Parent::Sub`. Import `aqt` bên trong try (tránh top-level).

## TRAPS

1. **Sửa prompt batch** → phải bump `_PROMPT_VERSION` (xem SKILL-02) vì batch cache dùng riêng key nhưng version chung `_PROMPT_VERSION`.
2. **Không gửi quá 100 từ/request** (`MAX_WORDS_PER_REQUEST`).
3. `parse_word_list` có nhánh JSON (`raw_text.startswith("[")`) — giữ nguyên để nhận JSON từ AI Chat.
4. **Grammar mode**: `grammar=True` đổi label + dùng prompt ngữ pháp + cache key riêng.

## VERIFY

```
python -m pytest tests/test_batch_processor.py tests/test_comprehensive.py tests/test_grammar.py -v
```
