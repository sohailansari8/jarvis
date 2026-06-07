"""
core/state_machine.py
IDLE ──(wake word)──► ACTIVE ──(20 s timeout / sleep word)──► IDLE
Runs entirely in a QThread; communicates with the UI via signals.
"""
import time
import speech_recognition as sr
from enum import Enum
from PyQt5.QtCore import QThread, pyqtSignal


class State(Enum):
    IDLE       = "IDLE"
    LISTENING  = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING   = "SPEAKING"


WAKE_WORDS  = ["hey jarvis", "jarvis", "ok jarvis", "hello jarvis"]
SLEEP_WORDS = ["sleep", "goodbye", "bye jarvis", "go to sleep",
               "finally sleep", "quit", "exit"]
CONTEXT_TIMEOUT = 20  # seconds


class StateMachine(QThread):
    # ── Signals ────────────────────────────────────────────
    state_changed    = pyqtSignal(str)   # State.value
    command_received = pyqtSignal(str)   # transcribed command text
    status_message   = pyqtSignal(str)   # short status for UI log
    wake_detected    = pyqtSignal()      # pulse the orb
    clap_wake_triggered = pyqtSignal()   # specific signal to run _welcome script

    def __init__(self, speech_engine, parent=None):
        super().__init__(parent)
        self.speech   = speech_engine
        self._state   = State.IDLE
        self._running = True
        self._last_cmd_time: float = 0.0

    # ── Public API ──────────────────────────────────────────
    def activate(self):
        """Manually switch to ACTIVE from the UI mic button."""
        if self._state == State.IDLE:
            self._set_state(State.LISTENING)
            self.status_message.emit("Activated manually — listening…")

    def stop(self):
        self._running = False

    # ── Thread entry ────────────────────────────────────────
    def run(self):
        recognizer = sr.Recognizer()
        recognizer.energy_threshold        = 300
        recognizer.dynamic_energy_threshold = True

        with sr.Microphone() as source:
            self.status_message.emit("Ready — say 'Hey Jarvis' to activate")
            recognizer.adjust_for_ambient_noise(source, duration=0.3)  # fast calibration

            while self._running:
                if self._state == State.IDLE:
                    self._idle_loop(recognizer, source)
                elif self._state == State.LISTENING:
                    self._active_loop(recognizer, source)

    # ── IDLE: listen only for wake word ─────────────────────
    def _idle_loop(self, recognizer: sr.Recognizer, source):
        try:
            audio = recognizer.listen(source, timeout=2, phrase_time_limit=4)
            
            # Check for clap (loud amplitude spike)
            import struct
            raw_data = audio.frame_data
            if raw_data and audio.sample_width == 2:
                shorts = struct.unpack(f"<{len(raw_data)//2}h", raw_data)
                peak = max(abs(s) for s in shorts) if shorts else 0
                if peak > 18000:
                    self.clap_wake_triggered.emit()
                    self.wake_detected.emit()
                    self._set_state(State.LISTENING)
                    self.status_message.emit("Clap detected — waking up!")
                    return
            
            text  = recognizer.recognize_google(audio, language='en-in').lower()
            if any(w in text for w in WAKE_WORDS):
                self.wake_detected.emit()
                self._set_state(State.LISTENING)
                self.status_message.emit("Wake word detected — listening for command…")
                self.speech.speak("Yes sir?")
        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except Exception:
            pass

    # ── ACTIVE: listen for commands, 20-second context window ──
    def _active_loop(self, recognizer: sr.Recognizer, source):
        try:
            # Wait up to CONTEXT_TIMEOUT seconds for speech
            audio = recognizer.listen(
                source,
                timeout=CONTEXT_TIMEOUT,
                phrase_time_limit=12
            )
            text = recognizer.recognize_google(audio, language='en-in').lower()

            if not text:
                return

            # Sleep word → go back to IDLE
            if any(w in text for w in SLEEP_WORDS):
                self._set_state(State.IDLE)
                self.status_message.emit("Going to sleep — say 'Hey Jarvis' to wake me")
                self.speech.speak("Going to sleep. Say Hey Jarvis when you need me.")
                return

            # Valid command
            self._last_cmd_time = time.time()
            self._set_state(State.PROCESSING)
            self.status_message.emit(f"Command: {text}")
            self.command_received.emit(text)
            # Return to LISTENING to stay in ACTIVE context
            self._set_state(State.LISTENING)

        except sr.WaitTimeoutError:
            # 20-second silence → return to IDLE
            self._set_state(State.IDLE)
            self.status_message.emit("Context timeout — returning to idle")
            self.speech.speak("Context timeout. Going idle.")
        except sr.UnknownValueError:
            # Couldn't parse speech; stay LISTENING
            self.status_message.emit("Didn't catch that — still listening…")
        except Exception:
            self._set_state(State.IDLE)

    # ── Helper ───────────────────────────────────────────────
    def _set_state(self, new_state: State):
        self._state = new_state
        self.state_changed.emit(new_state.value)

    @property
    def current_state(self) -> State:
        return self._state
