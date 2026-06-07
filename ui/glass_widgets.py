"""
ui/glass_widgets.py
Custom PyQt5 widgets for the redesigned J.A.R.V.I.S dark UI.
"""
from __future__ import annotations

import math
import random
import datetime

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QBrush, QPen, QFont,
    QRadialGradient,
)


# ════════════════════════════════════════════════════════════════════════════
# Animated JARVIS Orb — concentric pulsing rings + audio bars
# ════════════════════════════════════════════════════════════════════════════
class JarvisOrb(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._state     = "IDLE"
        self._pulse     = 0.0
        self._pulse_dir = 1
        self._bars      = [0.25, 0.40, 0.55, 0.40, 0.25]
        self._targets   = [0.25, 0.40, 0.55, 0.40, 0.25]

        t = QTimer(self)
        t.timeout.connect(self._step)
        t.start(40)          # ~25 fps

    # ── Public ────────────────────────────────────────────────────────────
    def set_state(self, state: str):
        self._state = (state or "IDLE").upper()

    # legacy alias
    def set_active(self, active: bool):
        self._state = "LISTENING" if active else "IDLE"

    # ── Animation ─────────────────────────────────────────────────────────
    def _step(self):
        speed = 0.04 if "LISTEN" in self._state else 0.018
        self._pulse = max(0.0, min(1.0, self._pulse + speed * self._pulse_dir))
        if self._pulse in (0.0, 1.0):
            self._pulse_dir *= -1

        active  = self._state in ("LISTENING", "PROCESSING", "SPEAKING")
        idle_h  = [0.20, 0.35, 0.48, 0.35, 0.20]
        for i in range(5):
            self._targets[i] = random.uniform(0.12, 0.95) if active else idle_h[i]
            self._bars[i]   += (self._targets[i] - self._bars[i]) * 0.22
        self.update()

    # ── Paint ─────────────────────────────────────────────────────────────
    def paintEvent(self, _event):
        pr = QPainter(self)
        pr.setRenderHint(QPainter.Antialiasing)

        w, h  = self.width(), self.height()
        cx, cy = w / 2, h / 2
        sz    = min(w, h)
        pulse = math.sin(self._pulse * math.pi)     # 0‥1 smooth

        # ── Concentric rings ──────────────────────────────────────────────
        ring_defs = [
            (0.47, 14, 1.0),
            (0.41, 26, 1.2),
            (0.35, 44, 1.5),
            (0.29, 66, 1.7),
        ]
        for rel, base_a, pen_w in ring_defs:
            r = sz * rel * (1.0 + 0.016 * pulse)
            a = int(base_a * (0.75 + 0.25 * pulse))
            pr.setPen(QPen(QColor(0, 178, 216, a), pen_w))
            pr.setBrush(Qt.NoBrush)
            pr.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # ── Inner filled disc ─────────────────────────────────────────────
        ir   = sz * 0.22
        grad = QRadialGradient(cx, cy, ir)
        b    = 0.45 + 0.55 * pulse
        grad.setColorAt(0.0,  QColor(0, 210, 255, int(215 * b)))
        grad.setColorAt(0.55, QColor(0, 118, 190, int(160 * b)))
        grad.setColorAt(1.0,  QColor(0,  48, 100, int(68  * b)))
        pr.setBrush(QBrush(grad))
        pr.setPen(QPen(QColor(0, 200, 240, 45), 0.8))
        pr.drawEllipse(QRectF(cx - ir, cy - ir, ir * 2, ir * 2))

        # ── Audio bars ────────────────────────────────────────────────────
        bw   = ir * 0.19
        gap  = bw * 0.55
        tot  = 5 * bw + 4 * gap
        x0   = cx - tot / 2
        maxh = ir * 0.72

        pr.setPen(Qt.NoPen)
        pr.setBrush(QBrush(QColor(0, 235, 255, 215)))
        for i, frac in enumerate(self._bars):
            bx = x0 + i * (bw + gap)
            bh = max(3.0, maxh * frac)
            by = cy - bh / 2
            pr.drawRoundedRect(QRectF(bx, by, bw, bh), 2, 2)

        pr.end()


# ════════════════════════════════════════════════════════════════════════════
# Circular Donut Gauge (70 × 86 px)
# ════════════════════════════════════════════════════════════════════════════
class CircularGauge(QWidget):

    def __init__(self, label: str = "", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(70, 86)
        self._label = label
        self._value = 0.0
        self._text  = "0%"

    def set_value(self, value: float, text: str = ""):
        self._value = max(0.0, min(100.0, float(value)))
        self._text  = text or f"{int(self._value)}%"
        self.update()

    def paintEvent(self, _event):
        p   = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        mg  = 8
        arc = QRectF(mg, mg, 70 - 2 * mg, 70 - 2 * mg)

        # Track
        p.setPen(QPen(QColor(18, 48, 68), 5, Qt.SolidLine, Qt.FlatCap))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(arc)

        # Value arc
        span = int(-360 * self._value / 100 * 16)
        if   self._value > 80: col = QColor("#ef4444")
        elif self._value > 60: col = QColor("#fb923c")
        else:                  col = QColor("#00b4d8")
        p.setPen(QPen(col, 5, Qt.SolidLine, Qt.FlatCap))
        p.drawArc(arc, 90 * 16, span)

        # Centre text
        p.setPen(QColor("#d0d8e0"))
        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.drawText(QRectF(0, 0, 70, 70), Qt.AlignCenter, self._text)

        # Label below
        p.setPen(QColor("#5a7a8a"))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(QRectF(0, 70, 70, 16), Qt.AlignCenter, self._label)
        p.end()


# ════════════════════════════════════════════════════════════════════════════
# Chat Bubble
# ════════════════════════════════════════════════════════════════════════════
class ChatBubble(QWidget):

    def __init__(self, sender: str, text: str, timestamp: str = "", parent=None):
        super().__init__(parent)
        self._sender = sender.lower()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._build(text, timestamp)

    def _build(self, text: str, ts: str):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 2, 0, 2)
        outer.setSpacing(0)

        frame = QFrame()
        if self._sender == "user":
            frame.setStyleSheet("""
                QFrame {
                    background: #152a42;
                    border: 1px solid rgba(0,180,216,0.38);
                    border-radius: 10px;
                }
            """)
        else:
            frame.setStyleSheet("""
                QFrame {
                    background: #0f2030;
                    border: 1px solid rgba(0,180,216,0.16);
                    border-radius: 10px;
                }
            """)

        inner = QVBoxLayout(frame)
        inner.setContentsMargins(10, 8, 10, 8)
        inner.setSpacing(4)

        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setStyleSheet(
            "color:#d0d8e0; font-size:12px; background:transparent; border:none;"
        )
        inner.addWidget(msg)

        if ts:
            tsl = QLabel(ts)
            tsl.setStyleSheet(
                "color:#2a5a6a; font-size:10px; background:transparent; border:none;"
            )
            inner.addWidget(tsl)

        if self._sender == "user":
            outer.addStretch()
            outer.addWidget(frame)
        else:
            outer.addWidget(frame)
            outer.addStretch()


# ════════════════════════════════════════════════════════════════════════════
# Scrollable chat container
# ════════════════════════════════════════════════════════════════════════════
class ChatScrollArea(QScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #0a1520; width: 5px; border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: #00b4d8; border-radius: 2px; min-height: 18px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
        """)


# ════════════════════════════════════════════════════════════════════════════
# Circular icon button
# ════════════════════════════════════════════════════════════════════════════
class IconButton(QPushButton):

    def __init__(self, icon: str, size: int = 50, font_size: int = 18, parent=None):
        super().__init__(icon, parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        r = size // 2
        self.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,180,216,0.10);
                border: 1px solid rgba(0,180,216,0.30);
                border-radius: {r}px;
                color: #00b4d8;
                font-size: {font_size}px;
            }}
            QPushButton:hover {{
                background: rgba(0,180,216,0.26);
                border: 1px solid rgba(0,180,216,0.65);
            }}
            QPushButton:pressed {{ background: rgba(0,180,216,0.40); }}
        """)


# ════════════════════════════════════════════════════════════════════════════
# Small text tool button
# ════════════════════════════════════════════════════════════════════════════
class ToolBtn(QPushButton):

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(25)
        self.setStyleSheet("""
            QPushButton {
                background: rgba(0,180,216,0.10);
                border: 1px solid rgba(0,180,216,0.28);
                border-radius: 4px;
                color: #00b4d8;
                font-size: 11px;
                padding: 0 8px;
            }
            QPushButton:hover { background: rgba(0,180,216,0.22); }
        """)


# ════════════════════════════════════════════════════════════════════════════
# Backward-compatibility aliases for any code that imports old widget names
# ════════════════════════════════════════════════════════════════════════════
class GlassPanel(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.setStyleSheet(
            "QFrame { background:#0d1929; border:1px solid rgba(0,180,216,0.2);"
            " border-radius:8px; }"
        )


class NeonButton(QPushButton):
    def __init__(self, text="", color=None, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: rgba(0,180,216,0.10);
                border: 1px solid rgba(0,180,216,0.28);
                border-radius: 4px;
                color: #00b4d8;
                padding: 3px 8px;
            }
            QPushButton:hover { background: rgba(0,180,216,0.22); }
        """)


# JarvisOrb IS AnimatedOrb
AnimatedOrb = JarvisOrb


class ChatMessage(ChatBubble):
    """Legacy alias: ChatMessage(sender, text) → ChatBubble with auto-timestamp."""
    def __init__(self, sender, text, parent=None):
        ts = datetime.datetime.now().strftime("%I:%M %p")
        super().__init__(sender, text, ts, parent)


GlassScrollArea = ChatScrollArea
