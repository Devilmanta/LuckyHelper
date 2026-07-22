"""
LuckyHelper - Statistics View
Professional trading performance dashboard with industry-standard metrics.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSizePolicy, QGraphicsDropShadowEffect, QPushButton
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient

from database import db_manager


# ── Turkish month names ────────────────────────────────────────────────────────
TURKISH_MONTHS_SHORT = {
    "01": "Oca", "02": "Şub", "03": "Mar", "04": "Nis",
    "05": "May", "06": "Haz", "07": "Tem", "08": "Ağu",
    "09": "Eyl", "10": "Eki", "11": "Kas", "12": "Ara",
}


# ── Helper: section title ──────────────────────────────────────────────────────

def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #8B949E; font-size: 10px; font-weight: 700; letter-spacing: 2px;"
        "text-transform: uppercase; background: transparent; padding-bottom: 4px;"
    )
    return lbl


# ── Mini bar chart widget ──────────────────────────────────────────────────────

class MiniBarChart(QWidget):
    """Draws a compact horizontal bar for symbol performance."""

    def __init__(self, value: float, max_abs: float, color: str, parent=None):
        super().__init__(parent)
        self._value = value
        self._max_abs = max_abs
        self._color = color
        self.setFixedHeight(10)
        self.setMinimumWidth(60)

    def paintEvent(self, event):
        if self._max_abs <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        ratio = min(abs(self._value) / self._max_abs, 1.0)
        bar_w = max(4, int(w * ratio))
        p.setBrush(QBrush(QColor(self._color)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 1, bar_w, h - 2, 3, 3)


# ── Monthly bar chart ─────────────────────────────────────────────────────────

class MonthlyBarChart(QWidget):
    """Draws a vertical bar chart for monthly PnL data."""

    def __init__(self, data: list[dict], parent=None):
        super().__init__(parent)
        self._data = data  # [{"month": "YYYY-MM", "pnl": float}]
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event):
        if not self._data:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        n = len(self._data)
        max_abs = max(abs(d["pnl"]) for d in self._data) or 1.0

        margin_x = 8
        margin_top = 8
        label_h = 22
        chart_h = h - margin_top - label_h

        bar_area_w = w - 2 * margin_x
        bar_w = max(6, bar_area_w // max(n, 1) - 4)
        gap = (bar_area_w - bar_w * n) // max(n - 1, 1) if n > 1 else 0

        baseline_y = margin_top + chart_h // 2

        # Baseline
        p.setPen(QPen(QColor("#21262D"), 1))
        p.drawLine(margin_x, baseline_y, w - margin_x, baseline_y)

        for i, d in enumerate(self._data):
            x = margin_x + i * (bar_w + gap)
            ratio = d["pnl"] / max_abs
            bar_h = int(abs(ratio) * (chart_h // 2 - 4))
            bar_h = max(2, bar_h)

            color = QColor("#00C853") if d["pnl"] >= 0 else QColor("#FF3D57")
            p.setBrush(QBrush(color))
            p.setPen(Qt.PenStyle.NoPen)

            if d["pnl"] >= 0:
                p.drawRoundedRect(x, baseline_y - bar_h, bar_w, bar_h, 3, 3)
            else:
                p.drawRoundedRect(x, baseline_y, bar_w, bar_h, 3, 3)

            # Month label
            month_key = d["month"][5:]  # "MM"
            short = TURKISH_MONTHS_SHORT.get(month_key, month_key)
            p.setPen(QColor("#484F58"))
            font = QFont("Segoe UI", 7)
            p.setFont(font)
            lx = x + bar_w // 2
            p.drawText(lx - 14, h - label_h + 6, 28, label_h - 4,
                       Qt.AlignmentFlag.AlignCenter, short)


# ── KPI Card ──────────────────────────────────────────────────────────────────

class KpiCard(QWidget):
    """A single KPI metric card."""

    def __init__(self, icon: str, label: str, value: str,
                 sub: str = "", color: str = "#E6EDF3",
                 badge: str = "", badge_color: str = "#00D4FF",
                 parent=None):
        super().__init__(parent)
        self.setObjectName("StatsCard")
        self._build(icon, label, value, sub, color, badge, badge_color)

    def _build(self, icon, label, value, sub, color, badge, badge_color):
        ly = QVBoxLayout(self)
        ly.setContentsMargins(16, 14, 16, 14)
        ly.setSpacing(4)

        # Top row: icon + label + optional badge
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(6)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 15px; background: transparent;")
        lbl = QLabel(label)
        lbl.setStyleSheet(
            "color: #8B949E; font-size: 11px; font-weight: 600; background: transparent;"
        )
        top.addWidget(icon_lbl)
        top.addWidget(lbl)
        top.addStretch()

        if badge:
            badge_lbl = QLabel(badge)
            badge_lbl.setStyleSheet(
                f"background-color: rgba({_hex_to_rgba(badge_color, 0.15)});"
                f"color: {badge_color}; border-radius: 8px;"
                "font-size: 9px; font-weight: 700; padding: 2px 6px;"
            )
            top.addWidget(badge_lbl)

        ly.addLayout(top)

        # Value
        self.val_lbl = QLabel(value)
        self.val_lbl.setStyleSheet(
            f"color: {color}; font-size: 22px; font-weight: 800; background: transparent;"
        )
        ly.addWidget(self.val_lbl)

        # Sub-label
        if sub:
            sub_lbl = QLabel(sub)
            sub_lbl.setStyleSheet(
                "color: #484F58; font-size: 10px; background: transparent;"
            )
            ly.addWidget(sub_lbl)

    def update_value(self, value: str, color: str = "#E6EDF3"):
        self.val_lbl.setText(value)
        self.val_lbl.setStyleSheet(
            f"color: {color}; font-size: 22px; font-weight: 800; background: transparent;"
        )


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert '#RRGGBB' to 'R, G, B, A' string for QSS rgba()."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r}, {g}, {b}, {int(alpha * 255)}"


# ── Symbol Row ────────────────────────────────────────────────────────────────

class SymbolRow(QWidget):
    """One row in the symbol leaderboard."""

    def __init__(self, rank: int, sym_data: dict, max_abs: float, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        pnl = sym_data["pnl"]
        color = "#00C853" if pnl >= 0 else "#FF3D57"
        wr = sym_data["win_rate"]

        ly = QHBoxLayout(self)
        ly.setContentsMargins(12, 8, 12, 8)
        ly.setSpacing(10)

        # Rank badge
        rank_lbl = QLabel(f"#{rank}")
        rank_lbl.setStyleSheet(
            "color: #484F58; font-size: 11px; font-weight: 700;"
            "background: transparent; min-width: 24px;"
        )
        ly.addWidget(rank_lbl)

        # Symbol
        sym_lbl = QLabel(sym_data["symbol"])
        sym_lbl.setStyleSheet(
            "color: #E6EDF3; font-size: 13px; font-weight: 700; background: transparent;"
        )
        sym_lbl.setMinimumWidth(90)
        ly.addWidget(sym_lbl)

        # Count
        cnt_lbl = QLabel(f"{sym_data['count']} işlem")
        cnt_lbl.setStyleSheet("color: #8B949E; font-size: 11px; background: transparent;")
        cnt_lbl.setMinimumWidth(60)
        ly.addWidget(cnt_lbl)

        # Win-rate
        wr_lbl = QLabel(f"%{wr:.0f} WR")
        wr_lbl.setStyleSheet(
            f"color: {'#00C853' if wr >= 50 else '#FF3D57'}; font-size: 11px;"
            "font-weight: 600; background: transparent;"
        )
        wr_lbl.setMinimumWidth(60)
        ly.addWidget(wr_lbl)

        # Mini bar
        bar = MiniBarChart(pnl, max_abs, color)
        bar.setMinimumWidth(80)
        ly.addWidget(bar, 1)

        # PnL
        sign = "+" if pnl >= 0 else ""
        pnl_lbl = QLabel(f"{sign}${pnl:,.2f}")
        pnl_lbl.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: 700; background: transparent;"
        )
        pnl_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        pnl_lbl.setMinimumWidth(90)
        ly.addWidget(pnl_lbl)


# ── Direction Split Card ──────────────────────────────────────────────────────

class DirectionSplitCard(QWidget):
    """Shows LONG vs SHORT stats side by side."""

    def __init__(self, stats: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("StatsCard")
        self._build(stats)

    def _build(self, s: dict):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)

        title_row = QHBoxLayout()
        icon = QLabel("↕️")
        icon.setStyleSheet("font-size: 15px; background: transparent;")
        title = QLabel("Long vs Short")
        title.setStyleSheet(
            "color: #8B949E; font-size: 11px; font-weight: 600; background: transparent;"
        )
        title_row.addWidget(icon)
        title_row.addWidget(title)
        title_row.addStretch()
        outer.addLayout(title_row)

        cols = QHBoxLayout()
        cols.setSpacing(12)

        for label, count, pnl, wr, color in [
            ("LONG",  s.get("long_count",  0), s.get("long_pnl",  0.0),
             s.get("long_win_rate",  0.0), "#00C853"),
            ("SHORT", s.get("short_count", 0), s.get("short_pnl", 0.0),
             s.get("short_win_rate", 0.0), "#FF7043"),
        ]:
            col = QVBoxLayout()
            col.setSpacing(4)

            name_lbl = QLabel(label)
            name_lbl.setStyleSheet(
                f"color: {color}; font-size: 12px; font-weight: 800; background: transparent;"
            )
            sign = "+" if pnl >= 0 else ""
            pnl_lbl = QLabel(f"{sign}${pnl:,.2f}")
            pnl_lbl.setStyleSheet(
                f"color: {'#00C853' if pnl >= 0 else '#FF3D57'}; font-size: 18px;"
                "font-weight: 800; background: transparent;"
            )
            detail = QLabel(f"{count} işlem  ·  %{wr:.0f} WR")
            detail.setStyleSheet("color: #484F58; font-size: 10px; background: transparent;")

            col.addWidget(name_lbl)
            col.addWidget(pnl_lbl)
            col.addWidget(detail)
            cols.addLayout(col)

        outer.addLayout(cols)


# ── Streak Card ───────────────────────────────────────────────────────────────

class StreakCard(QWidget):
    """Shows max win and loss streaks."""

    def __init__(self, win_streak: int, loss_streak: int, parent=None):
        super().__init__(parent)
        self.setObjectName("StatsCard")
        self._build(win_streak, loss_streak)

    def _build(self, ws: int, ls: int):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)

        title_row = QHBoxLayout()
        icon = QLabel("🔥")
        icon.setStyleSheet("font-size: 15px; background: transparent;")
        title = QLabel("Seri Kayıtları")
        title.setStyleSheet(
            "color: #8B949E; font-size: 11px; font-weight: 600; background: transparent;"
        )
        title_row.addWidget(icon)
        title_row.addWidget(title)
        title_row.addStretch()
        outer.addLayout(title_row)

        cols = QHBoxLayout()
        cols.setSpacing(16)

        for label, val, color, emoji in [
            ("Maks. Kazanma Serisi", ws, "#00C853", "🏆"),
            ("Maks. Kaybetme Serisi", ls, "#FF3D57", "💀"),
        ]:
            col = QVBoxLayout()
            col.setSpacing(2)
            e_lbl = QLabel(emoji)
            e_lbl.setStyleSheet("font-size: 20px; background: transparent;")
            v_lbl = QLabel(str(val))
            v_lbl.setStyleSheet(
                f"color: {color}; font-size: 28px; font-weight: 900; background: transparent;"
            )
            l_lbl = QLabel(label)
            l_lbl.setStyleSheet("color: #484F58; font-size: 10px; background: transparent;")
            col.addWidget(e_lbl)
            col.addWidget(v_lbl)
            col.addWidget(l_lbl)
            cols.addLayout(col)

        outer.addLayout(cols)


# ── Empty State ───────────────────────────────────────────────────────────────

class EmptyStatsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        ly = QVBoxLayout(self)
        ly.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ly.setSpacing(14)

        icon = QLabel("📊")
        icon.setStyleSheet("font-size: 64px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Henüz istatistik yok")
        title.setStyleSheet(
            "color: #E6EDF3; font-size: 22px; font-weight: 700; background: transparent;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Takvim sekmesinden işlem ekledikçe\nistatistikleriniz burada görünecek.")
        sub.setStyleSheet(
            "color: #8B949E; font-size: 14px; background: transparent;"
        )
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        badge = QLabel("📅  Takvime git ve ilk işlemini ekle")
        badge.setStyleSheet(
            "background-color: rgba(0,212,255,0.10); color: #00D4FF;"
            "border: 1px solid #00D4FF; border-radius: 20px;"
            "font-size: 12px; font-weight: 600; padding: 8px 20px;"
        )
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ly.addWidget(icon)
        ly.addWidget(title)
        ly.addWidget(sub)
        ly.addSpacing(12)
        ly.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)


# ── Main Statistics View ──────────────────────────────────────────────────────

class StatisticsView(QWidget):
    """
    Professional trading statistics dashboard.
    Shows KPI cards, charts, and leaderboards.
    """

    _CARD_STYLE = """
        QWidget#StatsCard {
            background-color: #161B22;
            border: 1px solid #21262D;
            border-radius: 12px;
        }
        QWidget#StatsCard:hover {
            border: 1px solid #30363D;
            background-color: #1C2128;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentArea")
        self._build_ui()

    # ──────────────────────────────────────────────────────────────────────────
    #  UI BUILD
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Page header ───────────────────────────────────────────
        header = QWidget()
        header.setObjectName("CalendarHeader")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(32, 24, 32, 16)
        h_lay.setSpacing(12)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title_lbl = QLabel("İstatistikler")
        title_lbl.setObjectName("CalendarTitle")
        sub_lbl = QLabel("Tüm zamanlar · Endüstri standartı performans metrikleri")
        sub_lbl.setObjectName("CalendarSubtitle")
        title_block.addWidget(title_lbl)
        title_block.addWidget(sub_lbl)

        h_lay.addLayout(title_block)
        h_lay.addStretch()

        # Refresh button
        refresh_btn = QPushButton("↻  Yenile")
        refresh_btn.setObjectName("TodayBtn")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh)
        h_lay.addWidget(refresh_btn)

        root.addWidget(header)

        # ── Scroll area ───────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: #0D1117; border: none;")

        self._content = QWidget()
        self._content.setStyleSheet("background: #0D1117;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(32, 24, 32, 32)
        self._content_layout.setSpacing(24)

        scroll.setWidget(self._content)
        root.addWidget(scroll, 1)

    # ──────────────────────────────────────────────────────────────────────────
    #  DATA LOADING
    # ──────────────────────────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()

    def refresh(self):
        """Reload stats from DB and rebuild the content area."""
        # Clear old content
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        stats = db_manager.get_advanced_stats()

        if not stats:
            self._content_layout.addWidget(EmptyStatsWidget())
            self._content_layout.addStretch()
            return

        self._build_content(stats)

    def _build_content(self, s: dict):
        """Build all statistics sections."""
        cl = self._content_layout

        # ── Section 1: Top KPI row ────────────────────────────────
        cl.addWidget(_section_title("GENEL BAKIŞ"))
        cl.addWidget(self._wrap_row(self._build_overview_row(s)))

        # ── Section 2: Performance metrics ───────────────────────
        cl.addWidget(_section_title("PERFORMANS METRİKLERİ"))
        cl.addWidget(self._wrap_row(self._build_performance_row(s)))

        # ── Section 3: Monthly chart + Direction + Streak ─────────
        cl.addWidget(_section_title("ANALİZ"))
        cl.addWidget(self._build_analysis_row(s))

        # ── Section 4: Symbol leaderboard ────────────────────────
        cl.addWidget(_section_title("SEMBOL PERFORMANSI"))
        cl.addWidget(self._build_symbol_table(s))

        cl.addStretch()

    # ──────────────────────────────────────────────────────────────────────────
    #  HELPERS
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _wrap_row(layout: QHBoxLayout) -> QWidget:
        """Wrap a QHBoxLayout in a QWidget so it can be added to a QVBoxLayout."""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container.setLayout(layout)
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return container

    # ──────────────────────────────────────────────────────────────────────────
    #  SECTION BUILDERS
    # ──────────────────────────────────────────────────────────────────────────

    def _build_overview_row(self, s: dict) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)

        total_pnl = s["total_pnl"]
        pnl_color = "#00C853" if total_pnl >= 0 else "#FF3D57"
        sign = "+" if total_pnl >= 0 else ""

        cards = [
            KpiCard("💰", "Toplam PnL",
                    f"{sign}${total_pnl:,.2f}",
                    f"{s['total_trades']} işlemin toplamı",
                    pnl_color),
            KpiCard("📈", "Win Rate",
                    f"%{s['win_rate']:.1f}",
                    f"{s['win_count']}K / {s['loss_count']}K / {s['breakeven_count']}BE",
                    "#00C853" if s["win_rate"] >= 50 else "#FF7043",
                    "KAZANMA", "#00C853" if s["win_rate"] >= 50 else "#FF7043"),
            KpiCard("⚖️", "Profit Factor",
                    f"{s['profit_factor']:.2f}" if s["profit_factor"] != float("inf") else "∞",
                    "Brüt kâr / Brüt zarar",
                    self._pf_color(s["profit_factor"]),
                    self._pf_badge(s["profit_factor"]), self._pf_color(s["profit_factor"])),
            KpiCard("🎯", "Beklenti",
                    f"${s['expectancy']:+,.2f}",
                    "İşlem başına beklenen kâr",
                    "#00C853" if s["expectancy"] >= 0 else "#FF3D57"),
            KpiCard("💸", "Toplam Fee",
                    f"-${s.get('total_fee', 0.0):,.2f}",
                    "Ödenen toplam komisyon",
                    "#FF7043"),
        ]

        for c in cards:
            c.setStyleSheet(self._CARD_STYLE)
            c.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            row.addWidget(c)

        return row

    def _build_performance_row(self, s: dict) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)

        sharpe = s["sharpe"]
        sharpe_color = (
            "#00C853" if sharpe >= 2.0 else
            "#F0A500" if sharpe >= 1.0 else
            "#FF3D57"
        )
        sharpe_badge = (
            "MÜKEMMEL" if sharpe >= 2.0 else
            "İYİ"      if sharpe >= 1.0 else
            "ZAYIF"
        )

        cards = [
            KpiCard("📉", "Max Drawdown",
                    f"-${s['max_drawdown']:,.2f}",
                    "Tepe noktasından en büyük düşüş",
                    "#FF3D57"),
            KpiCard("📐", "Sharpe Oranı",
                    f"{sharpe:.2f}",
                    "Yıllıklaştırılmış risk-düzeltmeli getiri",
                    sharpe_color, sharpe_badge, sharpe_color),
            KpiCard("🔁", "Risk/Ödül",
                    f"{s['rr_ratio']:.2f}",
                    f"Ort. Kazanç ${s['avg_win']:,.0f} · Ort. Kayıp ${s['avg_loss']:,.0f}",
                    "#00D4FF"),
            KpiCard("🔄", "Recovery Factor",
                    f"{s['recovery_factor']:.2f}",
                    "Toplam PnL / Max Drawdown",
                    "#00C853" if s["recovery_factor"] >= 1 else "#FF7043"),
        ]

        for c in cards:
            c.setStyleSheet(self._CARD_STYLE)
            c.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            row.addWidget(c)

        return row

    def _build_analysis_row(self, s: dict) -> QWidget:
        """Build the analysis section as a proper widget container."""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row = QHBoxLayout(container)
        row.setSpacing(12)
        row.setContentsMargins(0, 0, 0, 0)

        # Monthly chart card
        monthly_card = QWidget()
        monthly_card.setObjectName("StatsCard")
        monthly_card.setStyleSheet(self._CARD_STYLE)
        monthly_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        m_lay = QVBoxLayout(monthly_card)
        m_lay.setContentsMargins(16, 14, 16, 14)
        m_lay.setSpacing(8)

        m_title_row = QHBoxLayout()
        m_icon = QLabel("📅")
        m_icon.setStyleSheet("font-size: 15px; background: transparent;")
        m_title = QLabel("Aylık PnL Dağılımı")
        m_title.setStyleSheet(
            "color: #8B949E; font-size: 11px; font-weight: 600; background: transparent;"
        )
        m_title_row.addWidget(m_icon)
        m_title_row.addWidget(m_title)
        m_title_row.addStretch()
        m_lay.addLayout(m_title_row)

        chart = MonthlyBarChart(s.get("monthly_breakdown", []))
        chart.setFixedHeight(140)
        m_lay.addWidget(chart)

        # Best and worst month info
        if s.get("monthly_breakdown"):
            best_m = max(s["monthly_breakdown"], key=lambda x: x["pnl"])
            worst_m = min(s["monthly_breakdown"], key=lambda x: x["pnl"])
            best_key = best_m["month"][5:]
            worst_key = worst_m["month"][5:]
            info_row = QHBoxLayout()
            for label, d, color in [
                ("En İyi Ay", f"{TURKISH_MONTHS_SHORT.get(best_key, best_key)} {best_m['month'][:4]} · +${best_m['pnl']:,.2f}", "#00C853"),
                ("En Kötü Ay", f"{TURKISH_MONTHS_SHORT.get(worst_key, worst_key)} {worst_m['month'][:4]} · -${abs(worst_m['pnl']):,.2f}", "#FF3D57"),
            ]:
                col = QVBoxLayout()
                lbl = QLabel(label)
                lbl.setStyleSheet("color: #484F58; font-size: 10px; background: transparent;")
                val = QLabel(d)
                val.setStyleSheet(
                    f"color: {color}; font-size: 11px; font-weight: 700; background: transparent;"
                )
                col.addWidget(lbl)
                col.addWidget(val)
                info_row.addLayout(col)
            info_row.addStretch()
            m_lay.addLayout(info_row)

        row.addWidget(monthly_card, 2)

        # Right column: Direction + Streak + Extra (stacked vertically, no stretch between)
        right_col_widget = QWidget()
        right_col_widget.setStyleSheet("background: transparent;")
        right_col_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        right_col = QVBoxLayout(right_col_widget)
        right_col.setSpacing(12)
        right_col.setContentsMargins(0, 0, 0, 0)

        dir_card = DirectionSplitCard(s)
        dir_card.setStyleSheet(self._CARD_STYLE)
        dir_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        right_col.addWidget(dir_card)

        streak_card = StreakCard(s["max_win_streak"], s["max_loss_streak"])
        streak_card.setStyleSheet(self._CARD_STYLE)
        streak_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        right_col.addWidget(streak_card)

        # Extra stats card (no stretch before it — keeps cards stacked tightly)
        extra = self._build_extra_card(s)
        extra.setStyleSheet(self._CARD_STYLE)
        extra.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        right_col.addWidget(extra)

        right_col.addStretch()  # push all cards to top

        row.addWidget(right_col_widget, 1)
        return container

    def _build_extra_card(self, s: dict) -> QWidget:
        """Miscellaneous stats card."""
        card = QWidget()
        card.setObjectName("StatsCard")
        ly = QVBoxLayout(card)
        ly.setContentsMargins(16, 14, 16, 14)
        ly.setSpacing(6)

        title_row = QHBoxLayout()
        icon = QLabel("📋")
        icon.setStyleSheet("font-size: 15px; background: transparent;")
        title = QLabel("Diğer Metrikler")
        title.setStyleSheet(
            "color: #8B949E; font-size: 11px; font-weight: 600; background: transparent;"
        )
        title_row.addWidget(icon)
        title_row.addWidget(title)
        title_row.addStretch()
        ly.addLayout(title_row)

        rows = [
            ("En Büyük Kazanç", f"+${s['best_trade']:,.2f}", "#00C853"),
            ("En Büyük Kayıp",  f"-${abs(s['worst_trade']):,.2f}", "#FF3D57"),
            ("Aktif Gün Sayısı", str(s["active_days"]), "#E6EDF3"),
            ("Gün Başına Ort. İşlem", f"{s['avg_trades_per_day']:.1f}", "#E6EDF3"),
            ("Brüt Kâr",  f"+${s['gross_profit']:,.2f}", "#00C853"),
            ("Brüt Zarar", f"-${s['gross_loss']:,.2f}", "#FF3D57"),
        ]

        for label, value, color in rows:
            r = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #8B949E; font-size: 11px; background: transparent;")
            val = QLabel(value)
            val.setStyleSheet(
                f"color: {color}; font-size: 11px; font-weight: 700; background: transparent;"
            )
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            r.addWidget(lbl)
            r.addStretch()
            r.addWidget(val)
            ly.addLayout(r)

            # Thin divider
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("background-color: #21262D; max-height: 1px; border: none;")
            ly.addWidget(sep)

        return card

    def _build_symbol_table(self, s: dict) -> QWidget:
        """Symbol leaderboard table."""
        card = QWidget()
        card.setObjectName("StatsCard")
        card.setStyleSheet(self._CARD_STYLE)
        ly = QVBoxLayout(card)
        ly.setContentsMargins(0, 0, 0, 0)
        ly.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setStyleSheet(
            "background-color: #1C2128; border-radius: 11px 11px 0 0;"
            "border-bottom: 1px solid #21262D;"
        )
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(12, 10, 12, 10)
        hdr_lay.setSpacing(10)

        for text, min_w in [("#", 24), ("Sembol", 90), ("İşlem", 60),
                             ("Win Rate", 60), ("PnL Bar", 80), ("PnL", 90)]:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "color: #484F58; font-size: 10px; font-weight: 700; letter-spacing: 1px;"
                "background: transparent;"
            )
            lbl.setMinimumWidth(min_w)
            if text in ("PnL", "PnL Bar"):
                lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            hdr_lay.addWidget(lbl)
        hdr_lay.addStretch()
        ly.addWidget(hdr)

        syms = s.get("symbol_performance", [])
        if not syms:
            empty = QLabel("İşlem kaydı yok.")
            empty.setStyleSheet(
                "color: #484F58; font-size: 12px; padding: 16px; background: transparent;"
            )
            ly.addWidget(empty)
            return card

        max_abs = max(abs(sym["pnl"]) for sym in syms) or 1.0

        for i, sym in enumerate(syms[:15]):  # Show top 15
            row_widget = SymbolRow(i + 1, sym, max_abs)
            if i % 2 == 1:
                row_widget.setStyleSheet("background-color: rgba(255,255,255,0.02);")
            ly.addWidget(row_widget)

            if i < len(syms) - 1 and i < 14:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet("background-color: #21262D; max-height: 1px; border: none;")
                ly.addWidget(sep)

        return card

    # ──────────────────────────────────────────────────────────────────────────
    #  HELPERS
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _pf_color(pf: float) -> str:
        if pf == float("inf") or pf >= 2.0:
            return "#00C853"
        if pf >= 1.0:
            return "#F0A500"
        return "#FF3D57"

    @staticmethod
    def _pf_badge(pf: float) -> str:
        if pf == float("inf") or pf >= 2.0:
            return "MÜKEMMEL"
        if pf >= 1.5:
            return "İYİ"
        if pf >= 1.0:
            return "KABUL"
        return "NEGATIF"
