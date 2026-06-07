"""
handlers/ai_executor.py
Receives the structured JSON action dict from ai_brain.py and dispatches
to the right handler or performs the action directly.
"""
from __future__ import annotations

import os
import io
import glob
import subprocess
import time
import datetime

import pyautogui
from PIL import Image

try:
    import pyperclip
    HAS_CLIP = True
except ImportError:
    HAS_CLIP = False

from handlers.web_handler    import WebHandler
from handlers.system_handler import SystemHandler
from handlers.media_handler  import MediaHandler
from handlers.ocr_handler    import OCRHandler


class AIExecutor:
    """Execute structured action dicts returned by AIBrain."""

    def __init__(self, config=None):
        self._config = config
        self.web    = WebHandler()
        self.system = SystemHandler()
        self.media  = MediaHandler()
        self.ocr    = OCRHandler()

    def execute(self, action: dict, context) -> str:
        """
        Execute the action and return the spoken response string.
        Also persists any save_output data into context.
        """
        act    = action.get("action", "speak_only")
        params = action.get("params", {})
        speak  = action.get("speak", "")

        # Persist named outputs if AI flagged them
        save = action.get("save_output")
        if save and isinstance(save, dict):
            key = save.get("key")
            val = save.get("value")
            if key is not None:
                context.save_output(key, val)

        # Dispatch
        try:
            result = self._dispatch(act, params, context)
            # If the handler returned its own message, prefer that unless
            # Gemini already gave a richer speak line
            if result and not speak:
                speak = result
        except Exception as e:
            speak = f"Sorry sir, I ran into an issue: {e}"

        return speak or "Done, sir."

    # ── Dispatcher ───────────────────────────────────────────────────────────
    def _dispatch(self, act: str, params: dict, context) -> str:

        # ── open app ─────────────────────────────────────────────────────────
        if act == "open_app":
            name = params.get("name", "")
            resp, _ = self.system.handle(f"open {name}", context)
            return resp

        # ── close app ────────────────────────────────────────────────────────
        if act == "close_app":
            name = params.get("name", "")
            resp, _ = self.system.handle(f"close {name}", context)
            return resp

        # ── open website ─────────────────────────────────────────────────────
        if act == "open_website":
            url  = params.get("url", "")
            name = params.get("name", url)
            import webbrowser
            webbrowser.open(url)
            return f"Opening {name}, sir."

        # ── search web ───────────────────────────────────────────────────────
        if act == "search_web":
            term = params.get("term", "")
            import webbrowser
            url = f"https://www.google.com/search?q={term.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Searching for {term}, sir."

        # ── type text ────────────────────────────────────────────────────────
        if act == "type_text":
            text = params.get("text", "")
            time.sleep(0.3)
            pyautogui.write(text, interval=0.04)
            return f"Typed: {text}"

        # ── click at coordinates ──────────────────────────────────────────────
        if act == "click_at":
            x = int(params.get("x", 0))
            y = int(params.get("y", 0))
            pyautogui.click(x, y)
            return f"Clicked at ({x}, {y}), sir."

        # ── play youtube (search + play Nth result) ───────────────────────────
        if act == "play_youtube":
            query  = params.get("query", "")
            n      = int(params.get("n", 1))
            if query:
                import webbrowser, time as _t
                url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                webbrowser.open(url)
                _t.sleep(4)
            self.web._play_nth_video(n)
            ordinal = self.web._ordinal(n)
            return f"Playing the {ordinal} YouTube result for '{query}', sir." if query else f"Playing the {ordinal} video, sir."

        # ── youtube nth video (already on results page) ───────────────────────
        if act == "youtube_nth":
            n = int(params.get("n", 1))
            self.web._play_nth_video(n)
            return f"Playing the {self.web._ordinal(n)} video, sir."

        # ── find and click by label (OCR) ─────────────────────────────────────
        if act == "find_and_click":
            label = params.get("label", "")
            resp, _ = self.ocr.handle(f"click on {label}", context)
            return resp

        # ── screenshot ────────────────────────────────────────────────────────
        if act == "take_screenshot":
            return self._take_and_describe_screenshot(context)

        # ── system stats ──────────────────────────────────────────────────────
        if act == "system_stats":
            resp, _ = self.system.handle("system stats", context)
            return resp

        # ── open file ─────────────────────────────────────────────────────────
        if act == "open_file":
            path = params.get("path", "")
            if path and os.path.exists(path):
                os.startfile(path)
                return f"Opening {os.path.basename(path)}, sir."
            return f"File not found: {path}"

        # ── list files ────────────────────────────────────────────────────────
        if act == "list_files":
            directory = params.get("directory", os.path.expanduser("~"))
            pattern   = params.get("pattern", "*")
            full_pat  = os.path.join(directory, pattern)
            try:
                files = sorted(glob.glob(full_pat))
                names = [os.path.basename(f) for f in files]
                # Save full paths for follow-up ("open the first one")
                context.save_output("files_list",  files)
                context.save_output("files_names", names)
                if names:
                    listing = ", ".join(names[:10])
                    suffix  = f" and {len(names)-10} more" if len(names) > 10 else ""
                    return f"Found {len(names)} file(s): {listing}{suffix}."
                return "No files found matching that pattern."
            except Exception as e:
                return f"Could not list files: {e}"

        # ── key press ────────────────────────────────────────────────────────
        if act == "key_press":
            keys = params.get("keys", [])
            if isinstance(keys, str):
                keys = [keys]
            if len(keys) == 1:
                pyautogui.press(keys[0])
            else:
                pyautogui.hotkey(*keys)
            return f"Pressed {'+'.join(keys)}."

        # ── scroll ───────────────────────────────────────────────────────────
        if act == "scroll":
            direction = params.get("direction", "down")
            amount    = int(params.get("amount", 3))
            clicks    = amount if direction == "up" else -amount
            pyautogui.scroll(clicks)
            return f"Scrolled {direction}."

        # ── volume control ───────────────────────────────────────────────────
        if act == "volume_control":
            resp, _ = self.media.handle(
                f"volume {params.get('action', 'up')}", context
            )
            return resp

        # ── play music ───────────────────────────────────────────────────────
        if act == "play_music":
            query = params.get("query", "")
            resp, _ = self.media.handle(
                f"play {query}" if query else "play music", context
            )
            return resp

        # ── clipboard read ───────────────────────────────────────────────────
        if act == "clipboard_read":
            if HAS_CLIP:
                text = pyperclip.paste()
                context.save_output("clipboard", text)
                return f"Clipboard contains: {text[:120]}"
            return "Clipboard access not available."

        # ── clipboard write ──────────────────────────────────────────────────
        if act == "clipboard_write":
            text = params.get("text", "")
            if HAS_CLIP:
                pyperclip.copy(text)
                return "Copied to clipboard, sir."
            return "Clipboard access not available."

        # ── run shell command ────────────────────────────────────────────────
        if act == "run_shell":
            cmd = params.get("command", "")
            try:
                result = subprocess.check_output(
                    cmd, shell=True, timeout=15,
                    stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace"
                )
                # Save output so AI can reference it in next turn
                lines = [l.strip() for l in result.strip().splitlines() if l.strip()]
                context.save_output("shell_output", lines)
                context.save_output("files_list",   lines)   # often file listings
                context.save_output("files_names",  [os.path.basename(l) for l in lines])
                preview = "\n".join(lines[:8])
                if len(lines) > 8:
                    preview += f"\n... and {len(lines)-8} more lines"
                return preview or "Command executed with no output."
            except subprocess.TimeoutExpired:
                return "Command timed out."
            except subprocess.CalledProcessError as e:
                out = (e.output or "").strip()
                return out[:300] if out else f"Command failed (exit {e.returncode})."
            except Exception as e:
                return f"Shell error: {e}"

        # ── speak only ───────────────────────────────────────────────────────
        if act == "speak_only":
            return ""   # speak text is already in action["speak"]

        return f"Unknown action: {act}"

    # ── Screenshot + Vision description ──────────────────────────────────────
    def _take_and_describe_screenshot(self, context) -> str:
        """Capture the screen, save it, attach to context for the AI to describe."""
        try:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            screenshots_dir = os.path.join(base_dir, "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            path = os.path.join(screenshots_dir, f"jarvis_{ts}.png")

            screenshot = pyautogui.screenshot()
            # Resize to reasonable size for vision
            w, h = screenshot.size
            if w > 1280:
                scale = 1280 / w
                screenshot = screenshot.resize((1280, int(h * scale)), Image.LANCZOS)
            screenshot.save(path)

            # Store the raw bytes in context so AI brain can attach on next call
            buf = io.BytesIO()
            screenshot.save(buf, format="PNG")
            context.save_output("last_screenshot_path", path)
            context.save_output("last_screenshot_bytes", buf.getvalue().hex())

            return f"Screenshot taken and saved. I can now see your screen — ask me what you'd like to know about it."
        except Exception as e:
            return f"Screenshot failed: {e}"
