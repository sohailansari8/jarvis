"""
ui/settings_dialog.py
⚙ Settings modal — AI provider selector, API keys, vision mode, memory.
Supports: Gemini · OpenAI · Groq · Ollama
"""
from __future__ import annotations
import webbrowser

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QSlider,
    QGroupBox, QFormLayout, QComboBox, QStackedWidget,
    QWidget, QSizePolicy, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui  import QFont


# ── Background test thread so the UI never freezes ────────────────────────────
class _TestThread(QThread):
    result = pyqtSignal(bool, str)  # success, message

    def __init__(self, provider: str, config, parent=None):
        super().__init__(parent)
        self._provider = provider
        self._config   = config

    def run(self):
        try:
            p = self._provider
            if p == "gemini":
                self._test_gemini()
            elif p == "openai":
                self._test_openai_compat(
                    self._config.openai_api_key,
                    self._config.openai_base_url,
                    self._config.openai_model,
                    "OpenAI",
                )
            elif p == "groq":
                self._test_openai_compat(
                    self._config.groq_api_key,
                    "https://api.groq.com/openai/v1",
                    self._config.groq_model,
                    "Groq",
                )
            elif p == "ollama":
                self._test_ollama()
            else:
                self.result.emit(False, f"Unknown provider: {p}")
        except Exception as e:
            self.result.emit(False, f"❌ Unexpected error: {str(e)[:200]}")

    def _test_gemini(self):
        key = self._config.gemini_api_key
        if not key:
            self.result.emit(False, "❌ No Gemini API key entered.")
            return
        try:
            from google import genai
            client = genai.Client(api_key=key)
            resp   = client.models.generate_content(
                model="gemini-2.0-flash", contents="Reply with exactly: OK"
            )
            self.result.emit(bool(resp.text), "✅ Gemini connected!" if resp.text else "⚠ Empty response.")
        except ImportError:
            self.result.emit(False, "❌ google-genai not installed.\nRun: pip install google-genai")
        except Exception as e:
            self.result.emit(False, self._friendly(e))

    def _test_openai_compat(self, key, base_url, model, name):
        if not key:
            self.result.emit(False, f"❌ No {name} API key entered.")
            return
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key, base_url=base_url)
            resp   = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Reply with exactly: OK"}],
                max_tokens=5,
            )
            txt = resp.choices[0].message.content
            self.result.emit(bool(txt), f"✅ {name} connected!" if txt else f"⚠ Empty response from {name}.")
        except ImportError:
            self.result.emit(False, "❌ openai not installed.\nRun: pip install openai")
        except Exception as e:
            self.result.emit(False, self._friendly(e))

    def _test_ollama(self):
        import urllib.request, json
        base = self._config.ollama_base_url.rstrip("/")
        model = self._config.ollama_model
        try:
            payload = json.dumps({"model": model, "prompt": "Reply: OK", "stream": False}).encode()
            req = urllib.request.Request(
                f"{base}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            self.result.emit(True, f"✅ Ollama ({model}) connected!")
        except Exception as e:
            self.result.emit(False, f"❌ Ollama error: {str(e)[:200]}\nMake sure Ollama is running.")

    @staticmethod
    def _friendly(e: Exception) -> str:
        s = str(e)
        if "401" in s or "UNAUTHENTICATED" in s:
            return "❌ Authentication failed — invalid API key."
        if "403" in s or "PERMISSION_DENIED" in s:
            return "❌ Permission denied — key may be restricted."
        if "429" in s or "RESOURCE_EXHAUSTED" in s:
            return "⚠ Rate limit hit — wait a minute and try again."
        if "Connection refused" in s or "ConnectionRefused" in s:
            return "❌ Connection refused — is the server running?"
        return f"❌ {s[:200]}"


# ── Settings dialog ───────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    """Modal settings window. Emits settings_saved when the user saves."""

    settings_saved = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._test_thread = None
        self.setWindowTitle("JARVIS — Settings")
        self.setMinimumWidth(540)
        self.setModal(True)
        self._build_ui()
        self._load_values()
        self._apply_stylesheet()

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        # Title
        title = QLabel("⚙  JARVIS Settings")
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet("color: #00f5ff; margin-bottom: 6px;")
        layout.addWidget(title)

        # ── AI Provider ───────────────────────────────────────────────────────
        prov_group = QGroupBox("AI Provider")
        prov_vl    = QVBoxLayout(prov_group)

        prov_row = QHBoxLayout()
        prov_row.addWidget(QLabel("Provider:"))
        self._provider_combo = QComboBox()
        self._provider_combo.addItems([
            "🔵  Gemini  (Google)",
            "🟢  OpenAI  (ChatGPT / GPT-4o)",
            "⚡  Groq  (Free · Ultra-fast)",
            "🖥️  Ollama  (Local · No key needed)",
        ])
        self._provider_combo.setMinimumWidth(260)
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        prov_row.addWidget(self._provider_combo)
        prov_row.addStretch()
        prov_vl.addLayout(prov_row)

        # Stacked panels — one per provider
        self._stack = QStackedWidget()
        self._stack.addWidget(self._panel_gemini())    # 0
        self._stack.addWidget(self._panel_openai())    # 1
        self._stack.addWidget(self._panel_groq())      # 2
        self._stack.addWidget(self._panel_ollama())    # 3
        prov_vl.addWidget(self._stack)

        # Shared test button + status label
        self._test_btn = QPushButton("🔌  Test Connection")
        self._test_btn.clicked.connect(self._test_connection)
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("color: #aaa; font-size: 11px;")
        self._status_lbl.setWordWrap(True)
        prov_vl.addWidget(self._test_btn)
        prov_vl.addWidget(self._status_lbl)
        layout.addWidget(prov_group)

        # ── Vision ────────────────────────────────────────────────────────────
        vis_group  = QGroupBox("Screen Vision")
        vis_layout = QVBoxLayout(vis_group)

        self._vision_cb = QCheckBox(
            "Enable vision (send screenshot with screen-aware commands)"
        )
        self._vision_always_cb = QCheckBox("Always send screenshot (not just when needed)")
        self._vision_always_cb.setEnabled(False)
        self._vision_cb.toggled.connect(self._vision_always_cb.setEnabled)

        note = QLabel("ℹ  Screenshots are sent to the AI API only — never stored locally.")
        note.setStyleSheet("color: #888; font-size: 10px;")
        note.setWordWrap(True)

        vis_layout.addWidget(self._vision_cb)
        vis_layout.addWidget(self._vision_always_cb)
        vis_layout.addWidget(note)
        layout.addWidget(vis_group)

        # ── Memory ────────────────────────────────────────────────────────────
        mem_group = QGroupBox("Conversation Memory")
        mem_form  = QFormLayout(mem_group)

        self._mem_slider = QSlider(Qt.Horizontal)
        self._mem_slider.setRange(5, 40)
        self._mem_slider.setTickInterval(5)
        self._mem_slider.setTickPosition(QSlider.TicksBelow)
        self._mem_lbl = QLabel("20 turns")
        self._mem_slider.valueChanged.connect(
            lambda v: self._mem_lbl.setText(f"{v} turns")
        )
        slider_row = QHBoxLayout()
        slider_row.addWidget(self._mem_slider)
        slider_row.addWidget(self._mem_lbl)
        mem_form.addRow("History depth:", slider_row)
        layout.addWidget(mem_group)

        # ── Save / Cancel ─────────────────────────────────────────────────────
        btn_row    = QHBoxLayout()
        save_btn   = QPushButton("💾  Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.setFixedHeight(36)
        cancel_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    # ── Provider panels ───────────────────────────────────────────────────────
    def _panel_gemini(self) -> QWidget:
        w = QWidget(); f = QFormLayout(w)
        self._gemini_key  = self._secret_edit("API Key  (aistudio.google.com/app/apikey)")
        self._gemini_model = QLineEdit(); self._gemini_model.setPlaceholderText("gemini-2.0-flash")
        link = QPushButton("🌐  Get Free Gemini API Key")
        link.clicked.connect(lambda: webbrowser.open("https://aistudio.google.com/app/apikey"))
        link.setStyleSheet("font-size:11px; padding:4px 8px;")
        f.addRow("API Key:", self._gemini_key)
        f.addRow("Model:", self._gemini_model)
        f.addRow("", link)
        return w

    def _panel_openai(self) -> QWidget:
        w = QWidget(); f = QFormLayout(w)
        self._openai_key      = self._secret_edit("sk-...")
        self._openai_model    = QLineEdit(); self._openai_model.setPlaceholderText("gpt-4o-mini")
        self._openai_base_url = QLineEdit(); self._openai_base_url.setPlaceholderText("https://api.openai.com/v1")
        note = QLabel("ℹ  Base URL can be changed for Azure, LM Studio, or other compatible servers.")
        note.setStyleSheet("color:#888; font-size:10px;"); note.setWordWrap(True)
        f.addRow("API Key:", self._openai_key)
        f.addRow("Model:", self._openai_model)
        f.addRow("Base URL:", self._openai_base_url)
        f.addRow("", note)
        return w

    def _panel_groq(self) -> QWidget:
        w = QWidget(); f = QFormLayout(w)
        self._groq_key   = self._secret_edit("gsk_...")
        self._groq_model = QLineEdit(); self._groq_model.setPlaceholderText("llama-3.3-70b-versatile")
        link = QPushButton("🌐  Get Free Groq API Key  (console.groq.com)")
        link.clicked.connect(lambda: webbrowser.open("https://console.groq.com/keys"))
        link.setStyleSheet("font-size:11px; padding:4px 8px;")
        note = QLabel("⚡ Groq runs Llama at ~300 tok/s — fastest free option.")
        note.setStyleSheet("color:#4ade80; font-size:10px;"); note.setWordWrap(True)
        f.addRow("API Key:", self._groq_key)
        f.addRow("Model:", self._groq_model)
        f.addRow("", link)
        f.addRow("", note)
        return w

    def _panel_ollama(self) -> QWidget:
        w = QWidget(); f = QFormLayout(w)
        self._ollama_url   = QLineEdit(); self._ollama_url.setPlaceholderText("http://localhost:11434")
        self._ollama_model = QLineEdit(); self._ollama_model.setPlaceholderText("llama3")
        link = QPushButton("🌐  Download Ollama  (ollama.com)")
        link.clicked.connect(lambda: webbrowser.open("https://ollama.com/download"))
        link.setStyleSheet("font-size:11px; padding:4px 8px;")
        note = QLabel("🖥️ Fully local — no internet needed after model download.\nRun: ollama pull llama3")
        note.setStyleSheet("color:#00b4d8; font-size:10px;"); note.setWordWrap(True)
        f.addRow("Base URL:", self._ollama_url)
        f.addRow("Model:", self._ollama_model)
        f.addRow("", link)
        f.addRow("", note)
        return w

    def _secret_edit(self, placeholder: str) -> QHBoxLayout:
        """Returns a QHBoxLayout with a password field + eye toggle."""
        container = QWidget()
        hl = QHBoxLayout(container)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(4)
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setEchoMode(QLineEdit.Password)
        eye = QPushButton("👁")
        eye.setFixedWidth(30)
        eye.setCheckable(True)
        eye.toggled.connect(
            lambda v: edit.setEchoMode(QLineEdit.Normal if v else QLineEdit.Password)
        )
        hl.addWidget(edit)
        hl.addWidget(eye)
        # Store the QLineEdit as attribute on container so we can access it
        container._edit = edit
        return container

    # ── Load / Save ───────────────────────────────────────────────────────────
    def _load_values(self):
        p_map = {"gemini": 0, "openai": 1, "groq": 2, "ollama": 3}
        self._provider_combo.setCurrentIndex(p_map.get(self._config.ai_provider, 0))
        self._stack.setCurrentIndex(p_map.get(self._config.ai_provider, 0))

        self._gemini_key._edit.setText(self._config.gemini_api_key)
        self._gemini_model.setText(self._config.gemini_model)

        self._openai_key._edit.setText(self._config.openai_api_key)
        self._openai_model.setText(self._config.openai_model)
        self._openai_base_url.setText(self._config.openai_base_url)

        self._groq_key._edit.setText(self._config.groq_api_key)
        self._groq_model.setText(self._config.groq_model)

        self._ollama_url.setText(self._config.ollama_base_url)
        self._ollama_model.setText(self._config.ollama_model)

        self._vision_cb.setChecked(self._config.enable_vision)
        self._vision_always_cb.setChecked(self._config.vision_always)
        self._vision_always_cb.setEnabled(self._config.enable_vision)
        self._mem_slider.setValue(self._config.conversation_max_turns)

    def _save(self):
        idx_map = {0: "gemini", 1: "openai", 2: "groq", 3: "ollama"}
        self._config.ai_provider = idx_map[self._provider_combo.currentIndex()]

        self._config.gemini_api_key = self._gemini_key._edit.text()
        self._config.gemini_model   = self._gemini_model.text() or "gemini-2.0-flash"

        self._config.openai_api_key  = self._openai_key._edit.text()
        self._config.openai_model    = self._openai_model.text() or "gpt-4o-mini"
        self._config.openai_base_url = self._openai_base_url.text() or "https://api.openai.com/v1"

        self._config.groq_api_key = self._groq_key._edit.text()
        self._config.groq_model   = self._groq_model.text() or "llama-3.3-70b-versatile"

        self._config.ollama_base_url = self._ollama_url.text() or "http://localhost:11434"
        self._config.ollama_model    = self._ollama_model.text() or "llama3"

        self._config.enable_vision         = self._vision_cb.isChecked()
        self._config.vision_always         = self._vision_always_cb.isChecked()
        self._config.conversation_max_turns = self._mem_slider.value()

        self._config.save()
        self.settings_saved.emit()
        self.accept()

    # ── Provider combo → stack switch ─────────────────────────────────────────
    def _on_provider_changed(self, idx: int):
        self._stack.setCurrentIndex(idx)
        self._status_lbl.setText("")

    # ── Test connection ───────────────────────────────────────────────────────
    def _test_connection(self):
        # Temporarily push current field values into config for the test
        idx_map = {0: "gemini", 1: "openai", 2: "groq", 3: "ollama"}
        provider = idx_map[self._provider_combo.currentIndex()]

        self._config.gemini_api_key  = self._gemini_key._edit.text()
        self._config.gemini_model    = self._gemini_model.text() or "gemini-2.0-flash"
        self._config.openai_api_key  = self._openai_key._edit.text()
        self._config.openai_model    = self._openai_model.text() or "gpt-4o-mini"
        self._config.openai_base_url = self._openai_base_url.text() or "https://api.openai.com/v1"
        self._config.groq_api_key    = self._groq_key._edit.text()
        self._config.groq_model      = self._groq_model.text() or "llama-3.3-70b-versatile"
        self._config.ollama_base_url = self._ollama_url.text() or "http://localhost:11434"
        self._config.ollama_model    = self._ollama_model.text() or "llama3"

        self._status_lbl.setText(f"⏳ Testing {provider}… (may take a few seconds)")
        self._status_lbl.setStyleSheet("color: #aaa; font-size: 11px;")
        self._test_btn.setEnabled(False)

        self._test_thread = _TestThread(provider, self._config, self)
        self._test_thread.result.connect(self._on_test_result)
        self._test_thread.start()

    def _on_test_result(self, success: bool, msg: str):
        color = "#50fa7b" if success else "#ff5555"
        self._status_lbl.setText(msg)
        self._status_lbl.setStyleSheet(f"color: {color}; font-size: 11px;")
        self._test_btn.setEnabled(True)

    # ── Stylesheet ────────────────────────────────────────────────────────────
    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QDialog {
                background: #0d0d1a;
                color: #e0e0ff;
            }
            QGroupBox {
                border: 1px solid rgba(0,245,255,60);
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
                color: #00f5ff;
                font-weight: bold;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QLabel { color: #c0c0e0; font-size: 12px; }
            QLineEdit {
                background: rgba(255,255,255,10);
                border: 1px solid rgba(0,245,255,80);
                border-radius: 6px;
                color: #e0e0ff;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus { border: 1px solid rgba(0,245,255,200); }
            QPushButton {
                background: rgba(0,245,255,30);
                border: 1px solid rgba(0,245,255,100);
                border-radius: 6px;
                color: #00f5ff;
                padding: 6px 14px;
                font-size: 12px;
            }
            QPushButton:hover   { background: rgba(0,245,255,60);  }
            QPushButton:pressed { background: rgba(0,245,255,20);  }
            QPushButton:disabled { color: #444; border-color: #333; }
            QCheckBox { color: #c0c0e0; font-size: 12px; }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border: 1px solid rgba(0,245,255,100);
                border-radius: 3px;
                background: rgba(255,255,255,5);
            }
            QCheckBox::indicator:checked { background: rgba(0,245,255,180); }
            QComboBox {
                background: rgba(255,255,255,8);
                border: 1px solid rgba(0,245,255,80);
                border-radius: 6px;
                color: #e0e0ff;
                padding: 5px 10px;
                font-size: 12px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #1a1a2e;
                color: #e0e0ff;
                selection-background-color: rgba(0,245,255,40);
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: rgba(255,255,255,20);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00f5ff;
                border-radius: 6px;
                width: 16px; height: 16px;
                margin: -5px 0;
            }
            QSlider::sub-page:horizontal {
                background: rgba(0,245,255,120);
                border-radius: 3px;
            }
        """)
