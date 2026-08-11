"""
AI Settings Dialog — Cấu hình API Key & model cho AI.
"""

import json
import urllib.request
import urllib.error

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QCheckBox, QComboBox, QDoubleSpinBox, QSpinBox,
    QPushButton, QGroupBox,
)
from aqt.utils import showInfo, tooltip

from utils.ai_extractor import get_api_config, save_api_config, clear_cache, clear_import_history


def show_ai_settings_dialog(parent):
    """Mở dialog cấu hình API Key & endpoint cho AI.
    Trả về True nếu người dùng đã lưu."""
    cfg = get_api_config()

    dlg = QDialog(parent)
    dlg.setWindowTitle("⚙️ Cài Đặt AI — API Key & Model")
    dlg.setMinimumWidth(550)
    vl = QVBoxLayout(dlg)

    vl.addWidget(QLabel(
        "<h3>🤖 Cấu hình OpenAI-compatible API</h3>"
        "<p style='color:#555;'>Hỗ trợ: OpenAI, DeepSeek, Ollama, LM Studio, Claude (qua proxy), OpenRouter, v.v.</p>"
        "<p style='color:#e67e22;'><b>💡 Mẹo:</b> Bấm nút <b>DeepSeek</b> bên dưới để tự điền Base URL + Model, "
        "sau đó chỉ cần nhập API Key từ <a href='https://platform.deepseek.com/api_keys'>platform.deepseek.com/api_keys</a></p>"
    ))

    # API Key
    vl.addWidget(QLabel("<b>🔑 API Key:</b>"))
    txt_key = QLineEdit()
    txt_key.setEchoMode(QLineEdit.EchoMode.Password)
    txt_key.setPlaceholderText("sk-... (DeepSeek: vào platform.deepseek.com/api_keys để lấy)")
    txt_key.setText(cfg.get("api_key", ""))
    txt_key.setMinimumHeight(30)
    vl.addWidget(txt_key)

    chk_show = QCheckBox("👁 Hiện API Key")
    chk_show.toggled.connect(lambda checked: (
        txt_key.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
    ))
    vl.addWidget(chk_show)

    # API Base URL
    vl.addWidget(QLabel("<b>🌐 API Base URL:</b>"))
    txt_base = QLineEdit()
    txt_base.setPlaceholderText("https://api.deepseek.com/v1 (DeepSeek) hoặc https://api.openai.com/v1")
    txt_base.setText(cfg.get("api_base", "https://api.openai.com/v1"))
    txt_base.setMinimumHeight(30)
    vl.addWidget(txt_base)

    # Model
    vl.addWidget(QLabel("<b>🧠 Model:</b>"))
    cbo_model = QComboBox()
    cbo_model.setEditable(True)
    models = [
        "deepseek-chat", "deepseek-reasoner",
        "gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo",
        "claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku",
        "llama3.1", "mistral", "gemma2", "qwen2.5",
    ]
    cbo_model.addItems(models)
    current_model = cfg.get("model", "gpt-4o-mini")
    idx = cbo_model.findText(current_model)
    if idx >= 0:
        cbo_model.setCurrentIndex(idx)
    else:
        cbo_model.setCurrentText(current_model)
    vl.addWidget(cbo_model)

    # Temperature
    vl.addWidget(QLabel("<b>🌡 Temperature (0-2):</b>"))
    spin_temp = QDoubleSpinBox()
    spin_temp.setRange(0.0, 2.0)
    spin_temp.setSingleStep(0.1)
    spin_temp.setValue(cfg.get("temperature", 0.3))
    vl.addWidget(spin_temp)

    # Reasoning effort — mức độ nỗ lực suy nghĩ của model
    vl.addWidget(QLabel("<b>🧠 Mức độ suy nghĩ (reasoning_effort):</b>"))
    cbo_effort = QComboBox()
    effort_options = [
        ("Tự động (không gửi tham số)", ""),
        ("Thấp — nhanh, rẻ, ít token", "low"),
        ("Trung bình", "medium"),
        ("Cao — sâu, chất lượng tốt, tốn token", "high"),
    ]
    for label, val in effort_options:
        cbo_effort.addItem(label, val)
    idx_effort = cbo_effort.findData(cfg.get("reasoning_effort", ""))
    if idx_effort >= 0:
        cbo_effort.setCurrentIndex(idx_effort)
    cbo_effort.setToolTip(
        "Mức độ nỗ lực suy nghĩ của model.\n"
        "Chỉ áp dụng với model hỗ trợ (OpenAI o1/o3/o4...).\n"
        "DeepSeek: deepseek-chat = nhanh/rẻ; deepseek-reasoner = suy nghĩ sâu (đắt hơn).\n"
        "Mức càng cao → chất lượng tốt hơn nhưng tốn NHIỀU token output."
    )
    vl.addWidget(cbo_effort)

    # Chunk size — độ dài nội dung mỗi lần gọi (tránh bị cắt)
    vl.addWidget(QLabel("<b>📏 Độ dài xử lý mỗi lần gọi (ký tự):</b>"))
    spin_chunk = QSpinBox()
    spin_chunk.setRange(3000, 15000)
    spin_chunk.setSingleStep(1000)
    spin_chunk.setValue(cfg.get("chunk_size", 8000))
    spin_chunk.setToolTip(
        "Số ký tự tối đa gửi trong 1 request AI (càng nhỏ càng mịn, chất lượng cao hơn).\n"
        "Văn bản DÀI HƠN vẫn được xử lý hết (tự chia đoạn) — con số này chỉ là kích thước mỗi lần gọi.\n"
        "⚠️ ĐỪNG để quá lớn: DeepSeek giới hạn OUTPUT ~8192 token/lần, "
        "chunk lớn → JSON dễ bị CẮT giữa chừng. Khuyên 6k-8k."
    )
    vl.addWidget(spin_chunk)

    # Presets
    preset_grp = QGroupBox("⚡ Presets")
    preset_layout = QHBoxLayout()

    presets = [
        ("DeepSeek", "https://api.deepseek.com/v1", "deepseek-chat"),
        ("OpenAI", "https://api.openai.com/v1", "gpt-4o-mini"),
        ("Ollama (local)", "http://localhost:11434/v1", "llama3.1"),
        ("LM Studio (local)", "http://localhost:1234/v1", "local-model"),
        ("OpenRouter", "https://openrouter.ai/api/v1", "openai/gpt-4o-mini"),
    ]

    for pname, pbase, pmodel in presets:
        btn = QPushButton(pname)
        btn.setStyleSheet("padding:4px 10px;font-size:11px;border-radius:4px;")
        btn.clicked.connect(lambda checked, b=pbase, m=pmodel: (
            txt_base.setText(b), cbo_model.setCurrentText(m)
        ))
        preset_layout.addWidget(btn)

    preset_grp.setLayout(preset_layout)
    vl.addWidget(preset_grp)

    # Cache management
    cache_bar = QHBoxLayout()
    btn_clear_cache = QPushButton("🗑 Xóa Cache AI")
    btn_clear_cache.setStyleSheet("padding:6px 12px;background:#e74c3c;color:white;font-weight:bold;border-radius:6px;")
    btn_clear_cache.clicked.connect(lambda: (
        clear_cache(),
        tooltip("✅ Đã xóa toàn bộ cache AI!")
    ))
    cache_bar.addWidget(btn_clear_cache)

    btn_clear_history = QPushButton("🗑 Xóa Lịch Sử")
    btn_clear_history.setStyleSheet("padding:6px 12px;background:#e67e22;color:white;font-weight:bold;border-radius:6px;")
    btn_clear_history.clicked.connect(lambda: (
        tooltip("✅ Đã xóa lịch sử từ vựng!" if clear_import_history() else "⚠️ Không thể xóa lịch sử.")
    ))
    cache_bar.addWidget(btn_clear_history)

    cache_bar.addStretch()
    vl.addLayout(cache_bar)

    # Buttons
    btn_layout = QHBoxLayout()
    btn_test = QPushButton("🧪 Test Kết Nối")
    btn_test.setStyleSheet("padding:8px 16px;background:#3498db;color:white;font-weight:bold;border-radius:6px;")
    btn_test.clicked.connect(lambda: _test_ai_connection(
        txt_key.text().strip(),
        txt_base.text().strip(),
        cbo_model.currentText().strip(),
        dlg,
    ))
    btn_layout.addWidget(btn_test)

    btn_layout.addStretch()

    btn_cancel = QPushButton("❌ Hủy")
    btn_cancel.clicked.connect(dlg.reject)
    btn_layout.addWidget(btn_cancel)

    btn_save = QPushButton("💾 Lưu")
    btn_save.setStyleSheet("padding:8px 20px;background:#27ae60;color:white;font-weight:bold;border-radius:6px;")
    btn_save.clicked.connect(lambda: (
        save_api_config(
            txt_key.text().strip(),
            txt_base.text().strip(),
            cbo_model.currentText().strip(),
            spin_temp.value(),
            spin_chunk.value(),          # max_chars (mỗi lần gọi)
            spin_chunk.value(),          # chunk_size (chia đoạn)
            cbo_effort.currentData() or "",  # reasoning_effort
        ),
        dlg.accept(),
        tooltip("✅ Đã lưu cấu hình AI!"),
    ))
    btn_layout.addWidget(btn_save)

    vl.addLayout(btn_layout)
    dlg.exec()


def _test_ai_connection(api_key, api_base, model, parent_dlg):
    """Test kết nối đến AI API"""
    if not api_base:
        tooltip("⚠️ Vui lòng nhập API Base URL.")
        return

    try:
        url = api_base.rstrip("/") + "/chat/completions"
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": "Say 'OK' in Vietnamese."}],
            "max_tokens": 10,
        }).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

        # Disable parent dialog temporarily
        parent_dlg.setEnabled(False)
        from aqt.qt import QApplication
        QApplication.processEvents()

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                reply = body.get("choices", [{}])[0].get("message", {}).get("content", "")
                showInfo(f"✅ Kết nối thành công!\n\nModel: {model}\nPhản hồi: {reply}")
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")[:300]
            except Exception:
                pass
            showInfo(f"❌ Lỗi HTTP {e.code}: {e.reason}\n\n{err_body}")
        except Exception as e:
            showInfo(f"❌ Lỗi kết nối: {e}")
        finally:
            parent_dlg.setEnabled(True)

    except Exception as e:
        showInfo(f"❌ Lỗi: {e}")
