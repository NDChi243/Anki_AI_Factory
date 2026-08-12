---
name: debugging
description: Quy trình DEBUG nhanh cho AnkiTool — tìm root cause từ triệu chứng/lỗi, đọc log, cô lập vùng code, sửa + verify. Đọc TRƯỚC khi xử lý BUG/CRASH/behavior sai.
---

# 🐞 SKILL-12: DEBUGGING (Tìm & Sửa Bug Nhanh)

> Mục tiêu: **tốn ít token nhất** để tìm root cause và sửa đúng. KHÔNG đọc trọn file 2000 dòng — nhảy thẳng tới dòng nghi ngờ qua `file:line`.

## 0. TƯ DUY TRƯỚC KHI DEBUG (10 giây)

1. **Bug thuộc tầng nào?** AI / Batch / Audio / Worker / UI / Card / Utils / i18n → đọc skill tương ứng (INDEX trong `CLAUDE.md`).
2. **Có log không?** → Đọc log TRƯỚC (phần 2). Log thường chỉ rõ file + dòng + exception.
3. **Có test nào bảo vệ không?** → Chạy test liên quan TRƯỚC để biết mình có phá vỡ bất biến không.
4. **Sửa NHỎ, đúng root cause** — không sửa bề mặt (surface) khi nguyên nhân nằm sâu.

## 1. BẢN ĐỒ VÙNG LỖI (triệu chứng → nơi tra)

| Triệu chứng | Đọc skill | Nơi nghi ngờ |
|-------------|-----------|--------------|
| AI trả JSON sai/cắt | 02 | `utils/ai_extractor.py` — chunk, `_check_truncated_output:324`, reasoner fallback `:1055/:1407` |
| AI lỗi API key/HTTP | 02 | `get_api_config:253`, `_http_post_json:125`, `_pick_ssl_context:114` |
| AI trả cache cũ/sai | 02 | `_PROMPT_VERSION:385`, `_ai_cache_key:388`, `prompt_config.get_prompt_signature()` |
| Batch sai grouping/crash | 03 | `smart_group_words`, `_call_ai_for_batch:304`, `_fallback_deck_organization:773` |
| Không có audio / sai giọng / sai tốc độ | 04 | `audio/engine.py:97` router, `speed_to_edge_rate:117`, `VOICE_OPTIONS:12` |
| Crash trong thread / UI đơ | 05 | `run()` các worker, `error.emit`, signal connect trong `__init__.py` |
| Lỗi hiển thị / i18n / theme | 06 | `ui/*.py`, `t()` trong `utils/i18n.py`, `ui/theme.py` |
| Field/card sai | 08 | `mode/card_render.py`, `mode/templates.py`, `prompt_config.get_field_map` |
| Parse JSON crash | 09 | `safe_parse_json:13` (`utils/json_parser.py`) |
| Cache deck cũ | 09 | `utils/deck_cache.py` — `invalidate_deck_cache:93`, TTL incremental 5p / full 30p |
| Review không có speed/LG/combo | 05 | `hooks/reviewer.py:45` register_hooks |
| Overview sai | 05 | `hooks/overview_mode.py` register_overview_hooks |

## 2. ĐỌC LOG (làm ĐẦU TIÊN — ít token nhất)

### File log
- Vị trí: **`anki_tool.log`** (cùng thư mục addon = `c:/Users/nguye/AppData/Roaming/Anki2/addons21/Anki_AI_Smart Factory/anki_tool.log`).
- Rotation: 5MB × 3 file cũ (`anki_tool.log.1`, `.2`, `.3`).
- Console: hiện trong Anki **Tools → Debug → Debug Console** (stdout).

### Cách đọc log hiệu quả (trong terminal)
```powershell
# Tìm ERROR/WARNING mới nhất (ưu tiên trước)
Get-Content "anki_tool.log" -Tail 200 | Select-String -Pattern "ERROR|WARNING|Traceback|Exception"
# Tìm theo từ khóa triệu chứng
Select-String -Path "anki_tool.log" -Pattern "audio|api_key|timeout|json" -SimpleMatch
# Xem 50 dòng cuối đầy đủ (context quanh lỗi)
Get-Content "anki_tool.log" -Tail 50
```

### Cách thêm log tạm (khi log hiện chưa đủ)
```python
from utils.logger import get_logger
logger = get_logger()
logger.debug("DEBUG-VAR: %s", variable)   # level DEBUG cần setup_logging(level="DEBUG")
logger.warning("TRACE-%s: %s", step, value)  # level WARNING hiện rõ trong file
```
> ⚠️ **Sửa xong phải XÓA log debug tạm** — quy tắc vàng #5: mọi log qua `get_logger()`, không `print()`.

## 3. QUY TRÌNH TÌM ROOT CAUSE (3 bước — token tối thiểu)

1. **Tái hiện lỗi tối thiểu**: tìm input nhỏ nhất gây lỗi (1 từ / 1 câu / 1 deck nhỏ). Nếu có test → viết test tái hiện.
2. **Cô lập vùng**: dùng stack trace trong log → `file:line` → `read_file` indentation mode (đọc đúng khối hàm, KHÔNG đọc trọn file).
3. **Xác định root cause ≠ symptom**:
   - Symptom ở UI, root cause ở worker/utils → đọc data flow (SKILL-01 phần DATA FLOW).
   - Symptom ở output AI, root cause ở prompt/cache → kiểm tra `_PROMPT_VERSION` / `prompt_signature`.
   - Symptom crash lúc review → hook `reviewer.py` vs model name (thay đổi version).

## 4. SỬA THEO QUY TẮC VÀNG (AGENTS.md)

1. Đọc skill vùng trước (bảng phần 1) → nhảy thẳng `file:line`.
2. Tuân thủ QUY TẮC VÀNG trong [`CLAUDE.md`](../CLAUDE.md) (không `aqt` top-level, không `print`, không bare `except`, thread-safe, i18n `t()`).
3. Sửa prompt → bump `_PROMPT_VERSION` hoặc qua `prompt_config` (tự invalidate).
4. Thêm/sửa note trong deck → gọi `invalidate_deck_cache()`.
5. **Bare `except:` CẤM** — luôn `except Exception:` + log (để bug sau này tái hiện được).

## 5. VERIFY (bắt buộc trước khi báo xong)

```bash
python -m pytest tests/ -v                       # toàn bộ — phải XANH
# Hoặc tối thiểu (theo vùng đã sửa):
python -m pytest tests/test_<vùng>.py -v         # xem bảng SKILL-10
```

## 6. KHI BẾ TẮC (thoát khỏi vòng lặp)

- **Bug phụ thuộc Anki thật** (không test được): kiểm tra bằng tay theo SKILL-10 mục "KIỂM TRA BẰNG TAY", ghi log `WARNING` quanh nghi vấn, yêu cầu user thao tác lại + gửi log.
- **Đổi hành vi CỐ Ý**: cập nhật test tương ứng + ghi rõ lý do (SKILL-10).
- **Nghi circular import**: kiểm tra dependency graph SKILL-01 (`utils/__init__.py` ↔ `ai_extractor`).

## TÓM TẮT LUỒNG NHANH

```
BÁO BUG → Đọc LOG (ankitool.log) → Xác định file:line → Đọc skill vùng → read_file(indentation) đúng hàm
       → Sửa root cause → pytest XANH → attempt_completion
```
