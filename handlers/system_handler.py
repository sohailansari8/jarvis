"""
handlers/system_handler.py
App open/close, system stats, screenshots, typing, clipboard.
"""
import os
import pyautogui
import psutil
import datetime
import time

try:
    import pyperclip
    HAS_CLIP = True
except ImportError:
    HAS_CLIP = False


APP_KILL_MAP = {
    'notepad':     'notepad.exe',
    'chrome':      'chrome.exe',
    'edge':        'msedge.exe',
    'firefox':     'firefox.exe',
    'whatsapp':    'whatsapp.exe',
    'code':        'code.exe',
    'vscode':      'code.exe',
    'calculator':  'calculator.exe',
    'word':        'winword.exe',
    'excel':       'excel.exe',
    'spotify':     'spotify.exe',
    'vlc':         'vlc.exe',
    'discord':     'discord.exe',
    'slack':       'slack.exe',
    'paint':       'mspaint.exe',
}


class SystemHandler:
    def handle(self, query: str, context) -> tuple[str, bool]:
        # ── Open / Start app ────────────────────────────────
        if query.startswith('open ') or query.startswith('start '):
            return self._open_app(query)

        # ── Close app ────────────────────────────────────────
        if 'close ' in query or 'kill ' in query:
            return self._close_app(query)

        # ── System stats ─────────────────────────────────────
        if any(w in query for w in ['system stats', 'cpu', 'battery', 'ram', 'memory']):
            return self._system_stats()

        # ── Screenshot ───────────────────────────────────────
        if 'screenshot' in query or 'screen shot' in query:
            return self._take_screenshot()

        # ── Type text ────────────────────────────────────────
        if query.startswith('type '):
            text = query[5:].strip()
            pyautogui.typewrite(text, interval=0.05)
            return f"Typed: {text}", True

        # ── Clipboard ────────────────────────────────────────
        if 'copy' in query and HAS_CLIP:
            pyautogui.hotkey('ctrl', 'c')
            return "Copied selection to clipboard.", True
        if 'paste' in query and HAS_CLIP:
            pyautogui.hotkey('ctrl', 'v')
            return "Pasted from clipboard.", True

        # ── Window controls ──────────────────────────────────
        if 'minimize' in query:
            pyautogui.hotkey('win', 'down')
            return "Window minimized.", True
        if 'maximize' in query:
            pyautogui.hotkey('win', 'up')
            return "Window maximized.", True
        if 'switch window' in query or 'alt tab' in query:
            pyautogui.hotkey('alt', 'tab')
            return "Switching window.", True
        if 'show desktop' in query:
            pyautogui.hotkey('win', 'd')
            return "Showing desktop.", True
        if 'lock' in query and 'screen' in query:
            pyautogui.hotkey('win', 'l')
            return "Screen locked.", True

        return "", False

    # ── Helpers ──────────────────────────────────────────────
    def _open_app(self, query: str) -> tuple[str, bool]:
        # Strip leading verbs
        name = query.replace('open ', '').replace('start ', '').strip()
        # Known quick-launch shortcuts
        shortcuts = {
            'calculator': 'start calc',
            'notepad':    'start notepad',
            'paint':      'start mspaint',
            'chrome':     'start chrome',
            'edge':       'start msedge',
            'firefox':    'start firefox',
            'word':       'start winword',
            'excel':      'start excel',
        }
        for key, cmd in shortcuts.items():
            if key in name:
                os.system(cmd)
                return f"Opening {key}, sir.", True

        # Generic: Win + search
        pyautogui.press('super')
        time.sleep(0.5)
        pyautogui.typewrite(name, interval=0.05)
        time.sleep(0.8)
        pyautogui.press('enter')
        return f"Opening {name}, sir.", True

    def _close_app(self, query: str) -> tuple[str, bool]:
        name = query.replace('close ', '').replace('kill ', '').strip()
        exe = APP_KILL_MAP.get(name.lower())
        if exe:
            os.system(f'taskkill /f /im {exe}')
        else:
            os.system(f'taskkill /f /im {name}.exe')
        return f"Closing {name}, sir.", True

    def _system_stats(self) -> tuple[str, bool]:
        cpu  = psutil.cpu_percent(interval=0.5)
        ram  = psutil.virtual_memory()
        bat  = psutil.sensors_battery()
        msg  = f"CPU is at {cpu:.0f} percent. RAM usage is {ram.percent:.0f} percent."
        if bat:
            status = "charging" if bat.power_plugged else "on battery"
            msg += f" Battery is at {bat.percent:.0f} percent and {status}."
        return msg, True

    def _take_screenshot(self) -> tuple[str, bool]:
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, "screenshots", f"jarvis_{ts}.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pyautogui.screenshot(path)
        return f"Screenshot saved to JARVIS screenshots folder.", True
