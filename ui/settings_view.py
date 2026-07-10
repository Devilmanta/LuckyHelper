"""
LuckyHelper - Settings View
Industry-standard settings panel with tabbed navigation,
toggle switches, instant persistence, and restore defaults.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QScrollArea, QSizePolicy,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox,
    QDialog, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QSize
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush

from database import db_manager


# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULTS = {
    "balance":               "0",
    "risk_pct_1":            "1",
    "risk_pct_2":            "2",
    "risk_pct_3":            "3",
    "default_leverage":      "10",
    "calendar_week_start":   "monday",
    "currency_symbol":       "$",
    "start_page":            "calendar",
    "show_pnl_in_calendar":  "true",
    "stats_chart_type":      "bar",
    "risk_warning_threshold": "3",
}


# ── Toggle Switch ──────────────────────────────────────────────────────────────

class ToggleSwitch(QWidget):
    """Animated on/off toggle switch."""

    toggled = pyqtSignal(bool)

    _W, _H = 46, 24
    _KNOB  = 18
    _PAD   = 3

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedSize(self._W, self._H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = checked
        self._knob_x  = self._W - self._KNOB - self._PAD if checked else self._PAD

    # ── public API
    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, val: bool, emit: bool = False):
        self._checked = val
        self._knob_x  = self._W - self._KNOB - self._PAD if val else self._PAD
        self.update()
        if emit:
            self.toggled.emit(val)

    # ── events
    def mousePressEvent(self, _event):
        self._checked = not self._checked
        target_x = self._W - self._KNOB - self._PAD if self._checked else self._PAD

        self._anim = QPropertyAnimation(self, b"")
        # Manual animation via QTimer for knob_x
        self._animate_knob(self._knob_x, target_x)

    def _animate_knob(self, start: int, end: int):
        steps = 8
        delta = (end - start) / steps
        count = [0]

        def tick():
            count[0] += 1
            self._knob_x = int(start + delta * count[0])
            self.update()
            if count[0] >= steps:
                self._knob_x = end
                self.update()
                self.toggled.emit(self._checked)
            else:
                QTimer.singleShot(15, tick)

        QTimer.singleShot(0, tick)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track
        track_color = QColor("#00D4FF") if self._checked else QColor("#30363D")
        p.setBrush(QBrush(track_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, self._W, self._H, self._H / 2, self._H / 2)

        # Knob
        knob_y = (self._H - self._KNOB) // 2
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.drawEllipse(self._knob_x, knob_y, self._KNOB, self._KNOB)
        p.end()


# ── Setting Row ────────────────────────────────────────────────────────────────

class SettingRow(QWidget):
    """A single setting row: icon + label + description + control widget."""

    _STYLE = """
        SettingRow {
            background-color: #1C2128;
            border: 1px solid #21262D;
            border-radius: 10px;
        }
        SettingRow:hover {
            border: 1px solid #30363D;
        }
    """

    def __init__(self, icon: str, label: str, description: str,
                 control: QWidget, parent=None):
        super().__init__(parent)
        self.setStyleSheet(self._STYLE)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Icon
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(
            "font-size: 18px; background: transparent; color: #E6EDF3;"
        )
        icon_lbl.setFixedWidth(28)
        layout.addWidget(icon_lbl)

        # Text block
        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        name_lbl = QLabel(label)
        name_lbl.setStyleSheet(
            "color: #E6EDF3; font-size: 13px; font-weight: 600; background: transparent;"
        )
        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(
            "color: #8B949E; font-size: 11px; background: transparent;"
        )
        text_col.addWidget(name_lbl)
        text_col.addWidget(desc_lbl)
        layout.addLayout(text_col, 1)

        # Control
        layout.addWidget(control)


# ── Section Header ─────────────────────────────────────────────────────────────

class SectionHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            "color: #8B949E; font-size: 10px; font-weight: 600; "
            "letter-spacing: 2px; padding: 16px 4px 6px 4px; background: transparent;"
        )


# ── Toast Notification ─────────────────────────────────────────────────────────

class Toast(QLabel):
    """Brief 'Saved ✓' notification that fades away."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "background-color: #00C853; color: #0D1117; border-radius: 8px;"
            "font-size: 12px; font-weight: 700; padding: 8px 18px;"
        )
        self.setFixedHeight(36)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, msg: str = "Ayarlar kaydedildi  ✓"):
        self.setText(msg)
        self.show()
        self._timer.start(2500)


# ── Nav Button ─────────────────────────────────────────────────────────────────

class SettingsNavBtn(QPushButton):
    _STYLE = """
        QPushButton {
            background-color: transparent;
            color: #8B949E;
            text-align: left;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
            border: none;
        }
        QPushButton:hover {
            background-color: #21262D;
            color: #E6EDF3;
        }
        QPushButton[active="true"] {
            background-color: rgba(0, 212, 255, 0.12);
            color: #00D4FF;
            font-weight: 600;
        }
    """

    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self.setText(f"  {icon}   {label}")
        self.setStyleSheet(self._STYLE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.setCheckable(False)

    def set_active(self, active: bool):
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


# ── Settings View ──────────────────────────────────────────────────────────────

class SettingsView(QWidget):
    """Main settings panel with vertical tab navigation."""

    # emitted when balance or risk % changes so sidebar can refresh
    settings_changed = pyqtSignal()

    TABS = [
        ("⚙️", "Genel",          "general"),
        ("💰", "Hesap",          "account"),
        ("📅", "Takvim",         "calendar"),
        ("📊", "İstatistikler",  "statistics"),
        ("⚡", "Risk",           "risk"),
        ("🗄️", "Veri",           "data"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nav_buttons: dict[str, SettingsNavBtn] = {}
        self._build_ui()
        self._switch_tab("general")

    # ── Build UI ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left nav panel
        nav_panel = QWidget()
        nav_panel.setFixedWidth(210)
        nav_panel.setStyleSheet("background-color: #0D1117; border-right: 1px solid #21262D;")
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(12, 28, 12, 20)
        nav_layout.setSpacing(2)

        # Header
        hdr = QLabel("⚙️  Ayarlar")
        hdr.setStyleSheet(
            "color: #E6EDF3; font-size: 16px; font-weight: 700; "
            "padding: 0 4px 18px 4px; background: transparent;"
        )
        nav_layout.addWidget(hdr)

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #21262D; margin-bottom: 8px;")
        nav_layout.addWidget(divider)

        for icon, label, tab_id in self.TABS:
            btn = SettingsNavBtn(icon, label)
            btn.clicked.connect(lambda _, t=tab_id: self._switch_tab(t))
            self._nav_buttons[tab_id] = btn
            nav_layout.addWidget(btn)

        nav_layout.addStretch()

        root.addWidget(nav_panel)

        # ── Right content area
        content_wrapper = QWidget()
        content_wrapper.setStyleSheet("background-color: #0D1117;")
        cw_layout = QVBoxLayout(content_wrapper)
        cw_layout.setContentsMargins(0, 0, 0, 0)
        cw_layout.setSpacing(0)

        # Toast at top
        toast_row = QHBoxLayout()
        toast_row.setContentsMargins(32, 16, 32, 0)
        self.toast = Toast()
        self.toast.setFixedWidth(280)
        toast_row.addStretch()
        toast_row.addWidget(self.toast)
        cw_layout.addLayout(toast_row)

        # Stacked pages
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        cw_layout.addWidget(self.stack, 1)

        # Build each tab page
        self._pages = {
            "general":    self._build_general(),
            "account":    self._build_account(),
            "calendar":   self._build_calendar(),
            "statistics": self._build_statistics(),
            "risk":       self._build_risk(),
            "data":       self._build_data(),
        }
        for page in self._pages.values():
            self.stack.addWidget(page)

        root.addWidget(content_wrapper, 1)

    # ── Tab Switching ───────────────────────────────────────────────────────────

    def _switch_tab(self, tab_id: str):
        for tid, btn in self._nav_buttons.items():
            btn.set_active(tid == tab_id)
        self.stack.setCurrentWidget(self._pages[tab_id])

    # ── Scroll Page Helper ──────────────────────────────────────────────────────

    def _scroll_page(self, inner: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")
        return scroll

    def _page_inner(self) -> tuple[QWidget, QVBoxLayout]:
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(8)
        return inner, layout

    # ── Shared helpers ──────────────────────────────────────────────────────────

    def _make_toggle(self, key: str) -> ToggleSwitch:
        val = db_manager.get_setting(key, DEFAULTS.get(key, "false"))
        toggle = ToggleSwitch(val.lower() == "true")
        toggle.toggled.connect(lambda v, k=key: self._save_bool(k, v))
        return toggle

    def _make_combo(self, key: str, options: list[tuple[str, str]]) -> QComboBox:
        current = db_manager.get_setting(key, DEFAULTS.get(key, ""))
        combo = QComboBox()
        combo.setFixedWidth(180)
        combo.setStyleSheet(
            "QComboBox { background-color: #1C2128; color: #E6EDF3; "
            "border: 1px solid #30363D; border-radius: 6px; "
            "padding: 5px 10px; font-size: 12px; }"
            "QComboBox:focus { border: 1px solid #00D4FF; }"
            "QComboBox::drop-down { border: none; width: 20px; }"
            "QComboBox QAbstractItemView { background-color: #1C2128; "
            "border: 1px solid #30363D; selection-background-color: rgba(0,212,255,0.15); "
            "color: #E6EDF3; }"
        )
        for display, val in options:
            combo.addItem(display, val)
        # select current
        for i in range(combo.count()):
            if combo.itemData(i) == current:
                combo.setCurrentIndex(i)
                break
        combo.currentIndexChanged.connect(
            lambda _, k=key, c=combo: self._save_str(k, c.currentData())
        )
        return combo

    def _make_spinbox(self, key: str, min_v: float, max_v: float,
                      decimals: int = 1, suffix: str = "") -> QDoubleSpinBox:
        val_str = db_manager.get_setting(key, DEFAULTS.get(key, "0"))
        try:
            val = float(val_str)
        except ValueError:
            val = 0.0
        spin = QDoubleSpinBox()
        spin.setFixedWidth(120)
        spin.setRange(min_v, max_v)
        spin.setDecimals(decimals)
        spin.setSuffix(suffix)
        spin.setValue(val)
        spin.setStyleSheet(
            "QDoubleSpinBox { background-color: #1C2128; color: #E6EDF3; "
            "border: 1px solid #30363D; border-radius: 6px; padding: 5px 8px; "
            "font-size: 12px; }"
            "QDoubleSpinBox:focus { border: 1px solid #00D4FF; }"
            "QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { "
            "background: #30363D; width: 16px; border-radius: 3px; }"
            "QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover { "
            "background: #00D4FF; }"
        )
        spin.valueChanged.connect(
            lambda v, k=key: self._save_str(k, str(v))
        )
        return spin

    def _make_line_edit(self, key: str, placeholder: str = "") -> QLineEdit:
        val = db_manager.get_setting(key, DEFAULTS.get(key, ""))
        edit = QLineEdit(val)
        edit.setPlaceholderText(placeholder)
        edit.setFixedWidth(160)
        edit.setStyleSheet(
            "QLineEdit { background-color: #1C2128; color: #E6EDF3; "
            "border: 1px solid #30363D; border-radius: 6px; padding: 5px 10px; "
            "font-size: 12px; }"
            "QLineEdit:focus { border: 1px solid #00D4FF; }"
        )
        edit.editingFinished.connect(
            lambda k=key, e=edit: self._save_str(k, e.text().strip())
        )
        return edit

    # ── Persistence helpers ─────────────────────────────────────────────────────

    def _save_bool(self, key: str, val: bool):
        db_manager.set_setting(key, "true" if val else "false")
        self.toast.show_message()
        if key in ("show_pnl_in_calendar",):
            self.settings_changed.emit()

    def _save_str(self, key: str, val: str):
        db_manager.set_setting(key, val)
        self.toast.show_message()
        if key in ("balance", "risk_pct_1", "risk_pct_2", "risk_pct_3"):
            self.settings_changed.emit()

    # ── Page: General ───────────────────────────────────────────────────────────

    def _build_general(self) -> QScrollArea:
        inner, layout = self._page_inner()

        # Page title
        title = QLabel("Genel Ayarlar")
        title.setStyleSheet(
            "color: #E6EDF3; font-size: 20px; font-weight: 700; "
            "padding-bottom: 4px; background: transparent;"
        )
        subtitle = QLabel("Uygulama genelindeki temel tercihleri yönetin.")
        subtitle.setStyleSheet("color: #8B949E; font-size: 12px; background: transparent;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # ── Appearance section
        layout.addWidget(SectionHeader("GÖRÜNÜM"))

        layout.addWidget(SettingRow(
            "💱", "Para Birimi Sembolü",
            "İşlemlerde kullanılan para birimi gösterimi",
            self._make_line_edit("currency_symbol", "örn. $, ₺, €")
        ))

        # ── Navigation section
        layout.addWidget(SectionHeader("NAVİGASYON"))

        layout.addWidget(SettingRow(
            "🏠", "Açılış Sayfası",
            "Uygulama başlatıldığında açılacak sayfa",
            self._make_combo("start_page", [
                ("📅  Takvim",               "calendar"),
                ("📊  İstatistikler",        "stats"),
                ("⚡  Risk Hesaplayıcı",     "risk"),
                ("⚖️  Ortalama Maliyet",     "avg_cost"),
                ("🏆  Winrate Hesaplayıcı",  "winrate"),
            ])
        ))

        layout.addStretch()
        return self._scroll_page(inner)

    # ── Page: Account ───────────────────────────────────────────────────────────

    def _build_account(self) -> QScrollArea:
        inner, layout = self._page_inner()

        title = QLabel("Hesap Ayarları")
        title.setStyleSheet(
            "color: #E6EDF3; font-size: 20px; font-weight: 700; "
            "padding-bottom: 4px; background: transparent;"
        )
        subtitle = QLabel("Bakiye ve risk yüzdelerinizi buradan ayarlayabilirsiniz.")
        subtitle.setStyleSheet("color: #8B949E; font-size: 12px; background: transparent;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # ── Balance section
        layout.addWidget(SectionHeader("BAKİYE"))

        balance_spin = self._make_spinbox("balance", 0, 10_000_000, 2, " $")
        layout.addWidget(SettingRow(
            "💰", "Başlangıç Bakiyesi",
            "Portföyünüzün başlangıç değeri (PnL hesaplamalarında kullanılır)",
            balance_spin
        ))

        # ── Risk section
        layout.addWidget(SectionHeader("RİSK YÜZDELERİ"))

        layout.addWidget(SettingRow(
            "🟢", "Risk Oranı 1 (Düşük)",
            "Sidebar'da yeşil olarak gösterilen risk yüzdesi",
            self._make_spinbox("risk_pct_1", 0.1, 100, 1, " %")
        ))
        layout.addWidget(SettingRow(
            "🟡", "Risk Oranı 2 (Orta)",
            "Sidebar'da sarı olarak gösterilen risk yüzdesi",
            self._make_spinbox("risk_pct_2", 0.1, 100, 1, " %")
        ))
        layout.addWidget(SettingRow(
            "🔴", "Risk Oranı 3 (Yüksek)",
            "Sidebar'da kırmızı olarak gösterilen risk yüzdesi",
            self._make_spinbox("risk_pct_3", 0.1, 100, 1, " %")
        ))

        layout.addStretch()
        return self._scroll_page(inner)

    # ── Page: Calendar ──────────────────────────────────────────────────────────

    def _build_calendar(self) -> QScrollArea:
        inner, layout = self._page_inner()

        title = QLabel("Takvim Ayarları")
        title.setStyleSheet(
            "color: #E6EDF3; font-size: 20px; font-weight: 700; "
            "padding-bottom: 4px; background: transparent;"
        )
        subtitle = QLabel("Takvim görünümü ve davranışını özelleştirin.")
        subtitle.setStyleSheet("color: #8B949E; font-size: 12px; background: transparent;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addWidget(SectionHeader("GÖRÜNÜM"))

        layout.addWidget(SettingRow(
            "📆", "Hafta Başlangıcı",
            "Takvim haftasının hangi gün başlayacağı",
            self._make_combo("calendar_week_start", [
                ("Pazartesi", "monday"),
                ("Pazar",     "sunday"),
            ])
        ))

        layout.addWidget(SettingRow(
            "💹", "Günlük PnL Göster",
            "Takvim günlerinde kazanç/kayıp miktarını göster",
            self._make_toggle("show_pnl_in_calendar")
        ))

        layout.addStretch()
        return self._scroll_page(inner)

    # ── Page: Statistics ────────────────────────────────────────────────────────

    def _build_statistics(self) -> QScrollArea:
        inner, layout = self._page_inner()

        title = QLabel("İstatistik Ayarları")
        title.setStyleSheet(
            "color: #E6EDF3; font-size: 20px; font-weight: 700; "
            "padding-bottom: 4px; background: transparent;"
        )
        subtitle = QLabel("İstatistik sayfasındaki grafik ve gösterim tercihleriniz.")
        subtitle.setStyleSheet("color: #8B949E; font-size: 12px; background: transparent;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addWidget(SectionHeader("GRAFİK"))

        layout.addWidget(SettingRow(
            "📊", "Grafik Türü",
            "İstatistik sayfasında kullanılacak varsayılan grafik türü",
            self._make_combo("stats_chart_type", [
                ("📊  Çubuk Grafik",  "bar"),
                ("📈  Çizgi Grafik",  "line"),
                ("🥧  Pasta Grafik",  "pie"),
            ])
        ))

        layout.addStretch()
        return self._scroll_page(inner)

    # ── Page: Risk ──────────────────────────────────────────────────────────────

    def _build_risk(self) -> QScrollArea:
        inner, layout = self._page_inner()

        title = QLabel("Risk Hesaplayıcı Ayarları")
        title.setStyleSheet(
            "color: #E6EDF3; font-size: 20px; font-weight: 700; "
            "padding-bottom: 4px; background: transparent;"
        )
        subtitle = QLabel("Risk hesaplayıcı için varsayılan değerler ve uyarı eşikleri.")
        subtitle.setStyleSheet("color: #8B949E; font-size: 12px; background: transparent;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addWidget(SectionHeader("VARSAYILANLAR"))

        layout.addWidget(SettingRow(
            "⚡", "Varsayılan Kaldıraç",
            "Risk hesaplayıcı açıldığında kullanılan başlangıç kaldıracı",
            self._make_spinbox("default_leverage", 1, 200, 0, "x")
        ))

        layout.addWidget(SectionHeader("UYARILAR"))

        layout.addWidget(SettingRow(
            "⚠️", "Risk Uyarı Eşiği",
            "Bu yüzdeyi aştığınızda kırmızı uyarı gösterilir",
            self._make_spinbox("risk_warning_threshold", 0.5, 50, 1, " %")
        ))

        layout.addStretch()
        return self._scroll_page(inner)

    # ── Page: Data ──────────────────────────────────────────────────────────────

    def _build_data(self) -> QScrollArea:
        inner, layout = self._page_inner()

        title = QLabel("Veri Yönetimi")
        title.setStyleSheet(
            "color: #E6EDF3; font-size: 20px; font-weight: 700; "
            "padding-bottom: 4px; background: transparent;"
        )
        subtitle = QLabel("Veritabanı işlemleri ve fabrika ayarlarına dönüş.")
        subtitle.setStyleSheet("color: #8B949E; font-size: 12px; background: transparent;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addWidget(SectionHeader("AYARLAR"))

        # Restore defaults
        restore_btn = self._action_button(
            "Varsayılanlara Dön", "#F0A500", "#0D1117",
            "Tüm ayarları fabrika değerlerine sıfırla"
        )
        restore_btn.clicked.connect(self._restore_defaults)
        layout.addWidget(SettingRow(
            "🔄", "Fabrika Ayarları",
            "Tüm ayarlar (bakiye hariç) varsayılan değerlere döner",
            restore_btn
        ))

        layout.addWidget(SectionHeader("VERİTABANI"))

        # DB info card
        db_card = self._db_info_card()
        layout.addWidget(db_card)

        layout.addStretch()
        return self._scroll_page(inner)

    # ── Action Button ───────────────────────────────────────────────────────────

    def _action_button(self, text: str, bg: str, fg: str, tip: str = "") -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(34)
        btn.setToolTip(tip)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: none;
                border-radius: 7px;
                padding: 0 16px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                opacity: 0.85;
            }}
            QPushButton:pressed {{
                opacity: 0.7;
            }}
        """)
        return btn

    # ── DB Info Card ────────────────────────────────────────────────────────────

    def _db_info_card(self) -> QWidget:
        import os
        card = QWidget()
        card.setStyleSheet(
            "background-color: #1C2128; border: 1px solid #21262D; border-radius: 10px;"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        hdr = QLabel("📁  Veritabanı Bilgisi")
        hdr.setStyleSheet(
            "color: #E6EDF3; font-size: 13px; font-weight: 600; background: transparent;"
        )
        layout.addWidget(hdr)

        from database import db_manager as _db
        db_path = _db.DB_PATH
        try:
            size_bytes = os.path.getsize(db_path)
            size_str = (
                f"{size_bytes / 1024:.1f} KB" if size_bytes < 1024 * 1024
                else f"{size_bytes / (1024*1024):.2f} MB"
            )
        except Exception:
            size_str = "Bilinmiyor"

        for label, value in [
            ("Konum", db_path),
            ("Boyut",  size_str),
        ]:
            row = QHBoxLayout()
            row.setSpacing(8)
            k = QLabel(label + ":")
            k.setStyleSheet("color: #8B949E; font-size: 11px; background: transparent;")
            k.setFixedWidth(52)
            v = QLabel(value)
            v.setStyleSheet("color: #E6EDF3; font-size: 11px; background: transparent;")
            v.setWordWrap(True)
            row.addWidget(k)
            row.addWidget(v, 1)
            layout.addLayout(row)

        return card

    # ── Restore Defaults ────────────────────────────────────────────────────────

    def _restore_defaults(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Fabrika Ayarları")
        dlg.setFixedSize(420, 220)
        dlg.setStyleSheet(
            "QDialog { background-color: #0D1117; }"
            "QLabel  { background: transparent; }"
        )

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(12)

        icon_lbl = QLabel("🔄")
        icon_lbl.setStyleSheet("font-size: 36px; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel("Varsayılanlara Dön")
        title_lbl.setStyleSheet(
            "color: #E6EDF3; font-size: 16px; font-weight: 700; background: transparent;"
        )
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_lbl = QLabel(
            "Tüm ayarlar (bakiye hariç) fabrika değerlerine sıfırlanacak.\n"
            "Bu işlem geri alınamaz. Devam etmek istiyor musunuz?"
        )
        desc_lbl.setStyleSheet("color: #8B949E; font-size: 12px; background: transparent;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)

        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)
        layout.addSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("İptal")
        cancel_btn.setFixedHeight(36)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(
            "QPushButton { background: #21262D; color: #8B949E; border: none; "
            "border-radius: 8px; font-size: 13px; font-weight: 600; padding: 0 20px; }"
            "QPushButton:hover { background: #30363D; color: #E6EDF3; }"
        )
        cancel_btn.clicked.connect(dlg.reject)

        confirm_btn = QPushButton("Sıfırla")
        confirm_btn.setFixedHeight(36)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.setStyleSheet(
            "QPushButton { background: #F0A500; color: #0D1117; border: none; "
            "border-radius: 8px; font-size: 13px; font-weight: 700; padding: 0 20px; }"
            "QPushButton:hover { background: #FFB830; }"
        )
        confirm_btn.clicked.connect(dlg.accept)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(confirm_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._do_restore_defaults()

    def _do_restore_defaults(self):
        """Write all defaults (except balance) to DB."""
        skip_keys = {"balance"}
        for key, val in DEFAULTS.items():
            if key not in skip_keys:
                db_manager.set_setting(key, val)

        # Rebuild all pages so controls reflect new values
        tab_ids = [tid for _, _, tid in self.TABS]
        for tab_id in tab_ids:
            old_widget = self._pages[tab_id]
            idx = self.stack.indexOf(old_widget)
            builder = getattr(self, f"_build_{tab_id}")
            new_widget = builder()
            self._pages[tab_id] = new_widget
            self.stack.insertWidget(idx, new_widget)
            self.stack.removeWidget(old_widget)
            old_widget.deleteLater()

        self.settings_changed.emit()
        self.toast.show_message("Ayarlar sıfırlandı  ✓")


    # ── Public API ──────────────────────────────────────────────────────────────

    def refresh(self):
        """Called externally if settings need to be re-read."""
        pass
