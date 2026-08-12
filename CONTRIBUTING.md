# 🤝 Hướng dẫn đóng góp — AnkiTool Multi-Language

Cảm ơn bạn quan tâm đóng góp! Dự án này được tổ chức để **AI agent (Claude Code, Cursor, Copilot…) và con người cùng bảo trì hiệu quả**.

## Quy trình bắt buộc

1. **Đọc [`AGENTS.md`](AGENTS.md)** → vào [`.claude/CLAUDE.md`](.claude/CLAUDE.md) (~1.5k token) → chọn **đúng 1 skill** trong `.claude/skills/` theo việc cần làm.
2. **Đọc đúng đoạn code** bằng `file:line` trong skill — không mở trọn file 2000 dòng.
3. Tuân thủ **quy tắc vàng** (xem `.claude/CLAUDE.md`):
   - Mọi UI qua `t()` (i18n) — không hardcode tiếng Việt.
   - Mọi log qua `get_logger()` — không `print()`.
   - Không dùng `except:` trần (phải `except Exception:` + log).
   - Thread-safe cho state chia sẻ (`threading.Lock`).
   - Sửa prompt → đổi prompt config (xem skill 02); sửa template thẻ → chạy skill 08.
4. **Chạy test trước khi báo xong**: `python -m pytest tests/ -q` (phải xanh).
5. Cập nhật `CHANGELOG.md` cho thay đổi đáng kể.

## Trước khi tạo Pull Request

- [ ] `python -m pytest tests/ -q` → **xanh** (CI cũng sẽ chạy lại).
- [ ] Test trên Anki thật (nếu thay đổi UI/hook/import).
- [ ] Cập nhật `CHANGELOG.md`.
- [ ] **KHÔNG commit** `utils/ai_config.json`, `utils/ai_prompts.json`, `utils/import_history.json`, `utils/ai_cache/`, `utils/factory_state.json`, `anki_tool.log` (đã nằm trong `.gitignore`).

## Cấu trúc nhanh

```
__init__.py   → AnkiSmartFactory (dialog chính) + entry start_smart_factory()
Language/     → config từng ngôn ngữ (Nhật/Trung/Hàn + ngữ pháp)
mode/         → template thẻ (HTML/CSS/JS games) + card_render.py
utils/        → AI extractor, batch, prompt_config, i18n, logger...
ui/           → dialog (ai_settings, prompt_editor, batch, history...)
workers/      → background threads
hooks/        → reviewer + overview hooks
tests/        → 338+ unit/integration tests
```
