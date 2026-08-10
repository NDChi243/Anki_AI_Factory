"""
Import Worker — Background thread for batch importing notes into Anki.
V16.0: Parallel audio generation via ThreadPoolExecutor (3-phase approach).
"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from aqt import mw
from aqt.qt import QThread, pyqtSignal
from anki.notes import Note

from audio import get_audio_multilang
from audio.engine import speed_to_edge_rate
from utils.logger import get_logger

logger = get_logger()

# Số worker tối đa cho audio generation (không nên quá cao để tránh rate-limit)
_MAX_AUDIO_WORKERS = 4


class ImportWorker(QThread):
    """Worker thread xử lý import hàng loạt (add/update + parallel audio)."""

    progress = pyqtSignal(int, str)  # current, status_text
    finished = pyqtSignal(dict)  # report
    error = pyqtSignal(str)

    def __init__(self, batch_data, config, deck_id, audio_options, speed=1.0):
        super().__init__()
        self.batch = batch_data
        self.cfg = config
        self.deck_id = deck_id
        self.do_vocab, self.do_ex1, self.do_ex2 = audio_options
        self.rate = speed_to_edge_rate(speed)
        self._is_running = True

    def run(self):
        report = {"added": 0, "updated": 0, "audio_gen": 0, "errors": 0}
        errors_detail = []
        audio_fields = self.cfg["audio_fields"]
        lang_code = self.cfg["lang_code"]
        total = len(self.batch)

        # ── Phase 1: Create/update notes, collect audio tasks ──────────
        audio_tasks = []  # List[(note, src_text, audio_fn)]
        notes_to_flush = []

        for i, d in enumerate(self.batch):
            if not self._is_running:
                break

            item = d["item"]
            action = d["action"]
            dk = self.cfg["detect_key"]
            front_disp = str(item.get(dk, item.get('front', ''))).strip()

            self.progress.emit(i + 1, f"📝 ({i+1}/{total}) {front_disp}")

            try:
                if action == "update":
                    note = mw.col.get_note(d["nid"])
                    for fn in d.get("update_fields", []):
                        is_audio = False
                        for idx2, (audio_fn, src_fn) in enumerate(audio_fields):
                            if fn == audio_fn:
                                is_audio = True
                                do_it = [self.do_vocab, self.do_ex1, self.do_ex2][min(idx2, 2)]
                                if do_it:
                                    try:
                                        src_text = note[src_fn].strip()
                                        if src_text:
                                            audio_tasks.append((note, src_text, audio_fn, lang_code))
                                    except Exception:
                                        pass
                                break
                        if not is_audio:
                            for jk, mapped_fn in self.cfg["json_field_map"].items():
                                if mapped_fn == fn and jk in item:
                                    note[fn] = str(item[jk])
                                    break
                    # Fill fields
                    self._fill_example_blanks(note, self.cfg.get("front_field", ""))
                    notes_to_flush.append(note)
                    report["updated"] += 1

                else:  # add
                    note = Note(mw.col, mw.col.models.by_name(self.cfg["model_name"]))
                    for jk, fn in self.cfg["json_field_map"].items():
                        if jk in item and fn in self.cfg["all_fields"]:
                            note[fn] = str(item[jk])

                    self._fill_example_blanks(note, self.cfg.get("front_field", ""))

                    # Collect audio tasks
                    for idx2, (audio_fn, src_fn) in enumerate(audio_fields):
                        do_it = [self.do_vocab, self.do_ex1, self.do_ex2][min(idx2, 2)]
                        try:
                            src_val = note[src_fn].strip()
                        except Exception:
                            src_val = ''
                        if do_it and src_val:
                            audio_tasks.append((note, src_val, audio_fn, lang_code))

                    mw.col.add_note(note, self.deck_id)
                    notes_to_flush.append(note)
                    report["added"] += 1

            except Exception as e:
                report["errors"] += 1
                errors_detail.append(f"• {front_disp}: {str(e)}")

        # ── Phase 2: Parallel audio generation ──────────────────────────
        if audio_tasks and self._is_running:
            self.progress.emit(total, f"🎤 Đang tạo {len(audio_tasks)} audio files ({_MAX_AUDIO_WORKERS} workers)...")
            audio_results = {}  # (note_id, audio_fn) → tag

            with ThreadPoolExecutor(max_workers=_MAX_AUDIO_WORKERS) as executor:
                futures = {}
                for idx, (note, src_text, audio_fn, lang) in enumerate(audio_tasks):
                    if not self._is_running:
                        break
                    fut = executor.submit(
                        _generate_audio_safe, src_text, lang, self.rate
                    )
                    futures[fut] = (note, audio_fn)

                completed = 0
                for fut in as_completed(futures):
                    if not self._is_running:
                        break
                    note, audio_fn = futures[fut]
                    try:
                        tag = fut.result()
                        if tag:
                            note[audio_fn] = tag
                            report["audio_gen"] += 1
                    except Exception:
                        pass
                    completed += 1
                    if completed % 10 == 0:
                        self.progress.emit(total, f"🎤 Audio: {completed}/{len(audio_tasks)}")

        # ── Phase 3: Flush all notes ────────────────────────────────────
        if self._is_running:
            self.progress.emit(total, "💾 Đang lưu notes...")
            for note in notes_to_flush:
                try:
                    note.flush()
                except Exception:
                    pass

        if errors_detail:
            report["errors_detail"] = errors_detail[:10]

        self.finished.emit(report)

    def stop(self):
        self._is_running = False

    @staticmethod
    def _fill_example_blanks(note, front_field):
        """Fill Example Fill fields with blanks."""
        if not front_field:
            return
        try:
            front_val = note[front_field].strip()
        except Exception:
            return
        if not front_val:
            return
        frx = re.escape(front_val)
        for sf, df in [("Example", "Example Fill"), ("Example2", "Example2 Fill")]:
            try:
                st = note[sf]
                if st.strip():
                    note[df] = re.sub(frx, "<span class='blank'>___</span>", st)
            except Exception:
                pass


def _generate_audio_safe(text: str, lang: str, rate: str) -> str:
    """Wrapper an toàn cho get_audio_multilang (dùng trong thread pool)."""
    try:
        return get_audio_multilang(text, lang, rate=rate) or ""
    except Exception as e:
        logger.warning("Audio gen error for '%s': %s", text[:30], e)
        return ""
