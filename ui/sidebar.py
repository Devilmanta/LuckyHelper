"""
LuckyHelper - Sidebar Widget
Left navigation panel with balance display and menu items.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QLineEdit, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from database import db_manager


# ── Balance Widget ─────────────────────────────────────────────────────────────

class BalanceWidget(QWidget):
    """
    Compact balance + risk display panel for the sidebar.
    Shows current balance, allows inline editing, and
    displays 1%, 2%, 3% risk amounts.
    """

    _CARD_STYLE = """
        QWidget#BalanceCard {
            background-color: #1C2128;
            border: 1px solid #21262D;
            border-radius: 10px;
        }
    """
    _EDIT_BTN = """
        QPushButton {
            background-color: transparent; color: #00D4FF;
            border: none; font-size: 11px; font-weight: 600;
            padding: 2px 6px;
        }
        QPushButton:hover { color: #33DDFF; }
    """
    _SAVE_BTN = """
        QPushButton {
            background-color: #00C853; color: #0D1117;
            border: none; border-radius: 5px;
            font-size: 11px; font-weight: 700; padding: 3px 8px;
        }
        QPushButton:hover { background-color: #00E676; }
    """
    _INPUT_STYLE = """
        QLineEdit {
            background-color: #0D1117; color: #E6EDF3;
            border: 1px solid #00D4FF; border-radius: 5px;
            padding: 3px 6px; font-size: 12px;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(self._CARD_STYLE)
        self._editing = False
        self._build_ui()
        self._load_balance()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(6)

        # ── Header row ────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        bal_icon = QLabel("💰")
        bal_icon.setStyleSheet("font-size: 13px; background: transparent;")
        bal_lbl = QLabel("Bakiye")
        bal_lbl.setStyleSheet("color: #8B949E; font-size: 11px; font-weight: 600; background: transparent;")
        hdr.addWidget(bal_icon)
        hdr.addWidget(bal_lbl)
        hdr.addStretch()
        self.edit_btn = QPushButton("Düzenle")
        self.edit_btn.setStyleSheet(self._EDIT_BTN)
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.clicked.connect(self._toggle_edit)
        hdr.addWidget(self.edit_btn)
        outer.addLayout(hdr)

        # ── Balance display ───────────────────────────────────
        self.balance_display = QLabel("$0.00")
        self.balance_display.setStyleSheet(
            "color: #E6EDF3; font-size: 17px; font-weight: 800; background: transparent;"
        )
        outer.addWidget(self.balance_display)

        self.starting_balance_lbl = QLabel("Başlangıç: $0.00")
        self.starting_balance_lbl.setStyleSheet(
            "color: #8B949E; font-size: 10px; background: transparent;"
        )
        outer.addWidget(self.starting_balance_lbl)

        # ── Edit row (hidden by default) ──────────────────────
        self.edit_row = QWidget()
        self.edit_row.setStyleSheet("background: transparent;")
        edit_layout = QHBoxLayout(self.edit_row)
        edit_layout.setContentsMargins(0, 0, 0, 0)
        edit_layout.setSpacing(4)

        self.balance_input = QLineEdit()
        self.balance_input.setPlaceholderText("örn. 10000")
        self.balance_input.setStyleSheet(self._INPUT_STYLE)
        self.balance_input.setFixedHeight(26)
        self.balance_input.returnPressed.connect(self._save_balance)

        save_btn = QPushButton("✓")
        save_btn.setFixedSize(26, 26)
        save_btn.setStyleSheet(self._SAVE_BTN)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_balance)

        edit_layout.addWidget(self.balance_input)
        edit_layout.addWidget(save_btn)
        self.edit_row.hide()
        outer.addWidget(self.edit_row)

        # ── Risk amounts ──────────────────────────────────────
        risk_row = QHBoxLayout()
        risk_row.setContentsMargins(0, 2, 0, 0)
        risk_row.setSpacing(0)

        self.risk1_lbl = self._risk_item("%1", "#8B949E")
        self.risk2_lbl = self._risk_item("%2", "#F0A500")
        self.risk3_lbl = self._risk_item("%3", "#FF7043")

        risk_row.addWidget(self.risk1_lbl)
        risk_row.addWidget(self.risk2_lbl)
        risk_row.addWidget(self.risk3_lbl)
        outer.addLayout(risk_row)

    def _risk_item(self, pct_label: str, color: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        ly = QVBoxLayout(w)
        ly.setContentsMargins(0, 0, 6, 0)
        ly.setSpacing(1)
        lbl = QLabel(pct_label)
        lbl.setStyleSheet(f"color: #484F58; font-size: 9px; background: transparent;")
        val = QLabel("$0")
        val.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 700; background: transparent;")
        ly.addWidget(lbl)
        ly.addWidget(val)
        w._val = val   # type: ignore
        w._color = color  # type: ignore
        return w

    def _load_balance(self):
        starting_bal_str = db_manager.get_setting("balance", "0")
        try:
            starting_bal = float(starting_bal_str)
        except ValueError:
            starting_bal = 0.0

        # Calculate current balance
        stats = db_manager.get_overall_stats()
        total_pnl = stats.get("total_pnl", 0.0) or 0.0
        current_bal = starting_bal + total_pnl

        self._update_display(starting_bal, current_bal)

    def _update_display(self, starting_bal: float, current_bal: float):
        self.balance_display.setText(f"${current_bal:,.2f}")
        self.starting_balance_lbl.setText(f"Başlangıç: ${starting_bal:,.2f}")
        self.risk1_lbl._val.setText(f"${current_bal * 0.01:,.2f}")   # type: ignore
        self.risk2_lbl._val.setText(f"${current_bal * 0.02:,.2f}")   # type: ignore
        self.risk3_lbl._val.setText(f"${current_bal * 0.03:,.2f}")   # type: ignore

    def _toggle_edit(self):
        self._editing = not self._editing
        self.edit_row.setVisible(self._editing)
        if self._editing:
            balance_str = db_manager.get_setting("balance", "0")
            self.balance_input.setText(balance_str)
            self.balance_input.setFocus()
            self.edit_btn.setText("İptal")
        else:
            self.edit_btn.setText("Düzenle")

    def _save_balance(self):
        text = self.balance_input.text().strip().replace(",", "").replace("$", "")
        try:
            starting_bal = float(text)
            if starting_bal < 0:
                starting_bal = 0.0
        except ValueError:
            starting_bal = 0.0
        db_manager.set_setting("balance", str(starting_bal))
        
        # Calculate current balance
        stats = db_manager.get_overall_stats()
        total_pnl = stats.get("total_pnl", 0.0) or 0.0
        current_bal = starting_bal + total_pnl

        self._update_display(starting_bal, current_bal)
        self._editing = False
        self.edit_row.hide()
        self.edit_btn.setText("Düzenle")


# ── Sidebar Button ─────────────────────────────────────────────────────────────

class SidebarButton(QPushButton):
    """Custom sidebar navigation button."""

    def __init__(self, icon_char: str, label: str, parent=None):
        super().__init__(parent)
        self.setText(f"  {icon_char}   {label}")
        self.setObjectName("SidebarBtn")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)
        self.setCheckable(False)
        self._active = False

    def set_active(self, active: bool):
        self._active = active
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


# ── Sidebar ────────────────────────────────────────────────────────────────────

class Sidebar(QWidget):
    """Left sidebar navigation panel."""

    page_changed = pyqtSignal(str)  # emits page name

    PAGES = [
        ("📅", "Takvim", "calendar"),
        ("📊", "İstatistikler", "stats"),
        ("⚡", "Risk Hesaplayıcı", "risk"),
        ("⚖️", "Ortalama Maliyet", "avg_cost"),
        ("🏆", "Winrate Hesaplayıcı", "winrate"),
        ("⚙️", "Ayarlar", "settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)
        self._buttons: dict[str, SidebarButton] = {}
        self._current_page = "calendar"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Logo area ──────────────────────────────────────────
        logo_label = QLabel("LuckyHelper")
        logo_label.setObjectName("SidebarLogo")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        sub_label = QLabel("Trading Journal")
        sub_label.setObjectName("SidebarSubtitle")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(logo_label)
        layout.addWidget(sub_label)

        # ── Divider ────────────────────────────────────────────
        divider = QFrame()
        divider.setObjectName("SidebarDivider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        # ── Balance widget ─────────────────────────────────────
        bal_wrapper = QWidget()
        bal_wrapper.setStyleSheet("background: transparent;")
        bal_layout = QVBoxLayout(bal_wrapper)
        bal_layout.setContentsMargins(12, 12, 12, 4)
        self.balance_widget = BalanceWidget()
        self.balance_widget.setObjectName("BalanceCard")
        bal_layout.addWidget(self.balance_widget)
        layout.addWidget(bal_wrapper)

        # ── Divider 2 ──────────────────────────────────────────
        divider2 = QFrame()
        divider2.setObjectName("SidebarDivider")
        divider2.setFixedHeight(1)
        layout.addWidget(divider2)

        # ── Nav label ──────────────────────────────────────────
        nav_label = QLabel("MENÜ")
        nav_label.setObjectName("SidebarNavLabel")
        layout.addWidget(nav_label)

        # ── Nav buttons ────────────────────────────────────────
        for icon, label, page_id in self.PAGES:
            btn = SidebarButton(icon, label)
            btn.clicked.connect(lambda checked, p=page_id: self._on_page_click(p))
            self._buttons[page_id] = btn
            layout.addWidget(btn)

        # ── Spacer ─────────────────────────────────────────────
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(spacer)

        # ── Footer ─────────────────────────────────────────────
        footer = QLabel("v1.0.0  •  LuckyHelper")
        footer.setObjectName("SidebarFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        # Activate default page
        self._set_active_button("calendar")

    def _on_page_click(self, page_id: str):
        self._set_active_button(page_id)
        self.page_changed.emit(page_id)

    def _set_active_button(self, page_id: str):
        for pid, btn in self._buttons.items():
            btn.set_active(pid == page_id)
        self._current_page = page_id

    def refresh_balance(self):
        self.balance_widget._load_balance()

