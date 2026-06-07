"""
core/context_manager.py
SessionContext — tracks the active window, conversation history, and
named outputs from previous commands (for follow-up resolution).
"""
import time
import json
from collections import deque

try:
    import pygetwindow as gw
    HAS_PYGETWINDOW = True
except ImportError:
    HAS_PYGETWINDOW = False


class SessionContext:
    """Shared context store passed to every handler and the AI brain."""

    def __init__(self, max_history: int = 20, context_timeout: int = 60):
        self.max_history      = max_history
        self.context_timeout  = context_timeout
        self.command_history: deque = deque(maxlen=max_history)
        self._last_command_time: float | None = None

        # Named outputs — key/value store for cross-turn reference resolution
        # e.g. {"files_list": ["app.py", "test.py"], "last_url": "https://..."}
        self._named_outputs: dict = {}

    # ── Active window ────────────────────────────────────────────────────────
    @property
    def active_window(self) -> str:
        if not HAS_PYGETWINDOW:
            return "Unknown"
        try:
            win = gw.getActiveWindow()
            return win.title if win and win.title else "Desktop"
        except Exception:
            return "Unknown"

    # ── Command history ──────────────────────────────────────────────────────
    def add_command(self, query: str, response: str):
        self.command_history.append({
            "time":     time.time(),
            "query":    query,
            "response": response,
        })
        self._last_command_time = time.time()

    def get_recent(self, n: int = 5) -> list:
        h = list(self.command_history)
        return h[-n:]

    def get_context_summary(self, n: int = 10) -> str:
        """Return last N turns as plain text for the AI prompt."""
        recent = self.get_recent(n)
        if not recent:
            return ""
        lines = []
        for entry in recent:
            lines.append(f"User: {entry['query']}")
            lines.append(f"Jarvis: {entry['response']}")
        return "\n".join(lines)

    # ── Named output store (cross-turn reference resolution) ─────────────────
    def save_output(self, key: str, value):
        """Save a named piece of data for future follow-up resolution."""
        self._named_outputs[key] = value

    def get_output(self, key: str, default=None):
        return self._named_outputs.get(key, default)

    def get_all_outputs(self) -> dict:
        return dict(self._named_outputs)

    def clear_outputs(self):
        self._named_outputs.clear()

    # ── Timing helpers ───────────────────────────────────────────────────────
    def seconds_since_last(self) -> float:
        if self._last_command_time is None:
            return float("inf")
        return time.time() - self._last_command_time

    def is_expired(self) -> bool:
        return self.seconds_since_last() > self.context_timeout

    # ── App-awareness helpers ─────────────────────────────────────────────────
    def is_chrome_active(self) -> bool:
        return "chrome" in self.active_window.lower()

    def is_youtube_active(self) -> bool:
        return "youtube" in self.active_window.lower()

    def is_vscode_active(self) -> bool:
        title = self.active_window.lower()
        return "visual studio code" in title or "vscode" in title

    def is_notepad_active(self) -> bool:
        return "notepad" in self.active_window.lower()

    # ── Full clear ───────────────────────────────────────────────────────────
    def clear(self):
        self.command_history.clear()
        self._named_outputs.clear()
        self._last_command_time = None
