"""
core/config.py
Manages JARVIS persistent settings stored in ~/jarvis_config.json.
Supports multiple AI providers: Gemini, OpenAI, Groq, Ollama.
"""
import json
import os

_CONFIG_PATH = os.path.join(os.path.expanduser("~"), "jarvis_config.json")

_DEFAULTS = {
    # ── AI provider ────────────────────────────────────────────────────
    # Options: "gemini" | "openai" | "groq" | "ollama"
    "ai_provider":            "gemini",

    # Gemini
    "gemini_api_key":         "",
    "gemini_model":           "gemini-2.0-flash",

    # OpenAI  (also works with any OpenAI-compatible endpoint)
    "openai_api_key":         "",
    "openai_model":           "gpt-4o-mini",
    "openai_base_url":        "https://api.openai.com/v1",

    # Groq  (free tier, very fast)
    "groq_api_key":           "",
    "groq_model":             "llama-3.3-70b-versatile",

    # Ollama  (fully local, no key needed)
    "ollama_base_url":        "http://localhost:11434",
    "ollama_model":           "llama3",

    # ── Vision / conversation ─────────────────────────────────────────
    "enable_vision":          True,
    "vision_always":          False,
    "conversation_max_turns": 20,
    "vision_trigger_words": [
        "first", "second", "third", "that", "it", "the one", "this",
        "there", "here", "visible", "screen", "window", "file", "folder",
        "button", "icon", "link", "open", "click",
        "see", "look", "show", "describe", "what is", "what's",
        "read", "tell me", "currently", "right now", "on screen",
        "screenshot", "capture", "display", "monitor"
    ],
}


class Config:
    """Singleton-like config wrapper. Call Config() anywhere to get the live config."""

    def __init__(self):
        self._data: dict = dict(_DEFAULTS)
        self._load()

    # ── I/O ─────────────────────────────────────────────────
    def _load(self):
        if os.path.exists(_CONFIG_PATH):
            try:
                with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                self._data.update(stored)
            except Exception:
                pass  # corrupt file → use defaults

    def save(self):
        try:
            with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f"[Config] Could not save: {e}")

    # ── Provider selector ────────────────────────────────────
    @property
    def ai_provider(self) -> str:
        return self._data.get("ai_provider", "gemini")

    @ai_provider.setter
    def ai_provider(self, value: str):
        self._data["ai_provider"] = value

    # ── Gemini ───────────────────────────────────────────────
    @property
    def api_key(self) -> str:          # legacy alias → gemini key
        return self._data.get("gemini_api_key", "")

    @api_key.setter
    def api_key(self, value: str):
        self._data["gemini_api_key"] = value.strip()

    @property
    def gemini_api_key(self) -> str:
        return self._data.get("gemini_api_key", "")

    @gemini_api_key.setter
    def gemini_api_key(self, value: str):
        self._data["gemini_api_key"] = value.strip()

    @property
    def gemini_model(self) -> str:
        return self._data.get("gemini_model", "gemini-2.0-flash")

    @gemini_model.setter
    def gemini_model(self, value: str):
        self._data["gemini_model"] = value.strip()

    # ── OpenAI ───────────────────────────────────────────────
    @property
    def openai_api_key(self) -> str:
        return self._data.get("openai_api_key", "")

    @openai_api_key.setter
    def openai_api_key(self, value: str):
        self._data["openai_api_key"] = value.strip()

    @property
    def openai_model(self) -> str:
        return self._data.get("openai_model", "gpt-4o-mini")

    @openai_model.setter
    def openai_model(self, value: str):
        self._data["openai_model"] = value.strip()

    @property
    def openai_base_url(self) -> str:
        return self._data.get("openai_base_url", "https://api.openai.com/v1")

    @openai_base_url.setter
    def openai_base_url(self, value: str):
        self._data["openai_base_url"] = value.strip()

    # ── Groq ─────────────────────────────────────────────────
    @property
    def groq_api_key(self) -> str:
        return self._data.get("groq_api_key", "")

    @groq_api_key.setter
    def groq_api_key(self, value: str):
        self._data["groq_api_key"] = value.strip()

    @property
    def groq_model(self) -> str:
        return self._data.get("groq_model", "llama-3.3-70b-versatile")

    @groq_model.setter
    def groq_model(self, value: str):
        self._data["groq_model"] = value.strip()

    # ── Ollama ───────────────────────────────────────────────
    @property
    def ollama_base_url(self) -> str:
        return self._data.get("ollama_base_url", "http://localhost:11434")

    @ollama_base_url.setter
    def ollama_base_url(self, value: str):
        self._data["ollama_base_url"] = value.strip()

    @property
    def ollama_model(self) -> str:
        return self._data.get("ollama_model", "llama3")

    @ollama_model.setter
    def ollama_model(self, value: str):
        self._data["ollama_model"] = value.strip()

    # ── Shared / legacy ──────────────────────────────────────
    @property
    def ai_model(self) -> str:
        """Returns the active model name for the currently selected provider."""
        p = self.ai_provider
        if p == "gemini":  return self.gemini_model
        if p == "openai":  return self.openai_model
        if p == "groq":    return self.groq_model
        if p == "ollama":  return self.ollama_model
        return "gemini-2.0-flash"

    @property
    def enable_vision(self) -> bool:
        return bool(self._data.get("enable_vision", True))

    @enable_vision.setter
    def enable_vision(self, value: bool):
        self._data["enable_vision"] = value

    @property
    def vision_always(self) -> bool:
        return bool(self._data.get("vision_always", False))

    @vision_always.setter
    def vision_always(self, value: bool):
        self._data["vision_always"] = value

    @property
    def conversation_max_turns(self) -> int:
        return int(self._data.get("conversation_max_turns", 20))

    @conversation_max_turns.setter
    def conversation_max_turns(self, value: int):
        self._data["conversation_max_turns"] = value

    @property
    def vision_trigger_words(self) -> list:
        return self._data.get("vision_trigger_words", _DEFAULTS["vision_trigger_words"])

    def has_api_key(self) -> bool:
        """True if the active provider has credentials configured."""
        p = self.ai_provider
        if p == "ollama":  return True          # local — no key needed
        if p == "gemini":  return bool(self.gemini_api_key)
        if p == "openai":  return bool(self.openai_api_key)
        if p == "groq":    return bool(self.groq_api_key)
        return False

    def needs_screenshot(self, query: str) -> bool:
        """Decide whether this query warrants sending a screenshot."""
        if not self.enable_vision:
            return False
        if self.vision_always:
            return True
        q = query.lower()
        # Check all trigger words
        if any(word in q for word in self.vision_trigger_words):
            return True
        # Extra phrase-level patterns for screen-awareness
        screen_phrases = [
            "what do you see", "what can you see", "what is on",
            "what's on", "describe the", "look at", "can you see",
            "take a screenshot", "take screenshot", "screen shot",
            "what is happening", "what's happening", "what is open",
            "what's open", "tell me what", "analyze the screen",
            "read the screen", "read what", "summarize the screen",
        ]
        return any(phrase in q for phrase in screen_phrases)
