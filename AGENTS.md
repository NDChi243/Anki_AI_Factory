# AGENTS.md — AnkiTool Multi-Language V17.1

> Điểm vào cho mọi AI agent (Claude Code, Cursor, Copilot, Codex...).
> **Hệ thống kiến thức đầy đủ nằm trong `.claude/` — đọc theo progressive disclosure để tiết kiệm token.**

## QUY TRÌNH BẮT BUỘC (tiết kiệm token tối đa)

1. Đọc [`.claude/CLAUDE.md`](.claude/CLAUDE.md) (~1.5k token) — chứa luật vàng + index skills.
2. Chọn ĐÚNG 1 skill trong `.claude/skills/` theo việc cần làm.
3. Dùng `file:line` trong skill để đọc đúng đoạn code cần — **KHÔNG đọc trọn file 2000 dòng**.
4. Sửa xong → chạy pytest (xem skill 10).

## INDEX NHANH

| Việc cần làm | Skill |
|--------------|-------|
| Hiểu cấu trúc dự án | `.claude/skills/01-project-map/SKILL.md` |
| Sửa AI/prompt/cache | `.claude/skills/02-ai-extraction/SKILL.md` |
| Sửa batch/deck organize | `.claude/skills/03-batch-processing/SKILL.md` |
| Sửa audio/TTS | `.claude/skills/04-audio-tts/SKILL.md` |
| Sửa thread nền | `.claude/skills/05-workers/SKILL.md` |
| Sửa UI/theme/i18n | `.claude/skills/06-ui-layer/SKILL.md` |
| Sửa/ thêm ngôn ngữ | `.claude/skills/07-language-config/SKILL.md` |
| Sửa template thẻ/CSS/JS | `.claude/skills/08-card-templates/SKILL.md` |
| Sửa json_parser/logger/cache | `.claude/skills/09-utils/SKILL.md` |
| Chạy/viết test | `.claude/skills/10-testing/SKILL.md` |
| Nâng cấp version/release | `.claude/skills/11-upgrade-playbook/SKILL.md` |
| 🐞 Tìm/sửa BUG (đọc log, root cause) | `.claude/skills/12-debugging/SKILL.md` |

## CẤU TRÚC TỔNG QUAN (tóm tắt 1 dòng)

`__init__.py` (AnkiSmartFactory) → `Language/`, `mode/`, `audio/`, `utils/`, `workers/`, `ui/`, `hooks/reviewer.py`. Version 17.1.0, entry `start_smart_factory()` (`__init__.py:2430`), shortcut `Ctrl+Shift+I`.

> Lưu ý: `CODE_MAP.md`/`UPGRADE_GUIDE.md` ở root là tài liệu cũ — dùng `.claude/` làm nguồn chính thức.
