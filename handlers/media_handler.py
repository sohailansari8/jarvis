"""
handlers/media_handler.py
Local music playback and system volume control via media keys.
"""
import os
import random
import pyautogui


MUSIC_DIRS = [
    os.path.join(os.path.expanduser("~"), "Music"),
    os.path.join(os.path.expanduser("~"), "Downloads"),
]
AUDIO_EXTS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}


class MediaHandler:
    def handle(self, query: str, context) -> tuple[str, bool]:
        # ── Play local music ─────────────────────────────────
        if 'play music' in query or 'play a song' in query or 'play some music' in query:
            return self._play_local_music()

        # ── Stop / pause music ───────────────────────────────
        if 'stop music' in query or 'pause music' in query:
            pyautogui.press('playpause')
            return "Pausing music.", True

        # ── Volume controls (global) ──────────────────────────
        if 'volume up' in query:
            reps = self._extract_number(query, default=3)
            for _ in range(reps):
                pyautogui.press('volumeup')
            return f"Volume raised.", True

        if 'volume down' in query:
            reps = self._extract_number(query, default=3)
            for _ in range(reps):
                pyautogui.press('volumedown')
            return "Volume lowered.", True

        if 'mute' in query or 'unmute' in query:
            pyautogui.press('volumemute')
            return "Toggled mute.", True

        # ── Next / previous track ─────────────────────────────
        if 'next track' in query or 'next song' in query:
            pyautogui.press('nexttrack')
            return "Skipping to next track.", True

        if 'previous track' in query or 'previous song' in query or 'last track' in query:
            pyautogui.press('prevtrack')
            return "Going to previous track.", True

        return "", False

    # ── Helpers ──────────────────────────────────────────────
    def _play_local_music(self) -> tuple[str, bool]:
        songs = []
        for d in MUSIC_DIRS:
            if os.path.exists(d):
                for f in os.listdir(d):
                    if os.path.splitext(f)[1].lower() in AUDIO_EXTS:
                        songs.append(os.path.join(d, f))
        if not songs:
            return "I couldn't find any music files on your computer.", True
        song = random.choice(songs)
        os.startfile(song)
        name = os.path.splitext(os.path.basename(song))[0]
        return f"Playing {name}.", True

    def _extract_number(self, query: str, default: int = 3) -> int:
        words = {'one': 1, 'two': 2, 'three': 3, 'four': 4,
                 'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
                 'nine': 9, 'ten': 10}
        for w, n in words.items():
            if w in query:
                return n
        for token in query.split():
            if token.isdigit():
                return int(token)
        return default
