"""
ui/status_dashboard.py
Right-side panel showing:
  - Current state badge
  - CPU / RAM / Battery progress bars
  - Active window
  - Context timer countdown
Updates every 2 seconds via QTimer.
"""
import psutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QBrush, QLinearGradient, QFont, QPen
)
from ui.glass_widgets import GlassPanel, TEXT_DIM, TEXT_PRIMARY


# ── Thin neon progress bar ─────────────────────────────────────
class NeonBar(QWidget):
    def __init__(self, label: str, color: QColor, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._label = label
        self._color = color
        self._value = 0
        self.setFixedHeight(34)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_value(self, v: float):
        self._value = max(0.0, min(1.0, v))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Label
        p.setFont(QFont("Segoe UI", 9))
        p.setPen(QPen(QColor("#8888aa")))
        p.drawText(0, 0, 60, h, Qt.AlignVCenter | Qt.AlignLeft, self._label)

        # Track
        tx, ty, tw, th = 65, h//2 - 4, w - 65 - 38, 8
        track = QRectF(tx, ty, tw, th)
        p.setBrush(QBrush(QColor(255, 255, 255, 15)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(track, 4, 4)

        # Fill
        fill_w = tw * self._value
        if fill_w > 0:
            grad = QLinearGradient(tx, 0, tx + tw, 0)
            c0 = QColor(self._color); c0.setAlpha(200)
            c1 = QColor(self._color).lighter(130); c1.setAlpha(255)
            grad.setColorAt(0, c0)
            grad.setColorAt(1, c1)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(QRectF(tx, ty, fill_w, th), 4, 4)

        # Percentage text
        p.setPen(QPen(QColor(self._color)))
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        pct = f"{int(self._value * 100)}%"
        p.drawText(w - 36, 0, 36, h, Qt.AlignVCenter | Qt.AlignRight, pct)


# ── State badge ───────────────────────────────────────────────
class StateBadge(QWidget):
    COLORS = {
        "IDLE":       "#00f5ff",
        "LISTENING":  "#bf5fff",
        "PROCESSING": "#ffee00",
        "SPEAKING":   "#39ff14",
        "ERROR":      "#ff3355",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._state = "IDLE"
        self.setFixedHeight(36)

    def set_state(self, state: str):
        self._state = state
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        color = QColor(self.COLORS.get(self._state, "#00f5ff"))

        # Pill background
        fill = QColor(color); fill.setAlpha(30)
        p.setBrush(QBrush(fill))
        border = QColor(color); border.setAlpha(160)
        p.setPen(QPen(border, 1.2))
        rect = QRectF(0, 4, self.width(), 28)
        p.drawRoundedRect(rect, 14, 14)

        # Dot
        dot = QColor(color)
        p.setBrush(QBrush(dot)); p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(12, 12, 12, 12))

        # Text
        p.setPen(QPen(color))
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(QRectF(32, 4, self.width() - 36, 28),
                   Qt.AlignVCenter | Qt.AlignLeft,
                   self._state)


# ═══════════════════════════════════════════════════════════════
class StatusDashboard(GlassPanel):
    """Right sidebar with live system stats and context info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)
        self._ctx = None   # set by main window
        self._ctx_timeout = 20
        self._build_ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(2000)

    def set_context(self, ctx):
        self._ctx = ctx

    # ── Build ─────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("◈  SYSTEM STATUS")
        title.setStyleSheet(
            "color: #00f5ff; font-size: 10px; font-weight: bold; "
            "font-family: 'Segoe UI'; letter-spacing: 3px;"
        )
        layout.addWidget(title)

        # State badge
        self.state_badge = StateBadge()
        layout.addWidget(self.state_badge)

        self._divider(layout)

        # CPU / RAM / Battery bars
        self.cpu_bar = NeonBar("CPU", QColor("#00f5ff"))
        self.ram_bar = NeonBar("RAM", QColor("#bf5fff"))
        self.bat_bar = NeonBar("BAT", QColor("#39ff14"))
        layout.addWidget(self.cpu_bar)
        layout.addWidget(self.ram_bar)
        layout.addWidget(self.bat_bar)

        self._divider(layout)

        # Active window
        win_title = QLabel("ACTIVE APP")
        win_title.setStyleSheet(
            "color: #555577; font-size: 9px; letter-spacing: 2px; font-family: 'Segoe UI';"
        )
        self.win_label = QLabel("—")
        self.win_label.setWordWrap(True)
        self.win_label.setStyleSheet(
            "color: #aaaacc; font-size: 11px; font-family: 'Segoe UI';"
        )
        layout.addWidget(win_title)
        layout.addWidget(self.win_label)

        self._divider(layout)

        # Context timer
        ctx_title = QLabel("CONTEXT WINDOW")
        ctx_title.setStyleSheet(
            "color: #555577; font-size: 9px; letter-spacing: 2px; font-family: 'Segoe UI';"
        )
        self.ctx_label = QLabel("—")
        self.ctx_label.setStyleSheet(
            "color: #aaaacc; font-size: 11px; font-family: 'Segoe UI';"
        )
        layout.addWidget(ctx_title)
        layout.addWidget(self.ctx_label)

        layout.addStretch()

        # OCR status
        from handlers.ocr_handler import OCRHandler
        ocr_ok = OCRHandler.is_available()
        ocr_label = QLabel(f"OCR: {'✓ Active' if ocr_ok else '✗ Tesseract not found'}")
        ocr_label.setStyleSheet(
            f"color: {'#39ff14' if ocr_ok else '#ff3355'}; "
            "font-size: 9px; font-family: 'Segoe UI';"
        )
        layout.addWidget(ocr_label)

    # ── Refresh ───────────────────────────────────────────────
    def _refresh(self):
        # Stats
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        bat = psutil.sensors_battery()
        bat_pct = bat.percent if bat else 0

        self.cpu_bar.set_value(cpu / 100)
        self.ram_bar.set_value(ram / 100)
        self.bat_bar.set_value(bat_pct / 100)

        # Context
        if self._ctx:
            self.win_label.setText(self._ctx.active_window[:28] or "—")
            secs = self._ctx.seconds_since_last()
            if secs == float('inf'):
                self.ctx_label.setText("No commands yet")
            elif secs < self._ctx_timeout:
                remaining = int(self._ctx_timeout - secs)
                self.ctx_label.setText(f"{remaining}s remaining")
            else:
                self.ctx_label.setText("Expired")

    def update_state(self, state: str):
        self.state_badge.set_state(state)

    # ── Helper ────────────────────────────────────────────────
    def _divider(self, layout):
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background: rgba(255,255,255,20);")
        layout.addWidget(line)
