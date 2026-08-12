# ✅ CHECKLIST — Debug Nhanh (in ra / đọc trước khi sửa)

> Tick từng dòng. Nếu bỏ qua dòng nào → dừng lại làm trước khi attempt_completion.

## TRƯỚC KHI SỬA

- [ ] Xác định **loại bug**: CRASH / behavior sai / hiệu năng / chỉ Anki thật
- [ ] **Đã đọc log** `anki_tool.log` (Tail 200 + grep ERROR/WARNING/Traceback) chưa?
- [ ] **Tra `COMMON_BUGS.md`** có bug giống chưa? (0 token nếu có sẵn)
- [ ] Xác định được **`file:line`** nghi ngờ (từ log/stack trace)?
- [ ] Đã chọn **đúng skill vùng** (01-11) + đọc TRAPS chưa?
- [ ] Có **test bảo vệ** vùng này không? Chạy trước để biết baseline?
- [ ] Đã tái hiện được **input tối thiểu** chưa?

## KHI SỬA

- [ ] Không `import aqt` ở top-level ngoài `__init__.py`
- [ ] Không `print()` — dùng `get_logger()`
- [ ] Không `bare except:` — luôn `except Exception:` + log
- [ ] State chia sẻ thread → có `threading.Lock` không?
- [ ] UI string → qua `t()` i18n, không hardcode tiếng Việt
- [ ] Sửa prompt code → đã bump `_PROMPT_VERSION`? (hoặc qua prompt_config tự invalidate)
- [ ] Thêm/sửa note deck → đã `invalidate_deck_cache()`?
- [ ] Đã XÓA log debug tạm chưa?

## SAU KHI SỬA (bắt buộc)

- [ ] `python -m pytest tests/ -v` → **XANH toàn bộ**
- [ ] Nếu đổi hành vi CỐ Ý → cập nhật test + ghi rõ lý do
- [ ] Kiểm tra bằng tay trên Anki thật (nếu bug chỉ tái hiện ở đó)
- [ ] **Đã thêm bug vào `COMMON_BUGS.md`**? (để lần sau 0 token)
- [ ] **Đã cập nhật line number** trong skill vùng nếu code đổi vị trí?
- [ ] Viết **test bảo vệ** nếu bug có thể tái phát

## NẾU BẾ TẮC > 3 lượt đọc file

- [ ] Dừng lại, xem lại data flow (SKILL-01) — có đang đọc nhầm tầng không?
- [ ] Kiểm tra **circular import** (utils/__init__ ↔ ai_extractor)
- [ ] Yêu cầu user gửi **log đầy đủ** (`anki_tool.log` hoặc Debug Console)
- [ ] Ghi log `WARNING` chi tiết hơn quanh nghi vấn, tái hiện lại
