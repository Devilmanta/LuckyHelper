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

    # ── Global dark stylesheet ─────────────────────────────────
    app.setStyleSheet(MAIN_STYLE)

    # ── Default font ──────────────────────────────────────────
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # ── Initialize database ───────────────────────────────────
    db_manager.initialize_db()

    # ── Launch window ─────────────────────────────────────────
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
