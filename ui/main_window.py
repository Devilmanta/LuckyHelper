"""
LuckyHelper - Main Window
Hosts the sidebar and the content stack.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QLabel, QVBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ui.sidebar import Sidebar
from ui.calendar_view import CalendarView
from ui.risk_calculator import RiskCalculator
from ui.avg_cost_calculator import AvgCostCalculator
from ui.winrate_calculator import WinrateCalculator
from ui.statistics_view import StatisticsView
from ui.settings_view import SettingsView


class ComingSoonPage(QWidget):
    """Placeholder page for features not yet implemented."""

    def __init__(self, title: str, icon: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 56px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #E6EDF3; font-size: 22px; font-weight: 700;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub_lbl = QLabel("Bu özellik yakında eklenecek.")
        sub_lbl.setStyleSheet("color: #8B949E; font-size: 14px;")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        badge = QLabel("🚀  Çok Yakında")
        badge.setStyleSheet(
            "background-color: rgba(0,212,255,0.12); color: #00D4FF;"
            "border: 1px solid #00D4FF; border-radius: 20px;"
            "font-size: 12px; font-weight: 600; padding: 6px 18px;"
        )
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)
        layout.addSpacing(16)
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LuckyHelper  •  Futures Trading Journal")
        self.setMinimumSize(1280, 800)
        self.resize(1440, 900)

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._switch_page)
        root_layout.addWidget(self.sidebar)

        # Content stack
        self.stack = QStackedWidget()
        self.stack.setObjectName("ContentArea")
        root_layout.addWidget(self.stack, 1)

        # Pages
        self.calendar_page = CalendarView()
        self.calendar_page.trades_changed.connect(self.sidebar.refresh_balance)
        self.stack.addWidget(self.calendar_page)                       # index 0

        self.stats_page    = StatisticsView()
        self.calendar_page.trades_changed.connect(self.stats_page.refresh)
        self.stack.addWidget(self.stats_page)                          # index 1

        self.risk_page     = RiskCalculator()
        self.stack.addWidget(self.risk_page)                           # index 2

        self.avg_cost_page = AvgCostCalculator()
        self.stack.addWidget(self.avg_cost_page)                       # index 3

        self.winrate_page = WinrateCalculator()
        self.stack.addWidget(self.winrate_page)                        # index 4

        self.settings_page = SettingsView()
        self.settings_page.settings_changed.connect(self.sidebar.refresh_balance)
        self.stack.addWidget(self.settings_page)                       # index 5

        self._page_index = {
            "calendar": 0,
            "stats":    1,
            "risk":     2,
            "avg_cost": 3,
            "winrate":  4,
            "settings": 5,
        }

        self.stack.setCurrentIndex(0)

    def _switch_page(self, page_id: str):
        if page_id == "risk":
            self.risk_page.update_balance()
        idx = self._page_index.get(page_id, 0)
        self.stack.setCurrentIndex(idx)
