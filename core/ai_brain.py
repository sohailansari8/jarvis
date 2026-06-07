"""
core/ai_brain.py
Multi-provider AI reasoning engine for JARVIS.

Supported providers (select in Settings ⚙):
  • Gemini   — Google Gemini via google-genai SDK
  • OpenAI   — OpenAI GPT (or any OpenAI-compatible endpoint e.g. Azure, LM Studio)
  • Groq     — Ultra-fast Llama inference, free tier available
  • Ollama   — Fully local inference, no API key needed

Responsibilities:
  - Maintain a rolling conversation history (user + assistant turns)
  - Optionally attach a screenshot for screen-aware reasoning
  - Return a structured JSON action dict that ai_executor.py will execute
  - Gracefully degrade if the API key is missing or the call fails
"""
from __future__ import annotations

import json
import io
import re
import time
import traceback
from typing import Optional

# ── Optional SDK imports (each provider degrades gracefully) ─────────────────

# Gemini — new SDK only (google-genai >= 1.0)
try:
    from google import genai as _genai_new
    from google.genai import types as _genai_types
    HAS_GEMINI_NEW = True
except ImportError:
    HAS_GEMINI_NEW = False
    print("[AIBrain] google-genai not installed. Run: pip install google-genai")

# OpenAI / Groq (both use the openai SDK)
try:
    from openai import OpenAI as _OpenAIClient
    HAS_OPENAI_SDK = True
except ImportError:
    HAS_OPENAI_SDK = False

# Screenshot support
try:
    import pyautogui
    from PIL import Image, ImageGrab
    HAS_SCREENSHOT = True
except ImportError:
    HAS_SCREENSHOT = False


# ── System prompt ────────────────────────────────────────────────────────────
_SYSTEM_PROMPT_TEMPLATE = """
You are JARVIS, an advanced AI desktop assistant running on Windows.
Your job is to understand what the user wants and return a precise JSON action.

ACTIVE PROVIDER: {provider}
SCREEN VISION: {vision_status}

RULES:
1. ALWAYS respond with ONLY a valid JSON object — no markdown, no extra text.
2. Use the conversation history to resolve references like "the first one", "that file",
   "it", "open it", etc. Look at previous assistant save_output data.
3. If a screenshot is provided, use it to understand what is currently on screen.
4. Be smart about context — if the user said "open a Python file" and now says
   "run it", infer they mean run the previously opened file.
5. Prefer the most specific action available.
6. If SCREEN VISION is NOT AVAILABLE and the user asks what is on screen,
   use speak_only to politely explain you cannot see the screen with this provider.

AVAILABLE ACTIONS and their params:
- open_app:        {{ "name": "notepad" }}
- close_app:       {{ "name": "chrome" }}
- open_website:    {{ "url": "https://...", "name": "YouTube" }}
- search_web:      {{ "term": "python tutorials" }}
- play_youtube:    {{ "query": "song or video name", "n": 1 }}  ← use for ANY YouTube playback request
- youtube_nth:     {{ "n": 4 }}  ← use when user says "play the Nth video" from current YouTube results
- type_text:       {{ "text": "Hello world" }}
- click_at:        {{ "x": 500, "y": 300 }}
- find_and_click:  {{ "label": "Submit button" }}
- take_screenshot: {{}}
- system_stats:    {{}}
- open_file:       {{ "path": "C:/Users/..." }}
- list_files:      {{ "directory": "C:/Users/sohail/Desktop", "pattern": "*.py" }}
- key_press:       {{ "keys": ["ctrl", "c"] }}
- scroll:          {{ "direction": "down", "amount": 3 }}
- volume_control:  {{ "action": "up|down|mute", "amount": 5 }}
- play_music:      {{ "query": "song" }}  ← LOCAL music files ONLY, NOT YouTube
- clipboard_read:  {{}}
- clipboard_write: {{ "text": "..." }}
- run_shell:       {{ "command": "dir C:\\\\Users\\\\sohail\\\\Desktop" }}
- speak_only:      {{}}

IMPORTANT YOUTUBE RULES:
- NEVER use play_music for YouTube. Always use play_youtube or youtube_nth.
- If user says "play the 4th video" → use youtube_nth with n=4
- If user says "play [song] on YouTube" → use play_youtube with query=[song] and n=1
- If user says "play the Nth video on YouTube" → use youtube_nth with n=N

RESPONSE FORMAT (strict JSON):
{{
  "action": "<action_name>",
  "params": {{ ... }},
  "speak": "<what Jarvis says out loud — concise, natural>",
  "save_output": {{ "key": "<label>", "value": <any JSON value> }}
}}

"save_output" is OPTIONAL. Use it to save results for future follow-up resolution.
If ambiguous, use speak_only and ask a clarifying question.
""".strip()


class AIBrain:
    """Multi-provider AI reasoning engine with conversation memory."""

    def __init__(self, config):
        self._config = config
        self._history: list[dict] = []
        self._client = None
        self._last_provider: str = ""
        self._last_key: str = ""
        self._init_client()

    # ── Client initialisation ────────────────────────────────────────────────
    def _init_client(self):
        if not self._config:
            return
        p   = self._config.ai_provider
        key = self._active_key()

        # Re-init only if provider or key changed
        if p == self._last_provider and key == self._last_key and self._client is not None:
            return

        self._client = None

        try:
            if p == "gemini":
                self._client = self._init_gemini(key)
            elif p == "openai":
                self._client = self._init_openai(key)
            elif p == "groq":
                self._client = self._init_groq(key)
            elif p == "ollama":
                self._client = self._init_ollama()

            if self._client:
                self._last_provider = p
                self._last_key = key
                print(f"[AIBrain] Initialised provider: {p}")
        except Exception as e:
            print(f"[AIBrain] Client init failed ({p}): {e}")
            self._client = None

    def _active_key(self) -> str:
        p = self._config.ai_provider
        if p == "gemini":  return self._config.gemini_api_key
        if p == "openai":  return self._config.openai_api_key
        if p == "groq":    return self._config.groq_api_key
        return "local"

    def _init_gemini(self, key: str):
        if not key:
            return None
        if HAS_GEMINI_NEW:
            return ("gemini_new", _genai_new.Client(api_key=key))
        print("[AIBrain] google-genai not installed. Run: pip install google-genai")
        return None

    def _init_openai(self, key: str):
        if not key:
            return None
        if not HAS_OPENAI_SDK:
            print("[AIBrain] openai not installed. Run: pip install openai")
            return None
        client = _OpenAIClient(
            api_key=key,
            base_url=self._config.openai_base_url,
        )
        return ("openai", client)

    def _init_groq(self, key: str):
        if not key:
            return None
        if not HAS_OPENAI_SDK:
            print("[AIBrain] openai SDK needed for Groq. Run: pip install openai")
            return None
        # Groq is OpenAI-compatible
        client = _OpenAIClient(
            api_key=key,
            base_url="https://api.groq.com/openai/v1",
        )
        return ("groq", client)

    def _init_ollama(self):
        """Ollama uses its own REST API — no SDK needed."""
        base = self._config.ollama_base_url.rstrip("/")
        return ("ollama", base)

    # ── Public API ────────────────────────────────────────────────────────────
    def is_available(self) -> bool:
        self._init_client()
        return self._client is not None

    def process(self, query: str, context) -> Optional[dict]:
        """Send query to the active AI provider. Returns parsed action dict or None."""
        self._init_client()
        if not self._client:
            return None

        try:
            prompt = self._build_prompt_text(query, context)
            raw    = self._call_provider(prompt, query, context)
            action = self._parse_json(raw)

            # Record turn
            self._push_history("user",  query)
            self._push_history("model", action.get("speak", "Done."))

            max_t = self._config.conversation_max_turns * 2
            if len(self._history) > max_t:
                self._history = self._history[-max_t:]

            return action

        except Exception as e:
            print(f"[AIBrain] Error: {e}")
            traceback.print_exc()
            return None

    def clear_history(self):
        self._history.clear()

    # ── Provider dispatch ─────────────────────────────────────────────────────
    # Providers that support image/vision input
    _VISION_PROVIDERS = {"gemini_new", "openai"}

    def _call_provider(self, prompt: str, query: str, context=None) -> str:
        kind, client = self._client

        # Only attach screenshots for providers that support vision
        img_part = None
        provider_supports_vision = kind in self._VISION_PROVIDERS
        if provider_supports_vision and self._config.needs_screenshot(query) and HAS_SCREENSHOT:
            # Capture a fresh screenshot
            img_part = self._capture_screenshot()
            # If context has a recently saved screenshot (user took one explicitly), prefer it
            if context:
                saved_hex = None
                try:
                    saved_hex = context.get_all_outputs().get("last_screenshot_bytes")
                except Exception:
                    pass
                if saved_hex:
                    try:
                        img_part = {"mime_type": "image/png", "data": bytes.fromhex(saved_hex)}
                        context.save_output("last_screenshot_bytes", None)
                    except Exception:
                        pass

        if kind == "gemini_new":
            return self._call_gemini_new(client, prompt, img_part)
        elif kind in ("openai", "groq"):
            return self._call_openai_compat(client, prompt, img_part)
        elif kind == "ollama":
            return self._call_ollama(client, prompt)
        raise RuntimeError(f"Unknown provider kind: {kind}")

    def _build_system_prompt(self) -> str:
        kind = self._client[0] if self._client else "unknown"
        provider_name = kind.upper()
        vision_status = "AVAILABLE" if kind in self._VISION_PROVIDERS else "NOT AVAILABLE"
        return _SYSTEM_PROMPT_TEMPLATE.format(
            provider=provider_name,
            vision_status=vision_status
        )

    # ── Gemini (new SDK) ──────────────────────────────────────────────────────
    def _call_gemini_new(self, client, prompt: str, img_part) -> str:
        # For Gemini, system prompt is passed at init or config. We inject it here
        # or it could be attached to the contents. The easiest is appending it as a preamble.
        system_prompt = self._build_system_prompt()
        contents = [system_prompt, prompt]
        if img_part:
            contents.append(
                _genai_types.Part.from_bytes(
                    data=img_part["data"],
                    mime_type=img_part["mime_type"],
                )
            )
        response = client.models.generate_content(
            model=self._config.gemini_model,
            contents=contents,
        )
        return response.text.strip()

    # ── OpenAI / Groq ─────────────────────────────────────────────────────────
    def _call_openai_compat(self, client, prompt: str, img_part=None) -> str:
        model = self._config.ai_model
        messages = [{"role": "system", "content": self._build_system_prompt()}]
        # Inject history as alternating user/assistant messages
        for entry in self._history[-20:]:
            messages.append({
                "role":    "user" if entry["role"] == "user" else "assistant",
                "content": entry["text"],
            })
        # Append the current prompt (without the system prompt duplicated)
        if img_part:
            import base64
            b64_data = base64.b64encode(img_part["data"]).decode("utf-8")
            mime = img_part["mime_type"]
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64_data}"}
                    }
                ]
            })
        else:
            messages.append({"role": "user", "content": prompt})

        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=512,
        )
        return resp.choices[0].message.content.strip()

    # ── Ollama ────────────────────────────────────────────────────────────────
    def _call_ollama(self, base_url: str, prompt: str) -> str:
        import urllib.request
        model = self._config.ollama_model
        payload = json.dumps({
            "model":  model,
            "prompt": prompt,
            "stream": False,
            "system": self._build_system_prompt(),
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("response", "").strip()

    # ── Prompt builder ────────────────────────────────────────────────────────
    def _build_prompt_text(self, query: str, context) -> str:
        # We don't include SYSTEM_PROMPT here because Gemini/OpenAI/Ollama 
        # all take the system prompt as a separate parameter/message.
        # But for providers that don't, we can prepend it if needed.
        # Actually _call_gemini_new prepends it, _call_openai_compat uses "system" role.
        # So here we only build the user part.
        lines = []

        if self._history:
            lines.append("--- CONVERSATION HISTORY ---")
            lines.append(self._format_history())
            lines.append("--- END HISTORY ---")
            lines.append("")

        saved = context.get_all_outputs()
        if saved:
            lines.append("--- SAVED CONTEXT DATA ---")
            for k, v in saved.items():
                lines.append(f"  {k}: {json.dumps(v)}")
            lines.append("--- END SAVED DATA ---")
            lines.append("")

        lines.append(f"Currently active window: {context.active_window}")
        lines.append("")
        lines.append(f"User command: {query}")
        lines.append("")
        lines.append("Respond with JSON only:")
        return "\n".join(lines)

    def _format_history(self) -> str:
        lines = []
        for entry in self._history[-20:]:
            role = "User" if entry["role"] == "user" else "Jarvis"
            lines.append(f"{role}: {entry['text']}")
        return "\n".join(lines)

    def _push_history(self, role: str, text: str):
        self._history.append({"role": role, "text": text, "ts": time.time()})

    # ── Screenshot capture ──────────────────────────────────────────────────────
    def _capture_screenshot(self):
        """Capture screen using the most reliable method available."""
        try:
            # Method 1: PIL ImageGrab (most reliable on Windows)
            try:
                screenshot = ImageGrab.grab()
            except Exception:
                # Method 2: pyautogui fallback
                screenshot = pyautogui.screenshot()

            w, h = screenshot.size
            if w > 1280:
                scale = 1280 / w
                screenshot = screenshot.resize((1280, int(h * scale)), Image.LANCZOS)
            buf = io.BytesIO()
            screenshot.save(buf, format="PNG")
            print(f"[AIBrain] Screenshot captured: {w}x{h}px")
            return {"mime_type": "image/png", "data": buf.getvalue()}
        except Exception as e:
            print(f"[AIBrain] Screenshot failed: {e}")
            return None

    # ── JSON parser ───────────────────────────────────────────────────────────
    def _parse_json(self, raw: str) -> dict:
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {
            "action": "speak_only",
            "params": {},
            "speak": raw[:300] if raw else "I'm not sure how to handle that, sir."
        }
