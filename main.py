"""
main.py — JARVIS AI Desktop Assistant entry point
"""
import sys
import os

# Add project root to path so sub-packages resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.main_window import MainWindow


def main():
    # High-DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)

    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    app.setStyle("Fusion")

    # Global font
    app.setFont(QFont("Segoe UI", 10))

    # Dark fusion palette for any standard widgets
    app.setStyleSheet("""
        QToolTip {
            background: #1a1a2e;
            color: #00f5ff;
            border: 1px solid rgba(0,245,255,100);
            font-family: 'Segoe UI';
        }
        QMessageBox { background: #0d0d1a; color: #e0e0ff; }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
