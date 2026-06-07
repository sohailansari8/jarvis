"""
handlers/web_handler.py
Browser, Google/YouTube search, and YouTube playback control.
"""
import webbrowser
import pyautogui
import pyperclip
import time
import re


SITES = {
    'youtube':       'https://www.youtube.com',
    'google':        'https://www.google.com',
    'facebook':      'https://www.facebook.com',
    'instagram':     'https://www.instagram.com',
    'twitter':       'https://www.twitter.com',
    'github':        'https://www.github.com',
    'stackoverflow': 'https://www.stackoverflow.com',
    'reddit':        'https://www.reddit.com',
    'netflix':       'https://www.netflix.com',
    'spotify':       'https://www.spotify.com',
    'amazon':        'https://www.amazon.in',
    'whatsapp':      'https://web.whatsapp.com',
}


class WebHandler:
    def handle(self, query: str, context) -> tuple[str, bool]:
        # ── 1. Open named site ───────────────────────────────
        for site, url in SITES.items():
            if f'open {site}' in query:
                webbrowser.open(url)
                return f"Opening {site.capitalize()}, sir.", True

        # ── 2. Search on Google / Chrome ─────────────────────
        term = self._extract_search_term(query)
        if term:
            url = f"https://www.google.com/search?q={term.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Searching for {term}.", True

        # ── 3. Play on YouTube ─────────────────────────────────────────────────
        if 'play' in query and ('youtube' in query or 'on youtube' in query or 'in youtube' in query):
            song = (query.replace('play', '')
                         .replace('on youtube', '')
                         .replace('in youtube', '')
                         .replace('youtube', '')
                         .strip())

            # Check if asking to play the Nth video (from current results)
            nth = self._extract_video_number(song)
            if nth and context.is_youtube_active():
                self._play_nth_video(nth)
                return f"Playing the {self._ordinal(nth)} video, sir.", True

            if context.is_youtube_active():
                # Use existing window
                pyautogui.press('/')
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('backspace')
                pyautogui.write(song, interval=0.02)
                pyautogui.press('enter')
                time.sleep(2.5) # Wait for results
                # Auto-play first result
                self._play_nth_video(1)
                return f"Playing {song} on YouTube.", True
            else:
                url = f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}"
                webbrowser.open(url)
                time.sleep(4)
                self._play_nth_video(1)
                return f"Playing {song} on YouTube.", True

        # ── 4. YouTube playback controls (context-aware) ───────────────────────
        if context.is_youtube_active():
            result = self._youtube_controls(query)
            if result:
                return result

        return "", False

    # ── Helpers ──────────────────────────────────────────────
    def _extract_search_term(self, query: str) -> str:
        """Return search term from various phrasings, or ''."""
        for pattern in [
            'search for ', 'search ', 'google ', 'look up ',
            'find ', 'search on chrome ', 'search on google '
        ]:
            if query.startswith(pattern):
                return query[len(pattern):].strip()
        if 'search' in query and 'for' in query:
            idx = query.index('for') + 3
            return query[idx:].strip()
        return ''

    def _youtube_controls(self, query: str):
        # Play the Nth video from current results page
        nth = self._extract_video_number(query)
        if nth is not None and ('video' in query or 'result' in query):
            self._play_nth_video(nth)
            return f"Playing the {self._ordinal(nth)} video, sir.", True

        if 'first video' in query:
            self._play_nth_video(1)
            return "Playing the first video, sir.", True
        if 'pause' in query or ('play' in query and 'youtube' not in query):
            pyautogui.press('k')
            return "Toggling YouTube playback.", True
        if 'next' in query:
            pyautogui.hotkey('shift', 'n')
            return "Next video.", True
        if 'previous' in query or 'prev' in query:
            pyautogui.press('j')
            return "Going back.", True
        if 'mute' in query:
            pyautogui.press('m')
            return "Muted.", True
        if 'fullscreen' in query or 'full screen' in query:
            pyautogui.press('f')
            return "Toggled fullscreen.", True
        if 'volume up' in query:
            for _ in range(5): pyautogui.press('up')
            return "Volume up.", True
        if 'volume down' in query:
            for _ in range(5): pyautogui.press('down')
            return "Volume down.", True
        if 'skip' in query:
            pyautogui.press('l')
            return "Skipped 10 seconds.", True
        return None

    def _play_nth_video(self, n: int = 1):
        """Click the Nth video on a YouTube results/home page using JS via address bar.
        Uses clipboard paste so special characters survive intact."""
        # YouTube search results: ytd-video-renderer links
        # nth-of-type is 1-based in CSS
        js = (
            f"javascript:(function(){{"
            f"var vids=document.querySelectorAll("
            f"'ytd-video-renderer a#video-title,ytd-rich-item-renderer a#video-title-link'"
            f");if(vids.length>={n}){{vids[{n-1}].click();}}"
            f"else if(vids.length>0){{vids[0].click();}}"
            f"}})();"
        )
        # Put JS into clipboard then paste — avoids pyautogui.write() dropping special chars
        try:
            old_clip = pyperclip.paste()
        except Exception:
            old_clip = ""
        pyperclip.copy(js)
        pyautogui.hotkey('ctrl', 'l')   # focus address bar
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'a')   # select all
        pyautogui.hotkey('ctrl', 'v')   # paste JS
        time.sleep(0.2)
        pyautogui.press('enter')
        time.sleep(0.5)
        # Restore clipboard
        try:
            pyperclip.copy(old_clip)
        except Exception:
            pass

    def _play_first_video_js(self):
        """Backwards-compat alias."""
        self._play_nth_video(1)

    def _extract_video_number(self, query: str):
        """Extract ordinal/cardinal video number from query. Returns int or None."""
        # Ordinal words
        ordinals = {
            'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
            'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10,
        }
        q = query.lower()
        for word, num in ordinals.items():
            if word in q:
                return num
        # Numeric ordinals: 1st, 2nd, 3rd, 4th ... 10th
        match = re.search(r'(\d+)(?:st|nd|rd|th)', q)
        if match:
            return int(match.group(1))
        # Plain number followed by "video"
        match = re.search(r'(\d+)\s+video', q)
        if match:
            return int(match.group(1))
        return None

    def _ordinal(self, n: int) -> str:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10 if n % 100 not in (11,12,13) else 0, 'th')
        return f"{n}{suffix}"
