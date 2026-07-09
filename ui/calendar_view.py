"""
LuckyHelper - Calendar View
Custom monthly calendar with PnL-colored day cells.
"""

import calendar
from datetime import date, datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QCursor

from database import db_manager
from ui.trade_dialog import DayDetailDialog
from ui.styles import COLOR_PROFIT, COLOR_LOSS, COLOR_ACCENT


WEEKDAYS_TR = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]

TURKISH_MONTHS = [
    "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
]


class DayCell(QWidget):
    """
    Represents a single day in the calendar grid.
    Shows day number, PnL amount (if any trades exist),
    and trade count badge.
    """

    clicked = pyqtSignal(str)  # emits 'YYYY-MM-DD'

    def __init__(self, parent=None):
        super().__init__(parent)
        self._date_str: str | None = None
        self._is_current_month = True
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 6)
        layout.setSpacing(2)

        # Day number row
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        self.day_lbl = QLabel("0")
        self.day_lbl.setObjectName("DayNumber")
        self.day_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        top_row.addWidget(self.day_lbl)
        top_row.addStretch()

        self.badge_lbl = QLabel("")
        self.badge_lbl.setStyleSheet(
            "background-color: #00D4FF; color: #0D1117; border-radius: 8px;"
            "font-size: 10px; font-weight: 700; padding: 1px 5px;"
        )
        self.badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_lbl.hide()
        top_row.addWidget(self.badge_lbl)

        layout.addLayout(top_row)
        layout.addStretch()

        # PnL label centered at bottom
        self.pnl_lbl = QLabel("")
        self.pnl_lbl.setObjectName("DayPnlLabel")
        self.pnl_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.pnl_lbl)

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumSize(90, 80)

    def set_empty(self):
        """Mark cell as empty (padding cell)."""
        self._date_str = None
        self._is_current_month = False
        self.setProperty("is_empty", "true")
        self.setProperty("pnl_state", "neutral")
        self.setProperty("is_today", "false")
        self._apply_style()
        self.day_lbl.setText("")
        self.pnl_lbl.setText("")
        self.badge_lbl.hide()
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def set_day(self, date_str: str, day_num: int, is_today: bool,
                is_current_month: bool, pnl: float | None, trade_count: int):
        """Configure the cell for a specific date."""
        self._date_str = date_str
        self._is_current_month = is_current_month

        self.day_lbl.setText(str(day_num))

        self.setProperty("is_empty", "false")
        self.setProperty("is_today", "true" if is_today else "false")

        if not is_current_month:
            self.day_lbl.setObjectName("DayNumberOtherMonth")
            self.setProperty("pnl_state", "neutral")
        else:
            if is_today:
                self.day_lbl.setObjectName("DayNumberToday")
            else:
                self.day_lbl.setObjectName("DayNumber")

            if pnl is not None and pnl > 0:
                self.setProperty("pnl_state", "profit")
            elif pnl is not None and pnl < 0:
                self.setProperty("pnl_state", "loss")
            else:
                self.setProperty("pnl_state", "neutral")

        self._apply_style()

        # PnL text
        if pnl is not None and trade_count > 0:
            sign = "+" if pnl >= 0 else ""
            self.pnl_lbl.setText(f"${sign}{pnl:,.2f}")
            color = COLOR_PROFIT if pnl >= 0 else COLOR_LOSS
            self.pnl_lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {color};")
        else:
            self.pnl_lbl.setText("")

        # Badge
        if trade_count > 0:
            self.badge_lbl.setText(str(trade_count))
            self.badge_lbl.show()
        else:
            self.badge_lbl.hide()

        # Tooltip
        if trade_count > 0 and pnl is not None:
            sign = "+" if pnl >= 0 else ""
            self.setToolTip(f"{date_str}\n{trade_count} işlem  |  PnL: ${sign}{pnl:,.2f}")
        else:
            self.setToolTip(date_str if date_str else "")

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def _apply_style(self):
        self.style().unpolish(self)
        self.style().polish(self)
        self.day_lbl.style().unpolish(self.day_lbl)
        self.day_lbl.style().polish(self.day_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._date_str:
            self.clicked.emit(self._date_str)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        from PyQt6.QtWidgets import QStyleOption, QStyle
        from PyQt6.QtGui import QPainter
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)


class CalendarView(QWidget):
    """
    Full monthly calendar widget with navigation,
    summary bar, and day cells.
    """

    trades_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentArea")

        today = date.today()
        self._year  = today.year
        self._month = today.month
        self._today = today

        self._cells: list[DayCell] = []
        self._build_ui()
        self.refresh()

    # ──────────────────────────────────────────────────────────
    #  UI BUILD
    # ──────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("CalendarHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(32, 24, 32, 16)
        h_layout.setSpacing(12)

        # Title block
        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        self.title_lbl = QLabel("")
        self.title_lbl.setObjectName("CalendarTitle")
        self.sub_lbl = QLabel("Günlere tıklayarak işlemlerinizi ekleyin ve düzenleyin.")
        self.sub_lbl.setObjectName("CalendarSubtitle")
        title_block.addWidget(self.title_lbl)
        title_block.addWidget(self.sub_lbl)

        h_layout.addLayout(title_block)
        h_layout.addStretch()

        # Today button
        today_btn = QPushButton("Bugün")
        today_btn.setObjectName("TodayBtn")
        today_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        today_btn.clicked.connect(self._go_today)
        h_layout.addWidget(today_btn)

        # Nav buttons
        self.prev_btn = QPushButton("‹")
        self.prev_btn.setObjectName("NavBtn")
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self._prev_month)

        self.next_btn = QPushButton("›")
        self.next_btn.setObjectName("NavBtn")
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.clicked.connect(self._next_month)

        h_layout.addWidget(self.prev_btn)
        h_layout.addWidget(self.next_btn)

        root.addWidget(header)

        # ── Day-of-week headers ────────────────────────────────
        dow_widget = QWidget()
        dow_widget.setStyleSheet("background-color: #0D1117; padding: 0 32px;")
        dow_layout = QHBoxLayout(dow_widget)
        dow_layout.setContentsMargins(32, 0, 32, 0)
        dow_layout.setSpacing(6)

        for day in WEEKDAYS_TR:
            lbl = QLabel(day)
            lbl.setObjectName("DayHeader")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            dow_layout.addWidget(lbl)

        root.addWidget(dow_widget)

        # ── Grid ──────────────────────────────────────────────
        grid_wrapper = QWidget()
        grid_wrapper.setStyleSheet("background-color: #0D1117;")
        self.grid_layout = QGridLayout(grid_wrapper)
        self.grid_layout.setContentsMargins(32, 8, 32, 8)
        self.grid_layout.setSpacing(6)

        # Pre-create 6 rows × 7 cols of cells
        for row in range(6):
            for col in range(7):
                cell = DayCell()
                cell.clicked.connect(self._on_day_clicked)
                self.grid_layout.addWidget(cell, row, col)
                self._cells.append(cell)

        root.addWidget(grid_wrapper, 1)

        # ── Summary bar ───────────────────────────────────────
        self.summary_bar = QWidget()
        self.summary_bar.setObjectName("SummaryBar")
        sb_layout = QHBoxLayout(self.summary_bar)
        sb_layout.setContentsMargins(32, 12, 32, 12)
        sb_layout.setSpacing(32)

        self.sum_pnl_lbl      = self._summary_item("Aylık PnL",       "$0.00")
        self.sum_trades_lbl   = self._summary_item("Toplam İşlem",     "0")
        self.sum_days_lbl     = self._summary_item("Aktif Gün",        "0")
        self.sum_windays_lbl  = self._summary_item("Kazanan Gün",      "0")
        self.sum_lossdays_lbl = self._summary_item("Kaybeden Gün",     "0")
        self.sum_winrate_lbl  = self._summary_item("Günlük Win Rate",  "0%")

        for w in [self.sum_pnl_lbl, self.sum_trades_lbl, self.sum_days_lbl,
                  self.sum_windays_lbl, self.sum_lossdays_lbl, self.sum_winrate_lbl]:
            sb_layout.addWidget(w)
        sb_layout.addStretch()

        root.addWidget(self.summary_bar)

    def _summary_item(self, label: str, value: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        ly = QVBoxLayout(w)
        ly.setContentsMargins(0, 0, 0, 0)
        ly.setSpacing(2)
        lbl = QLabel(label)
        lbl.setObjectName("SummaryItem")
        val = QLabel(value)
        val.setObjectName("SummaryValue")
        ly.addWidget(lbl)
        ly.addWidget(val)
        w._val = val  # type: ignore
        return w

    # ──────────────────────────────────────────────────────────
    #  REFRESH / DATA
    # ──────────────────────────────────────────────────────────

    def refresh(self):
        """Reload data from DB and repaint calendar."""
        self.title_lbl.setText(f"{TURKISH_MONTHS[self._month]} {self._year}")
        monthly = db_manager.get_monthly_summary(self._year, self._month)
        self._repaint_cells(monthly)
        self._update_summary(monthly)

    def _repaint_cells(self, monthly: dict[str, dict]):
        # calendar.monthcalendar → list of weeks (Mon=0 .. Sun=6)
        weeks = calendar.monthcalendar(self._year, self._month)

        idx = 0
        for week in weeks:
            for day_num in week:
                cell = self._cells[idx]
                if day_num == 0:
                    cell.set_empty()
                else:
                    date_str = f"{self._year}-{self._month:02d}-{day_num:02d}"
                    is_today = (
                        self._today.year  == self._year and
                        self._today.month == self._month and
                        self._today.day   == day_num
                    )
                    day_data = monthly.get(date_str)
                    pnl = day_data["total_pnl"] if day_data else None
                    trade_count = day_data["trade_count"] if day_data else 0
                    cell.set_day(date_str, day_num, is_today, True, pnl, trade_count)
                idx += 1

        # Hide remaining rows if month < 6 weeks
        for i in range(idx, len(self._cells)):
            self._cells[i].set_empty()

    def _update_summary(self, monthly: dict[str, dict]):
        total_pnl  = sum(d["total_pnl"] for d in monthly.values())
        active_days = len(monthly)
        win_days   = sum(1 for d in monthly.values() if d["total_pnl"] > 0)
        loss_days  = sum(1 for d in monthly.values() if d["total_pnl"] < 0)
        winrate    = (win_days / active_days * 100) if active_days > 0 else 0

        # Fetch total trade count for the month
        total_trades = sum(d["trade_count"] for d in monthly.values())

        pnl_color = "#00C853" if total_pnl > 0 else ("#FF3D57" if total_pnl < 0 else "#E6EDF3")
        sign = "+" if total_pnl >= 0 else ""

        self.sum_pnl_lbl._val.setText(f"${sign}{total_pnl:,.2f}")          # type: ignore
        self.sum_pnl_lbl._val.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {pnl_color};")  # type: ignore

        self.sum_trades_lbl._val.setText(str(total_trades))                  # type: ignore
        self.sum_days_lbl._val.setText(str(active_days))                     # type: ignore
        self.sum_windays_lbl._val.setText(str(win_days))                     # type: ignore
        self.sum_lossdays_lbl._val.setText(str(loss_days))                   # type: ignore
        self.sum_winrate_lbl._val.setText(f"{winrate:.0f}%")                 # type: ignore

    def _get_monthly_trade_count(self) -> int:
        import sqlite3
        from database.db_manager import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM trades WHERE date LIKE ?",
            (f"{self._year}-{self._month:02d}-%",)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count

    # ──────────────────────────────────────────────────────────
    #  NAVIGATION
    # ──────────────────────────────────────────────────────────

    def _prev_month(self):
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        self.refresh()

    def _next_month(self):
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        self.refresh()

    def _go_today(self):
        today = date.today()
        self._year  = today.year
        self._month = today.month
        self.refresh()

    # ──────────────────────────────────────────────────────────
    #  DAY CLICK
    # ──────────────────────────────────────────────────────────

    def _on_day_clicked(self, date_str: str):
        dlg = DayDetailDialog(date_str, parent=self)
        dlg.trades_changed.connect(self.refresh)
        dlg.trades_changed.connect(self.trades_changed.emit)
        dlg.exec()
