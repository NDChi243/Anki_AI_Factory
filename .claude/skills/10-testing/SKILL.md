---
name: testing
description: Hệ thống test — tests/ (56+ tests). Cách chạy, mock Anki, viết test mới. Đọc TRƯỚC KHI báo xong bất kỳ task nào.
---

# 🧪 SKILL-10: TESTING

> pytest. Tests KHÔNG cần Anki chạy — mock `aqt`/`mw`. Test file tự chứa helper/mock (không import aqt ở top-level).

## CÁCH CHẠY

```bash
python -m pytest tests/ -v                  # toàn bộ
python -m pytest tests/test_json_parser.py -v   # 1 file
python -m pytest tests/test_batch_processor.py::TestSmartGroupWords -v  # 1 class
```

## BẢN ĐỒ TEST FILE

| File | Test những gì |
|------|---------------|
| `test_json_parser.py` | safe_parse_json — hợp lệ/rác/nested/unicode/edge cases |
| `test_audio_engine.py` | speed_to_edge_rate, get_voice_options (copy hàm pure vào test để không import aqt) |
| `test_batch_processor.py` | parse_word_list (mọi delimiter), smart_group_words, estimate_batch_cost, _fallback_deck_organization |
| `test_grammar.py` | LANG_GRAMMAR_CONFIG, grammar templates, css, prompts, batch grammar |
| `test_i18n.py` | t(), set_language, persistence, đủ key vi+en |
| `test_token_optimization.py` | _format_existing_context, _build_batch_user_prompt, prompt compactness, cache version |
| `test_length_and_reasoning.py` | get_api_config sanitize/clamp, reasoning_effort, chunk config, chat cap |
| `test_file_extract.py` | extract_text_from_file (txt/md/csv/...), extract_text_from_files |
| `test_factory_state.py` | Lưu/khôi phục state 2 luồng × 2 ngôn ngữ (factory_state.json) |
| `test_comprehensive.py` | AiChatDialog format, ImportWorker/AiExtractThread/PreviewThread/DeckScanWorker init, Encryption round-trip, End-to-end flows |
| `test_integration.py` | ImportWorker, threads, speed, voice options, safe_parse_json AI output |

## MOCK ANKI (pattern chuẩn)

```python
# Không import aqt. Module dùng Anki phải được test qua:
# 1) Hàm pure (copy logic hoặc import có guard) — vd speed_to_edge_rate
# 2) Mock signal/thread — vd MockSignal class (test_comprehensive.py:19)
# 3) Import nội bộ trong hàm test (workers.import_worker) — vd test_comprehensive.py:51
class MockSignal:
    def __init__(self, *types): self._slots = []
    def connect(self, slot): self._slots.append(slot)
    def emit(self, *args, **kwargs):
        for s in self._slots: s(*args, **kwargs)
```

## VIẾT TEST MỚI (checklist)

1. Đặt trong file phù hợp theo bảng trên.
2. Hàm pure → test trực tiếp; hàm dùng Anki/thread → mock hoặc import nội bộ.
3. Test BẢO VỆ bất biến quan trọng:
   - Encryption round-trip (`_encrypt_api_key`/`_decrypt_api_key`)
   - `_PROMPT_VERSION` bump (test_token_optimization.py::TestCacheVersion)
   - sanitize config (test_length_and_reasoning.py)
4. Đặt tên rõ ràng `test_<hành vi>`.

## SAU KHI SỬA CODE (bắt buộc)

```
python -m pytest tests/ -v
```
Phải XANH toàn bộ trước khi attempt_completion. Nếu test cũ fail do thay đổi hành vi CỐ Ý → cập nhật test tương ứng và ghi rõ lý do.

## THÊM: KIỂM TRA BẰNG TAY (Anki thật)

- Import add-on → Tools → AnkiTool Multi-Lang V16 (Ctrl+Shift+I)
- Test AI extract, import JSON, audio, reviewer (speed control, letter gap)
- Kiểm tra model name / migration nếu đổi version
