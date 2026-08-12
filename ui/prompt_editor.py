"""
✏️ Prompt / Schema / Field Map Editor.

Mức 1 (đề xuất #1 + #2): ngoài việc sửa System Prompt + JSON template (không cần
sửa code), cho phép MAP key JSON → Field Anki ngay trên giao diện:

- Tab "Prompt Từ Vựng" / "Prompt Ngữ Pháp": chỉnh system prompt (RAW, dùng
  {{JSON_TEMPLATE}}) + mẫu JSON cho từng ngôn ngữ.
- Tab "🗂 Field Map": bảng map key JSON (tự sinh từ template) → Field Anki.
  Field mới được TỰ ĐỘNG THÊM vào Note Type (khi Lưu, nếu model đã tồn tại),
  và mọi nơi dùng self._cfg() đều nhận json_field_map/all_fields hiệu lực.

Lưu vào utils/ai_prompts.json (gitignored) qua utils.prompt_config.
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QPlainTextEdit, QTabWidget, QWidget, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, Qt,
)
from aqt.utils import tooltip

from utils.prompt_config import (
    get_effective_config, save_config as save_prompt_config,
    reset_config as reset_prompt_config, TEMPLATE_PLACEHOLDER,
    validate_json_template, apply_field_map_to_cfg, auto_field_name,
)
from utils.logger import get_logger
from utils.i18n import t
from mode import LANG_TEMPLATES, LANG_GRAMMAR_TEMPLATES
from mode.card_render import build_qfmt as _build_qfmt, build_afmt as _build_afmt

logger = get_logger()

_LANG_LABELS = {
    "japanese": "🇯🇵 Nhật Bản",
    "chinese": "🇨🇳 Trung Quốc",
    "korean": "🇰🇷 Hàn Quốc",
}
_KIND_LABELS = {
    "vocab": "Từ Vựng",
    "grammar": "Ngữ Pháp",
}
_KINDS = ("vocab", "grammar")
_LANGS = ("japanese", "chinese", "korean")
# Vị trí hiển thị field tuỳ chỉnh trên thẻ (Mức 2)
_SIDE_LABELS = [
    ("back", "Chỉ mặt sau"),
    ("both", "Cả hai mặt"),
    ("front", "Chỉ mặt trước"),
]


class PromptEditorDialog(QDialog):
    """Dialog chỉnh prompt/schema + field map AI cho từng ngôn ngữ."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("prompt_editor_title"))
        self.setMinimumSize(820, 640)
        self.resize(940, 720)

        # Dữ liệu hiệu lực (defaults + ghi đè) và bản chỉnh sửa đang mở
        self._data = get_effective_config()
        self._edits = {}        # {kind: {lang: {"json_template","system_prompt"}}}
        self._fm_edits = {}     # {kind: {lang: {json_key: anki_field}}}
        self._fm_show_edits = {}  # {kind: {lang: {anki_field: "front"|"back"|"both"}}}
        self._last_prompt_kind = _KINDS[0]

        self._build_ui()
        self._load_prompt_editor(_KINDS[0])
        self._build_fm_table()

    # ── UI ────────────────────────────────────────────────
    def _build_ui(self):
        vl = QVBoxLayout(self)

        header = QLabel(
            f"<h3>{t('prompt_editor_header')}</h3>"
            f"<p style='color:#555;'>{t('prompt_editor_sub')}</p>"
            "<p style='color:#7f8c8d;font-size:12px;'>"
            "Trong System Prompt, dùng <code>{{JSON_TEMPLATE}}</code> để chèn mẫu vào \"MẪU:\". "
            "Sửa xong → cache AI tự làm mới. Field mới trong Field Map sẽ được thêm vào Note Type khi Lưu.</p>"
        )
        vl.addWidget(header)

        self.tabs = QTabWidget()
        self._tab_widgets = {}

        # ── Tab 1-2: Prompt (từ vựng / ngữ pháp) ──────────
        for kind in _KINDS:
            page = QWidget()
            page_layout = QVBoxLayout(page)

            lang_row = QHBoxLayout()
            lang_row.addWidget(QLabel(f"<b>{t('prompt_lang_label')}</b>"))
            cbo_lang = QComboBox()
            for lang, label in _LANG_LABELS.items():
                cbo_lang.addItem(label, lang)
            cbo_lang.currentIndexChanged.connect(lambda *_, k=kind: self._on_prompt_lang_change(k))
            lang_row.addWidget(cbo_lang)
            lang_row.addStretch()
            page_layout.addLayout(lang_row)

            info = QLabel("")
            info.setWordWrap(True)
            page_layout.addWidget(info)

            page_layout.addWidget(QLabel(f"<b>{t('prompt_json_label')}</b>"))
            txt_json = QPlainTextEdit()
            txt_json.setPlaceholderText('{\n  "front": "…",\n  "meaning": "…"\n}')
            txt_json.setMaximumHeight(200)
            txt_json.textChanged.connect(lambda *_, k=kind: self._validate_prompt(k))
            page_layout.addWidget(txt_json)

            page_layout.addWidget(QLabel(
                f"<b>{t('prompt_system_label')}</b> "
                f"<span style='color:#7f8c8d;'>(dùng <code>{TEMPLATE_PLACEHOLDER}</code> để chèn mẫu)</span>"
            ))
            txt_prompt = QPlainTextEdit()
            txt_prompt.setPlaceholderText(t("prompt_placeholder"))
            page_layout.addWidget(txt_prompt, stretch=1)

            self.tabs.addTab(page, f"Prompt {_KIND_LABELS[kind]}")
            self._tab_widgets[kind] = {
                "cbo_lang": cbo_lang, "txt_json": txt_json,
                "txt_prompt": txt_prompt, "info": info,
            }

        # ── Tab 3: Field Map ──────────────────────────────
        fm_page = QWidget()
        fm_layout = QVBoxLayout(fm_page)

        fm_row = QHBoxLayout()
        fm_row.addWidget(QLabel(f"<b>{t('prompt_kind_label')}</b>"))
        self.fm_cbo_kind = QComboBox()
        for kind in _KINDS:
            self.fm_cbo_kind.addItem(_KIND_LABELS[kind], kind)
        self.fm_cbo_kind.currentIndexChanged.connect(lambda *_: self._on_fm_change())
        fm_row.addWidget(self.fm_cbo_kind)

        fm_row.addWidget(QLabel(f"<b>{t('prompt_lang_label')}</b>"))
        self.fm_cbo_lang = QComboBox()
        for lang, label in _LANG_LABELS.items():
            self.fm_cbo_lang.addItem(label, lang)
        self.fm_cbo_lang.currentIndexChanged.connect(lambda *_: self._on_fm_change())
        fm_row.addWidget(self.fm_cbo_lang)
        fm_row.addStretch()
        fm_layout.addLayout(fm_row)

        self.fm_info = QLabel("")
        self.fm_info.setWordWrap(True)
        fm_layout.addWidget(self.fm_info)

        self.fm_table = QTableWidget(0, 3)
        self.fm_table.setHorizontalHeaderLabels([t("prompt_fm_key"), t("prompt_fm_field"), t("prompt_fm_show")])
        self.fm_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.fm_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.fm_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.fm_table.verticalHeader().setVisible(False)
        fm_layout.addWidget(self.fm_table, stretch=1)

        self.tabs.addTab(fm_page, t("prompt_field_map_tab"))

        self.tabs.currentChanged.connect(lambda *_: self._on_tab_change())
        vl.addWidget(self.tabs, stretch=1)

        # ── Nút chức năng ─────────────────────────────────
        btn_row = QHBoxLayout()
        btn_preview = QPushButton(t("btn_preview_prompt"))
        btn_preview.clicked.connect(self._on_preview)
        btn_row.addWidget(btn_preview)

        btn_reset = QPushButton(t("btn_reset_defaults"))
        btn_reset.setStyleSheet("padding:8px 14px;background:#e67e22;color:white;font-weight:bold;border-radius:6px;")
        btn_reset.clicked.connect(self._on_reset)
        btn_row.addWidget(btn_reset)

        btn_row.addStretch()

        btn_close = QPushButton(t("btn_close"))
        btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_close)

        btn_save = QPushButton(t("btn_save_all"))
        btn_save.setStyleSheet("padding:8px 20px;background:#27ae60;color:white;font-weight:bold;border-radius:6px;")
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)

        vl.addLayout(btn_row)

    # ── Prompt tabs ──────────────────────────────────────
    def _sync_all_prompt_edits(self):
        """Lưu nội dung CẢ HAI prompt tab vào self._edits (gọi trước khi chuyển tab/ngôn ngữ)."""
        for kind in _KINDS:
            w = self._tab_widgets[kind]
            lang = w["cbo_lang"].currentData()
            self._edits.setdefault(kind, {})[lang] = {
                "json_template": w["txt_json"].toPlainText(),
                "system_prompt": w["txt_prompt"].toPlainText(),
            }

    def _load_prompt_editor(self, kind):
        w = self._tab_widgets[kind]
        lang = w["cbo_lang"].currentData()
        entry = self._data[kind][lang]
        if kind in self._edits and lang in self._edits[kind]:
            entry = self._edits[kind][lang]
        w["txt_json"].setPlainText(entry["json_template"])
        raw = entry.get("system_prompt_raw") or entry.get("system_prompt")
        w["txt_prompt"].setPlainText(raw)
        self._validate_prompt(kind)

    def _validate_prompt(self, kind):
        w = self._tab_widgets[kind]
        lang = w["cbo_lang"].currentData()
        ok, err, fields = validate_json_template(w["txt_json"].toPlainText())
        if ok:
            mod = " ✏️ (đã chỉnh)" if (kind in self._edits and lang in self._edits[kind]) else ""
            self._tab_widgets[kind]["info"].setText(
                f"<span style='color:#27ae60;font-weight:bold;'>✅ Schema hợp lệ — {len(fields)} trường:</span> "
                f"<code>{', '.join(fields)}</code>{mod}"
            )
        else:
            self._tab_widgets[kind]["info"].setText(
                f"<span style='color:#e74c3c;font-weight:bold;'>❌ {err}</span>"
            )

    def _on_prompt_lang_change(self, kind):
        self._sync_all_prompt_edits()
        self._load_prompt_editor(kind)

    def _on_tab_change(self):
        idx = self.tabs.currentIndex()
        if idx < 2:
            self._last_prompt_kind = _KINDS[idx]
            self._sync_all_prompt_edits()
            self._load_prompt_editor(_KINDS[idx])
        else:
            # Sang Field Map: đồng bộ prompt edits trước (template mới nhất → key mới)
            self._sync_all_prompt_edits()
            self._build_fm_table()

    # ── Field Map tab ────────────────────────────────────
    def _current_fm(self):
        return self.fm_cbo_kind.currentData(), self.fm_cbo_lang.currentData()

    def _collect_fm_table(self):
        """Đọc bảng hiện tại vào self._fm_edits + self._fm_show_edits."""
        kind, lang = self._current_fm()
        m = {}
        show = {}
        for r in range(self.fm_table.rowCount()):
            k_item = self.fm_table.item(r, 0)
            cell = self.fm_table.cellWidget(r, 1)
            side_cbo = self.fm_table.cellWidget(r, 2)
            if k_item is None or cell is None:
                continue
            k = (k_item.text() or "").strip()
            v = (cell.text() or "").strip()
            if k and v:
                m[k] = v
                if side_cbo is not None and side_cbo.currentData() in ("front", "back", "both"):
                    side = side_cbo.currentData()
                    if side != "back":  # back là mặc định → không lưu thừa
                        show[v] = side
        self._fm_edits.setdefault(kind, {})[lang] = m
        self._fm_show_edits.setdefault(kind, {})[lang] = show

    def _build_fm_table(self):
        kind, lang = self._current_fm()
        tpl = self._edits.get(kind, {}).get(lang, {}).get("json_template") \
            or self._data[kind][lang]["json_template"]
        ok, err, keys = validate_json_template(tpl)
        if not ok:
            self.fm_info.setText(
                f"<span style='color:#e74c3c;font-weight:bold;'>❌ Mẫu JSON chưa hợp lệ — "
                f"sửa ở tab Prompt {_KIND_LABELS[kind]} trước. {err}</span>"
            )
            self.fm_table.setRowCount(0)
            return

        default_map = self._data[kind][lang]["default_field_map"]
        eff_map = self._data[kind][lang]["field_map"]
        saved_show = self._data[kind][lang]["card_show"]
        cur = self._fm_edits.get(kind, {}).get(lang, {})
        cur_show = self._fm_show_edits.get(kind, {}).get(lang, {})

        self.fm_table.setRowCount(len(keys))
        for r, key in enumerate(keys):
            item_key = QTableWidgetItem(key)
            item_key.setFlags(item_key.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.fm_table.setItem(r, 0, item_key)
            dflt = default_map.get(key) or auto_field_name(key)
            val = cur.get(key, eff_map.get(key, dflt))
            cell = QLineEdit(val)
            self.fm_table.setCellWidget(r, 1, cell)
            # Cột "Hiển thị" — nơi field xuất hiện trên thẻ (Mức 2)
            side_cbo = QComboBox()
            for side, label in _SIDE_LABELS:
                side_cbo.addItem(label, side)
            side = cur_show.get(val, saved_show.get(val, "back"))
            idx_side = side_cbo.findData(side)
            if idx_side >= 0:
                side_cbo.setCurrentIndex(idx_side)
            self.fm_table.setCellWidget(r, 2, side_cbo)

        new_keys = [k for k in keys if k not in default_map]
        note = f"<br><span style='color:#8e44ad;'>🆕 Key mới: {', '.join(new_keys) or 'không có'} — "
        note += "tự suy tên field, bạn có thể đổi.</span>"
        self.fm_info.setText(
            f"<span style='color:#27ae60;font-weight:bold;'>✅ {len(keys)} key JSON → Field Anki.</span>"
            f" Field chưa có trong Note Type sẽ được <b>thêm tự động khi Lưu</b>, "
            f"và field mới sẽ <b>tự hiện trên thẻ</b> (theo cột Hiển thị).{note}"
        )

    def _on_fm_change(self):
        self._collect_fm_table()
        self._build_fm_table()

    # ── Preview ──────────────────────────────────────────
    def _on_preview(self):
        kind = self._last_prompt_kind
        w = self._tab_widgets[kind]
        lang = w["cbo_lang"].currentData()
        self._sync_all_prompt_edits()
        e = self._edits[kind][lang]
        tpl = e["json_template"]
        ok, err, _ = validate_json_template(tpl)
        if not ok:
            QMessageBox.warning(self, "Lỗi JSON", f"Mẫu JSON không hợp lệ:\n{err}")
            return
        raw = e["system_prompt"]
        full = raw.replace(TEMPLATE_PLACEHOLDER, tpl) if TEMPLATE_PLACEHOLDER in raw else raw
        dlg = QDialog(self)
        dlg.setWindowTitle(f"👁 Prompt Đầy Đủ — {_LANG_LABELS[lang]} ({_KIND_LABELS[kind]})")
        dlg.setMinimumSize(640, 480)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(f"<b>Độ dài:</b> {len(full)} ký tự — <b>{len(tpl.splitlines())}</b> dòng mẫu"))
        txt = QPlainTextEdit()
        txt.setPlainText(full)
        txt.setReadOnly(True)
        lay.addWidget(txt)
        btn = QPushButton("Đóng")
        btn.clicked.connect(dlg.accept)
        lay.addWidget(btn)
        dlg.exec()

    # ── Save / Reset ─────────────────────────────────────
    def _on_save(self):
        self._sync_all_prompt_edits()
        self._collect_fm_table()

        entries = {"vocab": {}, "grammar": {}}
        for kind, lang_map in self._edits.items():
            for lang, e in lang_map.items():
                if e["json_template"].strip() or e["system_prompt"].strip():
                    entries[kind][lang] = {
                        "json_template": e["json_template"],
                        "system_prompt": e["system_prompt"],
                    }

        fm = {"vocab": {}, "grammar": {}}
        for kind, lang_map in self._fm_edits.items():
            for lang, m in lang_map.items():
                if m:
                    fm[kind][lang] = m

        card_show = {"vocab": {}, "grammar": {}}
        for kind, lang_map in self._fm_show_edits.items():
            for lang, show in lang_map.items():
                if show:
                    card_show[kind][lang] = show

        try:
            save_prompt_config(entries, field_map=fm, card_show=card_show)
            added_fields, updated_models = self._sync_models_after_save()
            msg = "✅ Đã lưu Prompt, Schema & Field Map! Cache AI đã tự làm mới."
            if added_fields:
                msg += f"\n➕ Đã thêm {added_fields} field mới vào Note Type."
            if updated_models:
                msg += f"\n🃏 Đã đồng bộ template {updated_models} Note Type — field mới sẽ hiện trên thẻ."
            tooltip(msg)
            self._data = get_effective_config()
            self._edits = {}
            self._fm_edits = {}
            self._fm_show_edits = {}
            self.accept()
        except Exception as ex:
            QMessageBox.critical(self, "Lỗi lưu", f"Không thể lưu cấu hình prompt:\n{ex}")

    def _sync_models_after_save(self):
        """Sau khi lưu (Mức 1 + 2): tự THÊM field mới + ĐỒNG BỘ template thẻ
        (append field tuỳ chỉnh) cho 6 model nếu đã tồn tại. Trả (added_fields, updated_models)."""
        added = 0
        updated_models = 0
        try:
            from aqt import mw
            from Language import LANG_CONFIG, LANG_GRAMMAR_CONFIG
            if mw is None or getattr(mw, "col", None) is None:
                return 0, 0
            mm = mw.col.models
            pairs = (
                ("vocab", LANG_CONFIG, LANG_TEMPLATES),
                ("grammar", LANG_GRAMMAR_CONFIG, LANG_GRAMMAR_TEMPLATES),
            )
            for kind, lang_cfgs, tmpl_map in pairs:
                for lang, base in lang_cfgs.items():
                    eff_cfg = apply_field_map_to_cfg(base, lang, kind)
                    m = mm.by_name(eff_cfg["model_name"])
                    if not m:
                        continue
                    existing = {f["name"] for f in m["flds"]}
                    n = 0
                    for fn in eff_cfg["all_fields"]:
                        if fn and fn not in existing:
                            mm.add_field(m, mm.new_field(fn))
                            existing.add(fn)
                            n += 1
                    # Mức 2: đồng bộ template thẻ (append field tuỳ chỉnh)
                    tmpls = tmpl_map[lang]
                    tmpl_count = len(tmpls) // 2
                    tmpl_changed = False
                    for i in range(tmpl_count):
                        if i < len(m["tmpls"]):
                            q = _build_qfmt(eff_cfg, tmpls, i * 2)
                            a = _build_afmt(eff_cfg, tmpls, i * 2 + 1)
                            if m["tmpls"][i]["qfmt"] != q or m["tmpls"][i]["afmt"] != a:
                                m["tmpls"][i]["qfmt"] = q
                                m["tmpls"][i]["afmt"] = a
                                tmpl_changed = True
                    if n or tmpl_changed:
                        mm.save(m)
                        added += n
                        if tmpl_changed:
                            updated_models += 1
                        logger.info(
                            "prompt_editor: sync model %s (+%d field, %s)",
                            eff_cfg["model_name"], n,
                            "template" if tmpl_changed else "no-template-change",
                        )
        except Exception as e:
            logger.warning("prompt_editor: không sync model: %s", e)
        return added, updated_models

    def _on_reset(self):
        if QMessageBox.question(
            self, "Reset Prompt",
            "Trả toàn bộ Prompt, Schema & Field Map về mặc định ban đầu?\n"
            "(Mọi chỉnh sửa của bạn sẽ bị xóa.)",
        ) != QMessageBox.StandardButton.Yes:
            return
        reset_prompt_config()
        self._data = get_effective_config()
        self._edits = {}
        self._fm_edits = {}
        self._fm_show_edits = {}
        self._load_prompt_editor(_KINDS[0])
        self._build_fm_table()
        tooltip("♻️ Đã reset về mặc định.")


def show_prompt_editor_dialog(parent=None):
    """Mở dialog chỉnh Prompt & Schema AI."""
    dlg = PromptEditorDialog(parent)
    dlg.exec()
    return dlg
