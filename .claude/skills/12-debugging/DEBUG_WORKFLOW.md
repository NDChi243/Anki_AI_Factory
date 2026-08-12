# 🐞 DEBUG WORKFLOW — Quy Trình Debug Từng Bước (Token Tối Thiểu)

> Áp dụng cho MỌI bug. Mục tiêu: root cause trong ≤3 lượt đọc file, không đọc trọn source.

## BƯỚC 0 — NHẬN DẠNG LOẠI BUG (5 giây)

Khoanh vùng ngay bằng câu hỏi:
- **CRASH** (Anki đóng / exception trong debug console) → đọc log `anki_tool.log` + stack trace.
- **Behavior sai** (ra kết quả không đúng) → xác định output đúng vs sai, tìm nơi sinh output.
- **Hiệu năng / đơ** → thread + UI blocking (SKILL-05).
- **Chỉ trên Anki thật** (test xanh nhưng user báo lỗi) → dependency aqt, hook, model name, cache.

## BƯỚC 1 — ĐỌC LOG (nhanh nhất, làm ngay)

```powershell
Get-Content "anki_tool.log" -Tail 200 | Select-String -Pattern "ERROR|WARNING|Traceback|Exception"
```
- Log có format `[AnkiTool] 2026-08-12 ... [ERROR] module | message` + traceback → cho ngay `file:line`.
- Nếu không có log đủ → xem phần "thêm log tạm" trong `SKILL.md`.

## BƯỚC 2 — XÁC ĐỊNH VÙNG + ĐỌC ĐÚNG HÀM (không đọc trọn file)

1. Từ stack trace / triệu chứng → tra bảng "BẢN ĐỒ VÙNG LỖI" trong `SKILL.md` hoặc `COMMON_BUGS.md`.
2. Mở file + `read_file(mode="indentation", anchor_line=<dòng nghi ngờ>)` → đọc ĐÚNG khối hàm chứa dòng đó (không kéo theo 1000 dòng khác).
3. Theo dõi data flow ngược: hàm báo lỗi → nơi gọi nó → nơi gọi nó... (dùng `search_files` tìm nơi gọi).

**Ví dụ**: Bug "import không có audio".
```
Log: [ERROR] audio.tts | get_audio_edge_tts failed...
→ read_file audio/tts.py indentation anchor≈64 (hàm get_audio_edge_tts)
→ search_files "get_audio_edge_tts" → thấy ImportWorker._generate_audio_safe:183 gọi
→ read_file workers/import_worker.py indentation anchor=183 → xem try/except + lock
→ root cause: voice bị loại (C1) hoặc thread-safe (C4)
```

## BƯỚC 3 — TÁI HIỆN TỐI THIỂU (nếu có thể)

- **Hàm pure** (parse, speed, grouping): viết test nhỏ / chạy python inline để tái hiện:
```powershell
python -c "from utils.json_parser import safe_parse_json; print(safe_parse_json('[bad'))"
```
- **Hàm dùng Anki/thread**: dùng test hiện có (mở rộng test tái hiện) hoặc mock (SKILL-10 pattern `MockSignal`).
- **Chỉ Anki thật**: ghi log `WARNING` quanh nghi vấn → yêu cầu user thao tác + gửi log.

## BƯỚC 4 — SỬA ROOT CAUSE (theo bảng quy tắc)

- Sửa đúng nguyên nhân gốc, tôn trọng bất biến (đọc TRAPS của skill vùng).
- Các bất biến hay bị phá: `safe_parse_json` (F1), encryption round-trip (A3), `_PROMPT_VERSION` (A5), thread-safe lock (C4), không `aqt` top-level (E5).

## BƯỚC 5 — VERIFY

```bash
python -m pytest tests/ -v
```
- Phải XANH toàn bộ. Nếu test cũ fail do đổi hành vi CỐ Ý → cập nhật test + ghi rõ lý do.
- Chạy đúng test theo vùng (cột Verify trong `COMMON_BUGS.md`).

## BƯỚC 6 — GHI LẠI (trả nợ token cho lần sau)

1. Thêm bug vào `COMMON_BUGS.md` (bảng đúng vùng A-H).
2. Cập nhật line number trong skill vùng nếu code đổi.
3. Nếu bug tái phát được → viết test bảo vệ.

---

## VÍ DỤ ĐẦY ĐỦ (từ đầu đến cuối)

**Báo cáo**: "Mở Anki Tool → Batch → nhập 100 từ → chạy xong báo lỗi giữa chừng".

| Bước | Hành động | Token |
|------|-----------|-------|
| 1 | Đọc log: `ERROR batch_processor | _call_ai_for_batch failed: ... HTTP 429` | ~50 |
| 2 | `COMMON_BUGS.md` → B2 (rate limit) → `MIN_DELAY_BETWEEN_BATCHES:39` | ~30 |
| 3 | `read_file` indentation `batch_processor.py` quanh `_call_ai_for_batch:304` | ~200 |
| 4 | Root cause: delay bị bỏ qua khi batch nhỏ (điều kiện `if i < len(batches)-1`) | — |
| 5 | Sửa: thêm `sleep(MIN_DELAY)` đều mọi batch | — |
| 6 | `pytest tests/test_batch_processor.py -v` → XANH | — |
| 7 | Thêm dòng B7 vào `COMMON_BUGS.md` | ~20 |
