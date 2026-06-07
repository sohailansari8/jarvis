"""
ui/main_window.py
J.A.R.V.I.S — Complete redesigned UI.
Layout: Top bar | Left sidebar (stats/weather/camera/uptime) | Centre orb | Right chat
"""
from __future__ import annotations

import sys
import os
import datetime
import requests
import psutil

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QFrame, QApplication,
    QSizePolicy, QProgressBar,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush

from core.config          import Config
from core.speech_engine   import SpeechEngine
from core.state_machine   import StateMachine
from core.context_manager import SessionContext
from handlers.command_router import CommandRouter
from ui.settings_dialog   import SettingsDialog
from ui.glass_widgets     import (
    JarvisOrb, CircularGauge, ChatBubble, ChatScrollArea,
    IconButton, ToolBtn,
)


# ─── Command worker thread ───────────────────────────────────────────────────
class CommandWorker(QThread):
    response_ready = pyqtSignal(str, str)

    def __init__(self, query, context, router, parent=None):
        super().__init__(parent)
        self._query   = query
        self._context = context
        self._router  = router

    def run(self):
        response, _ = self._router.route(self._query, self._context)
        self._context.add_command(self._query, response)
        self.response_ready.emit(self._query, response)


# ─── Widget factory helpers ──────────────────────────────────────────────────
def _card() -> QFrame:
    """Dark teal-bordered panel card."""
    f = QFrame()
    f.setStyleSheet("""
        QFrame {
            background: #0d1929;
            border: 1px solid rgba(0,178,216,0.22);
            border-radius: 8px;
        }
    """)
    return f


def _lbl(text="", style="") -> QLabel:
    l = QLabel(text)
    base = "background:transparent; border:none;"
    l.setStyleSheet(base + style)
    return l


def _progress(color="#00b4d8") -> QProgressBar:
    bar = QProgressBar()
    bar.setFixedHeight(5)
    bar.setTextVisible(False)
    bar.setRange(0, 100)
    bar.setStyleSheet(f"""
        QProgressBar {{
            background: #0a1520;
            border: none;
            border-radius: 2px;
        }}
        QProgressBar::chunk {{
            background: {color};
            border-radius: 2px;
        }}
    """)
    return bar


def _mini(icon: str) -> QPushButton:
    btn = QPushButton(icon)
    btn.setFixedSize(20, 20)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet("""
        QPushButton {
            background: transparent;
            border: none;
            color: #4a7a8a;
            font-size: 12px;
        }
        QPushButton:hover { color: #00b4d8; }
    """)
    return btn


def _panel_hdr(title: str, *extra_widgets) -> QWidget:
    """Section header: teal bullet + title + optional right-side widgets."""
    row = QWidget()
    row.setStyleSheet("background: transparent;")
    hl  = QHBoxLayout(row)
    hl.setContentsMargins(0, 0, 0, 0)
    hl.setSpacing(5)

    dot = _lbl("⬤", "color:#00b4d8; font-size:7px;")
    ttl = _lbl(title, "color:#d0d8e0; font-size:12px; font-weight:bold;")
    hl.addWidget(dot)
    hl.addWidget(ttl)
    hl.addStretch()
    for w in extra_widgets:
        hl.addWidget(w)
    return row


# ════════════════════════════════════════════════════════════════════════════
# Main Window
# ════════════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS — AI Desktop Assistant")
        self.setMinimumSize(1100, 650)
        self.resize(1280, 720)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Core
        self.config  = Config()
        self.speech  = SpeechEngine()
        self.context = SessionContext()
        self.router  = CommandRouter(config=self.config)
        self.sm      = StateMachine(self.speech)

        self._drag_pos       = QPoint()
        self._workers: list  = []
        self._session_start  = datetime.datetime.now()
        self._cmd_count      = 0
        self._cam_active     = False

        self._build_ui()
        self._connect_signals()
        self.sm.start()

        # ── Timers ──────────────────────────────────────────────────────
        t = QTimer(self)
        t.timeout.connect(self._tick_clock)
        t.start(1000)
        self._tick_clock()

        t2 = QTimer(self)
        t2.timeout.connect(self._tick_stats)
        t2.start(2000)
        self._tick_stats()

        t3 = QTimer(self)
        t3.timeout.connect(self._tick_uptime)
        t3.start(1000)
        self._tick_uptime()

        self._wx_timer = QTimer(self)
        self._wx_timer.timeout.connect(self._fetch_weather_async)
        self._wx_timer.start(600_000)
        self._has_greeted = False
        QTimer.singleShot(3000, self._fetch_weather_async)  # delay so window appears first

    # ════════════════════════════════════════════════════════════════════
    # UI assembly
    # ════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        root.setStyleSheet("QWidget#root { background: #0a0d14; }")
        self.setCentralWidget(root)

        vl = QVBoxLayout(root)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)
        vl.addWidget(self._make_topbar())

        body = QHBoxLayout()
        body.setContentsMargins(12, 8, 12, 12)
        body.setSpacing(10)
        body.addWidget(self._make_sidebar(),  stretch=0)
        body.addWidget(self._make_centre(),   stretch=1)
        body.addWidget(self._make_chatpanel(), stretch=0)
        vl.addLayout(body, stretch=1)

    # ── Top bar ──────────────────────────────────────────────────────────
    def _make_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(50)
        bar.setStyleSheet("""
            QWidget {
                background: #080b13;
                border-bottom: 1px solid rgba(0,178,216,0.18);
            }
        """)
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(18, 0, 14, 0)
        hl.setSpacing(0)

        # Left — logo + status
        logo = _lbl(
            "J.A.R.V.I.S",
            "color:#e0e8f0; font-size:18px; font-weight:bold; "
            "font-family:'Segoe UI'; letter-spacing:2px;"
        )
        self._status_dot = _lbl(
            "● Online",
            "color:#4ade80; font-size:11px; font-weight:bold; margin-left:10px;"
        )
        left = QHBoxLayout()
        left.setSpacing(0)
        left.addWidget(logo)
        left.addWidget(self._status_dot)
        left.addStretch()

        # Centre — clock | date
        self._clock_lbl = _lbl(
            "",
            "color:#c8d8e0; font-size:13px; font-family:'Segoe UI';"
        )
        self._clock_lbl.setAlignment(Qt.AlignCenter)
        centre_w = QWidget()
        centre_w.setStyleSheet("background:transparent;")
        cl = QHBoxLayout(centre_w)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addStretch()
        cl.addWidget(self._clock_lbl)
        cl.addStretch()

        # Right — weather + window controls
        self._wx_badge = _lbl(
            "🌡  --°C",
            "color:#c8d8e0; font-size:12px; margin-right:8px;"
        )

        def wbtn(txt, slot, col):
            b = QPushButton(txt)
            b.setFixedSize(28, 28)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(slot)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    color: {col};
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background: rgba(255,255,255,8);
                    border-radius: 4px;
                }}
            """)
            return b

        cfg_btn = QPushButton("⚙")
        cfg_btn.setFixedSize(30, 30)
        cfg_btn.setCursor(Qt.PointingHandCursor)
        cfg_btn.setToolTip("Settings")
        cfg_btn.clicked.connect(self._open_settings)
        cfg_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,180,216,0.12);
                border: 1px solid rgba(0,180,216,0.28);
                border-radius: 6px;
                color: #00b4d8;
                font-size: 16px;
            }
            QPushButton:hover { background: rgba(0,180,216,0.24); }
        """)

        right = QHBoxLayout()
        right.setSpacing(6)
        right.addStretch()
        right.addWidget(self._wx_badge)
        right.addWidget(cfg_btn)
        right.addSpacing(4)
        right.addWidget(wbtn("─", self.showMinimized, "#999"))
        right.addWidget(wbtn("□", self._toggle_max, "#999"))
        right.addWidget(wbtn("✕", self.close, "#f87171"))

        hl.addLayout(left,    stretch=1)
        hl.addWidget(centre_w, stretch=1)
        hl.addLayout(right,   stretch=1)

        bar.mousePressEvent = self._tb_press
        bar.mouseMoveEvent  = self._tb_move
        return bar

    # ── Left sidebar ─────────────────────────────────────────────────────
    def _make_sidebar(self) -> QWidget:
        sb = QWidget()
        sb.setFixedWidth(262)
        sb.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(sb)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(8)
        vl.addWidget(self._panel_stats())
        vl.addWidget(self._panel_weather())
        vl.addWidget(self._panel_camera())
        vl.addWidget(self._panel_uptime())
        vl.addStretch()
        return sb

    # ── System Stats panel ──────────────────────────────────────────────
    def _panel_stats(self) -> QFrame:
        card = _card()
        vl   = QVBoxLayout(card)
        vl.setContentsMargins(10, 10, 10, 10)
        vl.setSpacing(7)

        ref = _mini("↻")
        ref.clicked.connect(self._tick_stats)
        vl.addWidget(_panel_hdr("System Stats", ref))

        # CPU row + bar
        r1 = QHBoxLayout()
        r1.addWidget(_lbl("CPU Usage", "color:#8aa8b8; font-size:11px;"))
        self._cpu_pct = _lbl("0%", "color:#00b4d8; font-size:11px; font-weight:bold;")
        r1.addStretch()
        r1.addWidget(self._cpu_pct)
        vl.addLayout(r1)
        self._cpu_bar = _progress()
        vl.addWidget(self._cpu_bar)

        # RAM row + bar
        r2 = QHBoxLayout()
        r2.addWidget(_lbl("RAM Usage", "color:#8aa8b8; font-size:11px;"))
        self._ram_lbl = _lbl("0 GB", "color:#00b4d8; font-size:11px; font-weight:bold;")
        r2.addStretch()
        r2.addWidget(self._ram_lbl)
        vl.addLayout(r2)
        self._ram_bar = _progress()
        vl.addWidget(self._ram_bar)

        # Three circular gauges
        gr = QHBoxLayout()
        gr.setSpacing(2)
        self._g_cpu  = CircularGauge("CPU")
        self._g_mem  = CircularGauge("Memory")
        self._g_disk = CircularGauge("Disk")
        gr.addWidget(self._g_cpu)
        gr.addWidget(self._g_mem)
        gr.addWidget(self._g_disk)
        vl.addLayout(gr)
        return card

    # ── Weather panel ────────────────────────────────────────────────────
    def _panel_weather(self) -> QFrame:
        card = _card()
        vl   = QVBoxLayout(card)
        vl.setContentsMargins(10, 10, 10, 10)
        vl.setSpacing(5)

        ref = _mini("↻")
        ref.clicked.connect(self._fetch_weather)
        vl.addWidget(_panel_hdr("Weather", ref))

        # Temp + icon
        tr = QHBoxLayout()
        self._temp_lbl = _lbl("--°C", "color:#e0e8f0; font-size:22px; font-weight:bold;")
        self._wx_icon  = _lbl("☁", "color:#8aa8b8; font-size:26px;")
        tr.addWidget(self._temp_lbl)
        tr.addStretch()
        tr.addWidget(self._wx_icon)
        vl.addLayout(tr)

        self._city_lbl = _lbl("-- City", "color:#8aa8b8; font-size:11px;")
        self._wx_desc  = _lbl("--", "color:#4a6a7a; font-size:10px;")
        vl.addWidget(self._city_lbl)
        vl.addWidget(self._wx_desc)

        # Stats row
        sr = QHBoxLayout()
        sr.setSpacing(0)
        self._hum_lbl  = self._wx_stat("Humidity",   "--")
        self._wind_lbl = self._wx_stat("Wind",        "--")
        self._feel_lbl = self._wx_stat("Feels Like",  "--")
        sr.addWidget(self._hum_lbl)
        sr.addWidget(self._wind_lbl)
        sr.addWidget(self._feel_lbl)
        vl.addLayout(sr)
        return card

    def _wx_stat(self, title: str, value: str) -> QWidget:
        w  = QWidget()
        w.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 2, 0, 0)
        vl.setSpacing(1)
        val_lbl = _lbl(value, "color:#d0d8e0; font-size:11px; font-weight:bold;")
        ttl_lbl = _lbl(title, "color:#4a6a7a; font-size:10px;")
        vl.addWidget(val_lbl)
        vl.addWidget(ttl_lbl)
        # Store by title for later update
        setattr(self, f"_wx_{title.replace(' ', '_').lower()}_val", val_lbl)
        return w

    # ── Camera panel ─────────────────────────────────────────────────────
    def _panel_camera(self) -> QFrame:
        card = _card()
        vl   = QVBoxLayout(card)
        vl.setContentsMargins(10, 10, 10, 10)
        vl.setSpacing(6)

        snap  = _mini("📸")
        power = _mini("⏻")
        power.clicked.connect(self._toggle_camera)
        vl.addWidget(_panel_hdr("Camera", snap, power))

        # Camera view
        view = QFrame()
        view.setFixedHeight(88)
        view.setStyleSheet("""
            QFrame {
                background: #060d16;
                border: 1px solid rgba(0,180,216,0.14);
                border-radius: 6px;
            }
        """)
        vl2 = QVBoxLayout(view)
        vl2.setAlignment(Qt.AlignCenter)
        cam_ico = _lbl("📹", "color:#1e4a6a; font-size:26px;")
        cam_ico.setAlignment(Qt.AlignCenter)
        self._cam_lbl = _lbl("Camera Off", "color:#1e4a6a; font-size:11px;")
        self._cam_lbl.setAlignment(Qt.AlignCenter)
        vl2.addWidget(cam_ico)
        vl2.addWidget(self._cam_lbl)
        vl.addWidget(view)

        hint = _lbl(
            "Camera is inactive. Click the power button to start.",
            "color:#1e4a6a; font-size:10px;"
        )
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignCenter)
        vl.addWidget(hint)
        return card

    # ── System Uptime panel ──────────────────────────────────────────────
    def _panel_uptime(self) -> QFrame:
        card = _card()
        vl   = QVBoxLayout(card)
        vl.setContentsMargins(10, 10, 10, 10)
        vl.setSpacing(6)

        self._uptime_hdr = _lbl("00:00:00", "color:#00b4d8; font-size:11px;")
        ref = _mini("↻")
        vl.addWidget(_panel_hdr("System Uptime", self._uptime_hdr, ref))

        vl.addWidget(_lbl("System Running For:", "color:#4a6a7a; font-size:11px;"))

        self._uptime_big = _lbl(
            "00:00:00",
            "color:#d0d8e0; font-size:18px; font-weight:bold; font-family:'Courier New';"
        )
        self._uptime_big.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        vl.addWidget(self._uptime_big)

        # Session / Commands
        sc = QHBoxLayout()
        sess_w = QWidget()
        sess_w.setStyleSheet("background:transparent;")
        sv = QVBoxLayout(sess_w)
        sv.setContentsMargins(0, 0, 0, 0)
        sv.setSpacing(0)
        self._sess_lbl = _lbl("1", "color:#d0d8e0; font-size:14px; font-weight:bold;")
        sv.addWidget(self._sess_lbl)
        sv.addWidget(_lbl("Session", "color:#4a6a7a; font-size:10px;"))

        cmd_w = QWidget()
        cmd_w.setStyleSheet("background:transparent;")
        cv = QVBoxLayout(cmd_w)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)
        self._cmd_lbl = _lbl("0", "color:#d0d8e0; font-size:14px; font-weight:bold;")
        cv.addWidget(self._cmd_lbl)
        cv.addWidget(_lbl("Commands", "color:#4a6a7a; font-size:10px;"))

        sc.addWidget(sess_w)
        sc.addStretch()
        sc.addWidget(cmd_w)
        vl.addLayout(sc)

        vl.addWidget(_lbl("System Load", "color:#8aa8b8; font-size:11px;"))
        self._load_bar = _progress("#fb923c")
        vl.addWidget(self._load_bar)
        self._load_lbl = _lbl("Moderate", "color:#fb923c; font-size:10px;")
        vl.addWidget(self._load_lbl)
        return card

    # ── Centre panel ─────────────────────────────────────────────────────
    def _make_centre(self) -> QWidget:
        w  = QWidget()
        w.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(10, 10, 10, 10)
        vl.setSpacing(0)
        vl.setAlignment(Qt.AlignCenter)

        vl.addStretch(1)

        self.orb = JarvisOrb()
        self.orb.setMinimumSize(220, 220)
        self.orb.setMaximumSize(340, 340)
        vl.addWidget(self.orb, alignment=Qt.AlignCenter)

        vl.addSpacing(18)

        title = _lbl(
            "J.A.R.V.I.S",
            "color:#e0e8f0; font-size:22px; font-weight:bold; "
            "font-family:'Segoe UI'; letter-spacing:3px;"
        )
        title.setAlignment(Qt.AlignCenter)
        vl.addWidget(title)

        vl.addSpacing(6)

        self._orb_status = _lbl(
            "● Listening for wake word...",
            "color:#4ade80; font-size:12px;"
        )
        self._orb_status.setAlignment(Qt.AlignCenter)
        vl.addWidget(self._orb_status)

        vl.addStretch(1)

        # Bottom 3 icon buttons
        br = QHBoxLayout()
        br.setAlignment(Qt.AlignCenter)
        br.setSpacing(18)

        self._shot_btn = IconButton("📷", 50, 18)
        self._shot_btn.setToolTip("Take Screenshot")
        self._shot_btn.clicked.connect(self._take_screenshot)

        self._mic_btn = IconButton("🎤", 50, 18)
        self._mic_btn.setToolTip("Activate Voice (Hey Jarvis)")
        self._mic_btn.clicked.connect(self.sm.activate)

        self._kbd_btn = IconButton("⌨", 50, 20)
        self._kbd_btn.setToolTip("Focus text input")
        self._kbd_btn.clicked.connect(self._focus_input)

        br.addWidget(self._shot_btn)
        br.addWidget(self._mic_btn)
        br.addWidget(self._kbd_btn)
        vl.addLayout(br)
        vl.addSpacing(8)
        return w

    # ── Right chat panel ─────────────────────────────────────────────────
    def _make_chatpanel(self) -> QWidget:
        outer = QWidget()
        outer.setFixedWidth(318)
        outer.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(outer)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(6)

        # Main chat card
        card = _card()
        cl   = QVBoxLayout(card)
        cl.setContentsMargins(10, 10, 10, 10)
        cl.setSpacing(6)

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(_lbl("Conversation", "color:#d0d8e0; font-size:13px; font-weight:bold;"))
        hdr.addStretch()
        clr = ToolBtn("⎚ Clear")
        clr.clicked.connect(self._clear_chat)
        ext = ToolBtn("↓ Extract")
        hdr.addWidget(clr)
        hdr.addWidget(ext)
        cl.addLayout(hdr)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(0,178,216,0.18); border:none;")
        cl.addWidget(sep)

        # Chat area
        self._chat_scroll     = ChatScrollArea()
        self._chat_container  = QWidget()
        self._chat_container.setStyleSheet("background: transparent;")
        self._chat_layout     = QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(0, 4, 0, 4)
        self._chat_layout.setSpacing(6)
        self._chat_layout.addStretch()
        self._chat_scroll.setWidget(self._chat_container)
        cl.addWidget(self._chat_scroll, stretch=1)
        vl.addWidget(card, stretch=1)

        # Input bar
        ibar = _card()
        ibar.setFixedHeight(52)
        il   = QHBoxLayout(ibar)
        il.setContentsMargins(10, 8, 8, 8)
        il.setSpacing(6)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type a message...")
        self.text_input.setFont(QFont("Segoe UI", 11))
        self.text_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #d0d8e0;
                font-size: 12px;
            }
        """)
        self.text_input.returnPressed.connect(self._on_submit)

        send = QPushButton("➤")
        send.setFixedSize(32, 32)
        send.setCursor(Qt.PointingHandCursor)
        send.clicked.connect(self._on_submit)
        send.setStyleSheet("""
            QPushButton {
                background: #00b4d8;
                border: none;
                border-radius: 6px;
                color: #050a0e;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover { background: #00ccf0; }
            QPushButton:pressed { background: #0099bb; }
        """)

        il.addWidget(self.text_input, stretch=1)
        il.addWidget(send)
        vl.addWidget(ibar)
        return outer

    # ════════════════════════════════════════════════════════════════════
    # Signal wiring
    # ════════════════════════════════════════════════════════════════════
    def _connect_signals(self):
        self.sm.state_changed.connect(self._on_state)
        self.sm.command_received.connect(self._dispatch)
        self.sm.status_message.connect(lambda m: self._add_msg("jarvis", m))
        self.sm.clap_wake_triggered.connect(self._welcome)
        self.speech.tts.speaking_started.connect(
            lambda: self.orb.set_state("SPEAKING"))
        self.speech.tts.speaking_finished.connect(
            lambda: self.orb.set_state(self.sm.current_state.value))

    # ════════════════════════════════════════════════════════════════════
    # Slots
    # ════════════════════════════════════════════════════════════════════
    def _on_state(self, state: str):
        self.orb.set_state(state)
        tbl = {
            "IDLE":       ("● Listening for wake word...", "#4ade80"),
            "LISTENING":  ("● Listening...",               "#4ade80"),
            "PROCESSING": ("● Processing...",              "#fb923c"),
            "SPEAKING":   ("● Speaking...",                "#00b4d8"),
        }
        txt, col = tbl.get(state.upper(), (f"● {state}", "#9ab0be"))
        self._orb_status.setText(txt)
        self._orb_status.setStyleSheet(
            f"color:{col}; font-size:12px; background:transparent; border:none;"
        )

    def _dispatch(self, query: str):
        self._add_msg("user", query)
        self.orb.set_state("PROCESSING")
        self._cmd_count += 1
        self._cmd_lbl.setText(str(self._cmd_count))

        w = CommandWorker(query, self.context, self.router)
        w.response_ready.connect(self._on_response)
        w.finished.connect(lambda: self._workers.remove(w) if w in self._workers else None)
        self._workers.append(w)
        w.start()

    def _on_response(self, _query: str, response: str):
        self._add_msg("jarvis", response)
        self.speech.speak(response)
        self.orb.set_state(self.sm.current_state.value)

    def _on_submit(self):
        q = self.text_input.text().strip()
        if not q:
            return
        self.text_input.clear()
        self._dispatch(q)

    # ════════════════════════════════════════════════════════════════════
    # Timer callbacks
    # ════════════════════════════════════════════════════════════════════
    def _tick_clock(self):
        now = datetime.datetime.now()
        self._clock_lbl.setText(
            f"🕐  {now.strftime('%I:%M:%S %p')}  |  {now.strftime('%B %d, %Y')}"
        )

    def _tick_stats(self):
        cpu  = psutil.cpu_percent(interval=None)
        mem  = psutil.virtual_memory()

        # Use the system root drive
        root = os.path.abspath(os.sep)
        try:
            dsk = psutil.disk_usage(root)
        except Exception:
            dsk = None

        self._cpu_bar.setValue(int(cpu))
        self._cpu_pct.setText(f"{int(cpu)}%")
        self._g_cpu.set_value(cpu)

        ram_gb = mem.used / (1024 ** 3)
        self._ram_bar.setValue(int(mem.percent))
        self._ram_lbl.setText(f"{ram_gb:.1f} GB")
        self._g_mem.set_value(mem.percent)

        if dsk:
            du_gb = dsk.used  / (1024 ** 3)
            dt_gb = dsk.total / (1024 ** 3)
            self._g_disk.set_value(dsk.percent, f"{du_gb:.0f}G")
        else:
            self._g_disk.set_value(0, "N/A")

    def _tick_uptime(self):
        elapsed = datetime.datetime.now() - self._session_start
        secs    = int(elapsed.total_seconds())
        h, r    = divmod(secs, 3600)
        m, s    = divmod(r, 60)
        txt = f"{h:02d}:{m:02d}:{s:02d}"
        self._uptime_big.setText(txt)
        self._uptime_hdr.setText(txt)

        load = psutil.cpu_percent(interval=None)
        self._load_bar.setValue(int(load))
        if load < 30:
            lbl, col = "Low",      "#4ade80"
        elif load < 70:
            lbl, col = "Moderate", "#fb923c"
        else:
            lbl, col = "High",     "#ef4444"
        self._load_lbl.setText(f"{lbl}  {int(load)}%")
        self._load_lbl.setStyleSheet(
            f"color:{col}; font-size:10px; background:transparent; border:none;"
        )

    def _fetch_weather_async(self):
        """Fetch weather in a background thread so the UI never freezes."""
        class _WxThread(QThread):
            done = pyqtSignal(dict)
            err  = pyqtSignal()
            def run(self_):
                try:
                    r    = requests.get("https://wttr.in/Mumbai?format=j1", timeout=6)
                    data = r.json()
                    self_.done.emit(data)
                except Exception:
                    self_.err.emit()

        t = _WxThread(self)
        t.done.connect(self._apply_weather_data)
        t.err.connect(self._on_weather_error)
        t.finished.connect(lambda: self._workers.remove(t) if t in self._workers else None)
        self._workers.append(t)
        t.start()

    def _apply_weather_data(self, data: dict):
        try:
            cur  = data["current_condition"][0]
            area = data["nearest_area"][0]

            temp   = cur["temp_C"]
            feels  = cur["FeelsLikeC"]
            humid  = cur["humidity"]
            wind   = cur["windspeedKmph"]
            desc   = cur["weatherDesc"][0]["value"]
            city   = "Mumbai"
            ctry   = area["country"][0]["value"]

            self._temp_lbl.setText(f"{temp}°C")
            self._city_lbl.setText(f"{city}, {ctry}")
            self._wx_desc.setText(desc.lower())
            self._wx_badge.setText(f"🌡  {temp}°C  {city}")

            dl = desc.lower()
            if "rain"  in dl: ico = "🌧"
            elif "cloud" in dl: ico = "☁"
            elif "sun"  in dl or "clear" in dl: ico = "☀"
            elif "snow" in dl: ico = "❄"
            elif "storm" in dl: ico = "⛈"
            else: ico = "🌤"
            self._wx_icon.setText(ico)

            self._wx_humidity_val.setText(f"{humid}%")
            self._wx_wind_val.setText(f"{wind} km/h")
            self._wx_feels_like_val.setText(f"{feels}°C")

            if not getattr(self, '_has_greeted', False):
                self._has_greeted = True
                self._welcome()
        except Exception as e:
            print(f"[Weather] parse error: {e}")
            self._on_weather_error()

    def _on_weather_error(self):
        print("[Weather] fetch failed")
        if not getattr(self, '_has_greeted', False):
            self._has_greeted = True
            self._welcome()

    def _fetch_weather(self):
        try:
            r    = requests.get("https://wttr.in/Mumbai?format=j1", timeout=6)
            data = r.json()
            cur  = data["current_condition"][0]
            area = data["nearest_area"][0]

            temp   = cur["temp_C"]
            feels  = cur["FeelsLikeC"]
            humid  = cur["humidity"]
            wind   = cur["windspeedKmph"]
            desc   = cur["weatherDesc"][0]["value"]
            city   = "Mumbai"
            ctry   = area["country"][0]["value"]

            self._temp_lbl.setText(f"{temp}°C")
            self._city_lbl.setText(f"{city}, {ctry}")
            self._wx_desc.setText(desc.lower())
            self._wx_badge.setText(f"🌡  {temp}°C  {city}")

            dl = desc.lower()
            if "rain"  in dl: ico = "🌧"
            elif "cloud" in dl: ico = "☁"
            elif "sun"  in dl or "clear" in dl: ico = "☀"
            elif "snow" in dl: ico = "❄"
            elif "storm" in dl: ico = "⛈"
            else: ico = "🌤"
            self._wx_icon.setText(ico)

            self._wx_humidity_val.setText(f"{humid}%")
            self._wx_wind_val.setText(f"{wind} km/h")
            self._wx_feels_like_val.setText(f"{feels}°C")

            if not getattr(self, '_has_greeted', False):
                self._has_greeted = True
                self._welcome()

        except Exception as e:
            print(f"[Weather] {e}")
            if not getattr(self, '_has_greeted', False):
                self._has_greeted = True
                self._welcome()

    # ════════════════════════════════════════════════════════════════════
    # Chat helpers
    # ════════════════════════════════════════════════════════════════════
    def _add_msg(self, sender: str, text: str):
        if not text.strip():
            return
        ts     = datetime.datetime.now().strftime("%I:%M %p")
        bubble = ChatBubble(sender, text, ts)
        idx    = self._chat_layout.count() - 1  # before the stretch
        self._chat_layout.insertWidget(idx, bubble)
        QTimer.singleShot(50, self._scroll_bottom)

    def _scroll_bottom(self):
        sb = self._chat_scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear_chat(self):
        while self._chat_layout.count() > 1:
            item = self._chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ════════════════════════════════════════════════════════════════════
    # Actions
    # ════════════════════════════════════════════════════════════════════
    def _take_screenshot(self):
        self._dispatch("take a screenshot of the current screen")

    def _focus_input(self):
        self.text_input.setFocus()

    def _toggle_camera(self):
        self._cam_active = not self._cam_active
        if self._cam_active:
            self._cam_lbl.setText("Camera On")
            self._cam_lbl.setStyleSheet("color:#4ade80; font-size:11px; background:transparent;")
        else:
            self._cam_lbl.setText("Camera Off")
            self._cam_lbl.setStyleSheet("color:#1e4a6a; font-size:11px; background:transparent;")

    def _open_settings(self):
        dlg = SettingsDialog(self.config, parent=self)
        dlg.settings_saved.connect(self._on_settings_saved)
        dlg.exec_()

    def _on_settings_saved(self):
        self.router.reload_config(self.config)
        ai = self.config.has_api_key()
        p  = self.config.ai_provider.capitalize()
        self._status_dot.setText(f"● Online (AI · {p})" if ai else "● Online")
        self._add_msg("jarvis", f"Settings saved. {p} AI is now active, sir.")

    # ════════════════════════════════════════════════════════════════════
    # Welcome / prompt
    # ════════════════════════════════════════════════════════════════════
    def _welcome(self):
        temp = self._temp_lbl.text()
        weather = self._wx_desc.text()
        hum = getattr(self, '_wx_humidity_val', None)
        hum_text = hum.text() if hum else "--%"
        cpu = self._cpu_pct.text()
        ram = self._ram_lbl.text()

        if temp == "--°C":
            temp_str = "unknown"
            weather_str = "unknown conditions"
        else:
            temp_str = temp
            weather_str = f"{weather} and {hum_text} humidity"
            
        msg = (
            f"Hello, I’m Jarvis, at your service! The current temperature is {temp_str} with {weather_str}. "
            f"Your system is running at {cpu} CPU usage and {ram} memory used. "
            f"What’s the next task you’d like me to tackle?"
        )
        self._add_msg("jarvis", msg)
        self.speech.speak(msg)
        
        if not self.config.has_api_key():
            QTimer.singleShot(1200, self._prompt_api_key)

    def _prompt_api_key(self):
        self._add_msg(
            "jarvis",
            "No AI provider configured yet. Click ⚙ Settings to choose one:\n"
            "• Gemini — free key at aistudio.google.com/app/apikey\n"
            "• Groq   — free key at console.groq.com (fastest free option)\n"
            "• OpenAI — key at platform.openai.com\n"
            "• Ollama — fully local, no key needed (ollama.com)"
        )

    # ════════════════════════════════════════════════════════════════════
    # Background painting (fills window with solid dark colour)
    # ════════════════════════════════════════════════════════════════════
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#0a0d14"))
        p.end()

    # ════════════════════════════════════════════════════════════════════
    # Window drag / maximize / close
    # ════════════════════════════════════════════════════════════════════
    def _tb_press(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def _tb_move(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPos() - self._drag_pos)

    def _toggle_max(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def closeEvent(self, event):
        self.sm.stop()
        self.speech.cleanup()
        event.accept()
