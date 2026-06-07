"""
core/speech_engine.py
Handles Text-to-Speech using Microsoft edge-tts (J.A.R.V.I.S voice) in a dedicated QThread and
exposes a simple listen() helper for Speech-to-Text.
"""
import queue
import tempfile
import os
import asyncio
import speech_recognition as sr
import edge_tts

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

from PyQt5.QtCore import QThread, pyqtSignal


class TTSWorker(QThread):
    """Dedicated thread for edge-tts so it never blocks the UI or STT."""
    speaking_started = pyqtSignal()
    speaking_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue: queue.Queue = queue.Queue()
        self.daemon = True
        # pygame.mixer is initialised inside run() so it never blocks the UI thread

    def run(self):
        # Initialise mixer here (worker thread) so __init__ is instant
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"[TTS] pygame mixer init failed: {e}")
        # We need an event loop for edge-tts
        asyncio.run(self._process_queue())
        try:
            pygame.mixer.quit()
        except Exception:
            pass

    async def _process_queue(self):
        while True:
            text = self._queue.get()
            if text is None:          # poison-pill → exit
                break
                
            self.speaking_started.emit()
            
            try:
                # Use a temporary file for the mp3
                fd, path = tempfile.mkstemp(suffix=".mp3")
                os.close(fd)
                
                # J.A.R.V.I.S style British male voice
                voice = 'en-GB-RyanNeural'
                communicate = edge_tts.Communicate(text, voice, rate="+5%")
                await communicate.save(path)
                
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                
                # Wait for audio to finish
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.05)
                
                # Unload so we can delete the temp file
                pygame.mixer.music.unload()
                try:
                    os.remove(path)
                except Exception:
                    pass
            except Exception as e:
                print(f"[TTS] Error generating/playing speech: {e}")
                
            self.speaking_finished.emit()

    def speak(self, text: str):
        """Queue a string for speaking (non-blocking)."""
        self._queue.put(text)

    def stop(self):
        self._queue.put(None)


class SpeechEngine:
    """
    Thin wrapper that owns the TTSWorker thread and provides
    a simple listen() method for capturing voice input.
    """

    def __init__(self):
        self.tts = TTSWorker()
        self.tts.start()
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    # ── TTS ────────────────────────────────────────────────
    def speak(self, text: str):
        """Non-blocking speak."""
        self.tts.speak(text)

    # ── STT ────────────────────────────────────────────────
    def listen(self, source, timeout: int = 5, phrase_time_limit: int = 8) -> str:
        """
        Listen on an already-open Microphone source.
        Returns transcribed text (lowercase) or '' on failure.
        """
        try:
            audio = self.recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit
            )
            return self.recognizer.recognize_google(audio, language='en-in').lower()
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception:
            return ""

    def adjust_ambient(self, source, duration: float = 1.0):
        self.recognizer.adjust_for_ambient_noise(source, duration=duration)

    def cleanup(self):
        self.tts.stop()
