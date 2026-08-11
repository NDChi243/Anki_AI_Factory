---
name: upgrade-playbook
description: Quy trình nâng cấp version, bảo trì, release — checklist toàn diện + task cards tái sử dụng. Đọc khi thực hiện bất kỳ thay đổi lớn nào.
---

# 🚀 SKILL-11: UPGRADE & MAINTENANCE PLAYBOOK

## 1. NÂNG CẤP VERSION (VD V16.0 → V17.0)

> Đổi version là thao tác LAN RỘNG — dùng checklist này, đừng quên chỗ nào.

### Checklist bắt buộc

- [ ] **`manifest.json`**: `"version": "16.0.0"` → `"17.0.0"`
- [ ] **`Language/japanese.py`** + **`Language/chinese.py`**: `model_name` `...V16.0...` → `...V17.0...` (cả `LANG_CONFIG` và `GRAMMAR_CONFIG`), thêm model cũ vào `old_model_names`
- [ ] **`audio/engine.py:_MODEL_LANG_MAP`** (dòng 81): thêm mapping model cũ→lang (nếu model mới có format khác)
- [ ] **`utils/i18n.py`**: chuỗi `V16.0` trong title → `V17.0` nếu có
- [ ] **`__init__.py`**: window title (dòng 68) + chuỗi hiển thị version
- [ ] **`README.md`** badge version + nội dung
- [ ] **`CHANGELOG.md`**: thêm section `## [V17.0] — <date>` ở đầu (format giữ nguyên: ✨ Added / 🔧 Changed / 🐛 Fixed)
- [ ] **`.claude/`**: cập nhật version trong CLAUDE.md + mọi chỗ nhắc `V16.0`

### Migration Note Type

- `_get_or_migrate_model` (`__init__.py:1236`): nếu model cũ trong `old_model_names` → đổi tên/giữ dữ liệu. Giữ nguyên logic này.
- Model names phải ĐỒNG BỘ giữa `Language/*.py` và `audio/engine.py:_MODEL_LANG_MAP`.

## 2. BẢO TRÌ ĐỊNH KỲ

| Việc | Tần suất | Skill |
|------|----------|-------|
| Chạy toàn bộ pytest | mỗi release | 10 |
| Kiểm tra giọng TTS còn tồn tại (Microsoft loại giọng thường xuyên) | mỗi quý | 04 |
| Kiểm tra API provider pricing/endpoint | mỗi release | 02 |
| `pre-commit` (black/ruff) chạy sạch | mỗi commit | 11 |
| Rà soát `except:` rộng / `print()` | mỗi release | 09 |
| Verify cache invalidation khi đổi prompt | mỗi lần sửa prompt | 02 |

## 3. TASK CARDS TÁI SỬ DỤNG (copy-paste)

### TC-1: Thêm provider AI mới
```
Thêm preset provider mới vào ui/ai_settings.py (danh sách presets) + manifest.json config.ai_providers.
Đảm bảo get_api_config/save_api_config không hardcode tên provider.
Test bằng _test_ai_connection (ui/ai_settings.py:204).
```
**Đụng**: `ui/ai_settings.py`, `manifest.json` | **Verify**: test thủ công kết nối

### TC-2: Thêm 1 field vào Note Type (vocab hoặc grammar)
```
1. Language/{lang}.py: thêm field vào all_fields + json_field_map + audio_fields (nếu audio)
2. mode/templates.py: thêm {{Field}} vào template mong muốn
3. mode/css.py: thêm class nếu cần style
4. utils/ai_extractor.py: thêm key vào JSON template + prompt (nếu AI phải sinh field) + bump _PROMPT_VERSION
```
**Đụng**: Language/, mode/, ai_extractor | **Verify**: test_grammar + test thủ công "Tái Tạo Model"

### TC-3: Sửa system prompt AI (vocab/grammar/chat)
```
1. utils/ai_extractor.py: sửa _SYSTEM_PROMPTS[lang] (497) / _GRAMMAR_SYSTEM_PROMPTS[lang] (590)
2. BUMP _PROMPT_VERSION (371) — quan trọng, invalidate cache
3. Đảm bảo prompt gọn: output explanation ≤2 câu, ví dụ 5-12 từ
4. Chạy tests/test_token_optimization.py (kiểm tra độ compact)
```
**Verify**: `python -m pytest tests/test_token_optimization.py tests/test_length_and_reasoning.py -v`

### TC-4: Fix lỗi JSON bị cắt (tràn output token)
```
Nguyên nhân: chunk quá lớn > giới hạn output model (VD DeepSeek ~8192 token).
Fix: giảm chunk_size trong get_api_config (3k-15k, mặc định 8k) HOẶC prompt yêu cầu output ngắn.
Không tăng chunk > 15k. Giữ _check_truncated_output cảnh báo.
```
**Verify**: test_length_and_reasoning + test thủ công văn bản dài

### TC-5: Đổi cache TTL
```
AI cache: utils/ai_extractor.py _CACHE_DIR + cache funcs (379-409) — TTL đọc từ file cache
Deck cache: utils/deck_cache.py _DECK_CACHE_TTL (24) / _DECK_INCREMENTAL_TTL (25)
Batch cache: utils/batch_processor.py CACHE_TTL (43)
```

## 4. RELEASE CHECKLIST (cuối cùng)

```
[ ] python -m pytest tests/ -v  → 100% xanh
[ ] pre-commit run --all-files   → sạch (black, ruff)
[ ] Test trên Anki thật: mở Factory, AI extract, import, audio, review (speed control + letter gap)
[ ] CHANGELOG.md đã thêm version mới
[ ] manifest.json version khớp
[ ] Không có API key thật trong repo (ai_config.json đã .gitignore)
[ ] .claude/ skills đã cập nhật nếu cấu trúc thay đổi
```

## 5. PHẢN HỒI VÒNG ĐỜI (khi code thay đổi)

> Nếu task của bạn làm đổi line number/signature → **CẬP NHẬT lại skill tương ứng** trong `.claude/skills/` để giữ hệ thống luôn chính xác (chi phí thấp cho lần sau).
