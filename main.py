"""
LuckyHelper - Application Entry Point
Futures Day Trading Journal
"""

import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import db_manager
from ui.main_window import MainWindow
from ui.styles import MAIN_STYLE


def main():
    # ── High-DPI support ──────────────────────────────────────
    # PyQt6 enables HiDPI by default; no explicit call needed.

    app = QApplication(sys.argv)
    app.setApplicationName("LuckyHelper")
    app.setApplicationDisplayName("LuckyHelper")
    app.setOrganizationName("LuckyHelper")

    # ── Set window icon & taskbar grouping on Windows ─────────
    # We load the icon from the assets folder relative to main.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "assets", "icon.png")
    if os.path.exists(icon_path):
        from PyQt6.QtGui import QIcon
        app.setWindowIcon(QIcon(icon_path))

    # Set AppUserModelID to ensure Windows taskbar doesn't fallback to python icon
    if os.name == "nt":
        try:
            import ctypes
            myappid = "Devilmanta.LuckyHelper.TradingJournal.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    # ── Global dark stylesheet ─────────────────────────────────
    app.setStyleSheet(MAIN_STYLE)

    # ── Default font ──────────────────────────────────────────
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # ── Initialize database ───────────────────────────────────
    db_manager.initialize_db()

    # ── Launch window ─────────────────────────────────────────
    window = MainWindow()
    window.setWindowIcon(QIcon(icon_path))
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
