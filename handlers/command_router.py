"""
handlers/command_router.py
Central dispatcher — AI brain first, keyword handlers as fallback.

Priority:
  1. AI Brain (Gemini)  → AIExecutor
  2. Media / Web / System keyword handlers  (unchanged fallback)
  3. Inline knowledge (time, date, jokes, Wikipedia, weather)
"""
from __future__ import annotations

import datetime
import requests
import wikipedia
import pyjokes

from core.ai_brain       import AIBrain
from handlers.ai_executor    import AIExecutor
from handlers.web_handler    import WebHandler
from handlers.system_handler import SystemHandler
from handlers.media_handler  import MediaHandler
from handlers.ocr_handler    import OCRHandler


class CommandRouter:
    def __init__(self, config=None):
        # Config may be None when running without API key (old behaviour)
        self._config = config

        # AI layer (initialised lazily so missing key is graceful)
        self._brain    = AIBrain(config) if config else None
        self._executor = AIExecutor(config)

        # Fallback keyword handlers (always available)
        self.web    = WebHandler()
        self.system = SystemHandler()
        self.media  = MediaHandler()
        self.ocr    = OCRHandler()

    def reload_config(self, config):
        """Called when the user saves new settings in the UI."""
        self._config   = config
        self._brain    = AIBrain(config)
        self._executor = AIExecutor(config)

    def route(self, query: str, context) -> tuple[str, bool]:
        """
        Returns (response_text, handled).
        Tries AI brain first, then falls back to keyword handlers.
        """
        q = query.strip().lower()

        # ── 1. AI Brain ──────────────────────────────────────────────────────
        if self._brain and self._brain.is_available():
            try:
                action = self._brain.process(query, context)
                if action:
                    response = self._executor.execute(action, context)
                    # Use AI's speak line if executor returned nothing extra
                    if not response or response == "Done, sir.":
                        response = action.get("speak", response)
                    return response, True
            except Exception as e:
                print(f"[CommandRouter] AI error, falling back: {e}")
                import traceback; traceback.print_exc()
                # Fall through to keyword handlers

        # ── 2. Keyword fallback — OCR click ──────────────────────────────────
        if any(q.startswith(p) for p in
               ['click on ', 'click ', 'find and click ', 'find ']):
            return self.ocr.handle(q, context)

        # ── 3. Keyword fallback — Media ──────────────────────────────────────
        r, ok = self.media.handle(q, context)
        if ok:
            return r, True

        # ── 4. Keyword fallback — Web ─────────────────────────────────────────
        r, ok = self.web.handle(q, context)
        if ok:
            return r, True

        # ── 5. Keyword fallback — System ──────────────────────────────────────
        r, ok = self.system.handle(q, context)
        if ok:
            return r, True

        # ── 6. Inline knowledge ───────────────────────────────────────────────
        return self._inline(q)

    # ── Inline handlers (time, date, greetings, Wikipedia…) ─────────────────
    def _inline(self, q: str) -> tuple[str, bool]:
        if "time" in q:
            t = datetime.datetime.now().strftime("%I:%M %p")
            return f"The time is {t}, sir.", True

        if "date" in q:
            d = datetime.datetime.now().strftime("%d %B %Y")
            return f"Today is {d}, sir.", True

        if "hello" in q or "hi jarvis" in q:
            return "Hello sir, welcome back! How can I help?", True
        if "how are you" in q:
            return "I'm functioning perfectly, sir. How can I assist?", True
        if "who are you" in q or "what are you" in q:
            return ("I'm JARVIS, your personal AI desktop assistant. "
                    "I can open apps, search the web, control YouTube, "
                    "and much more."), True
        if "thank" in q:
            return "Always at your service, sir.", True
        if "fine" in q or "good" in q:
            return "Glad to hear that, sir!", True

        if "joke" in q:
            return pyjokes.get_joke(), True

        if "wikipedia" in q:
            topic = q.replace("wikipedia", "").replace("search", "").strip()
            if not topic:
                return "What would you like me to search on Wikipedia?", True
            try:
                result = wikipedia.summary(topic, sentences=2)
                return f"According to Wikipedia: {result}", True
            except Exception:
                return "I couldn't find that on Wikipedia.", True

        if "weather" in q:
            try:
                res  = requests.get("https://wttr.in/?format=3", timeout=5)
                data = res.text.strip()
                return f"Current weather: {data}", True
            except Exception:
                return "Sorry, I couldn't fetch the weather right now.", True

        # Final fallback
        provider = self._config.ai_provider.capitalize() if self._config else "AI"
        return ("I didn't quite catch that, sir. "
                f"Make sure your {provider} API key is set in ⚙ Settings for full AI understanding."), False
