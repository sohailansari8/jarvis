"""
handlers/ocr_handler.py
Uses pytesseract to find text on-screen and click it.
Gracefully disabled if Tesseract binary is not installed.
"""
import pyautogui

try:
    import pytesseract
    from pytesseract import Output
    from PIL import Image
    # Try to locate tesseract binary
    import subprocess, shutil
    _tess = shutil.which('tesseract') or r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    import os
    if os.path.exists(_tess):
        pytesseract.pytesseract.tesseract_cmd = _tess
        HAS_OCR = True
    else:
        HAS_OCR = False
except ImportError:
    HAS_OCR = False


class OCRHandler:
    """Find text on screen using OCR and click it."""

    def handle(self, query: str, context) -> tuple[str, bool]:
        if not HAS_OCR:
            return "OCR is not available — please install Tesseract.", True

        target = self._extract_target(query)
        if not target:
            return "Please tell me what text to find on screen.", True

        return self._find_and_click(target)

    # ── Helpers ──────────────────────────────────────────────
    def _extract_target(self, query: str) -> str:
        for prefix in ['click on ', 'click ', 'find and click ',
                       'find ', 'press ', 'tap ']:
            if query.startswith(prefix):
                return query[len(prefix):].strip()
        return ''

    def _find_and_click(self, target: str) -> tuple[str, bool]:
        try:
            screenshot = pyautogui.screenshot()
            data = pytesseract.image_to_data(
                screenshot, output_type=Output.DICT, lang='eng'
            )

            target_lower = target.lower()
            best_x, best_y, best_conf = None, None, 0

            for i, text in enumerate(data['text']):
                if not text.strip():
                    continue
                conf = int(data['conf'][i])
                if conf < 50:
                    continue
                if target_lower in text.lower():
                    if conf > best_conf:
                        x = data['left'][i] + data['width'][i]  // 2
                        y = data['top'][i]  + data['height'][i] // 2
                        best_x, best_y, best_conf = x, y, conf

            if best_x is not None:
                pyautogui.click(best_x, best_y)
                return f"Clicked on '{target}', sir.", True
            else:
                return f"Could not find '{target}' on screen.", True

        except Exception as e:
            return f"OCR error: {e}", True

    @staticmethod
    def is_available() -> bool:
        return HAS_OCR
