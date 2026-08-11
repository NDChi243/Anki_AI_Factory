---
name: audio-tts
description: Hệ thống audio/TTS — audio/engine.py (router + voice/speed) + audio/tts.py (Edge/gTTS/VoiceVox). Đọc khi sửa giọng đọc, tốc độ, audio generation.
---

# 🎤 SKILL-04: AUDIO & TTS

## `audio/engine.py` (122 dòng) — ROUTER & STATE

| Symbol | Dòng | Ghi chú |
|--------|------|---------|
| `VOICE_OPTIONS` | 12 | dict `{ja: [...], zh: [...], ko: [...]}` — **ja chỉ còn Nanami & Keita** (Microsoft loại AoiNeural/DaichiNeural 7/2026); zh có 8 giọng (CN/TW/HK); ko có 4 giọng (SunHi/InJoon/JiMin/Hyunsu) |
| `VOICE_SAMPLE` | 34 | text mẫu preview (ja/zh/ko) |
| `_selected_voice` + lock | 40-41 | ⚠️ thread-safe bắt buộc |
| `_default_speed` + lock | 44-45 | ⚠️ thread-safe bắt buộc |
| `get_voice_options(lang)` | 48 | trả VOICE_OPTIONS.get(lang, []) |
| `get_selected_voice(lang)` | 53 | default = giọng đầu |
| `set_selected_voice(lang, id)` | 62 | |
| `get_default_speed(lang)` | 68 | default 1.0 |
| `set_default_speed(lang, spd)` | 74 | |
| `_MODEL_LANG_MAP` | 81 | model name → lang code (ja/zh/ko, gồm cả V17 + Grammar models) |
| `detect_lang_from_model(name)` | 92 | dùng bởi reviewer hook |
| `get_audio_multilang(text, lang, voice=None, rate=None)` | 97 | **Router chính**: Edge → (fallback) gTTS (dùng lang_code). rate = edge rate string |
| `speed_to_edge_rate(speed)` | 117 | (0.25-4.0) → "-50%"..."+100%", clamp |

## `audio/tts.py` (174 dòng) — PROVIDERS

| Symbol | Dòng | Ghi chú |
|--------|------|---------|
| `_install_edge_tts()` | 33 | pip auto-install edge-tts nếu thiếu |
| `_install_gtts()` | 47 | pip auto-install gtts |
| `get_audio_edge_tts(text, voice, lang="ja", rate=None)` | 64 | trả `[sound:filename]` tag; có `_audio_query_cache` (27) |
| `get_audio_gtts(text, lang="ja")` | 106 | fallback |
| `get_audio_voicevox(text, speaker_id=3)` | 137 | local JP, dùng `mw.col.media` |

## LUỒNG GỌI AUDIO (IMPORT)

```python
# ImportWorker (workers/import_worker.py) gọi qua _generate_audio_safe:183
# PreviewThread (workers/ai_workers.py:20) gọi get_audio_edge_tts trực tiếp + speed_to_edge_rate
# Reviewer hook dùng detect_lang_from_model + get_default_speed để inject speed control
get_audio_multilang(text, lang, voice, rate)   # engine.py:97 — điểm vào chính
```

## TRAPS

1. **Thêm giọng**: chỉ thêm vào `VOICE_OPTIONS` — phải chắc chắn giọng còn tồn tại trên Microsoft Edge (AoiNeural/DaichiNeural từng bị loại → lỗi khi gọi).
2. **Thread-safe**: mọi đọc/ghi `_selected_voice`/`_default_speed` PHẢI trong `with _lock:`.
3. **Không import Anki (aqt) ở top-level** trong tts.py ngoài `mw` (đã import từ aqt — giữ nguyên).
4. `get_audio_multilang` fallback gTTS dùng `lang_code` (`"ja"`/`"zh"`/`"ko"`) — V17 đã sửa hardcode `"ja"`.
5. **Audio luôn sinh trong thread** (import/preview) — không gọi sync trong UI thread.

## VERIFY

```
python -m pytest tests/test_audio_engine.py tests/test_integration.py -v
```
