"""
LuckyHelper - Trade Entry / Edit Dialog
Opens when user clicks on a calendar day cell.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QWidget, QHeaderView,
    QFrame, QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit,
    QSizePolicy, QAbstractItemView, QMessageBox, QFormLayout,
    QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QEvent
from PyQt6.QtGui import QColor, QFont, QBrush, QPixmap

import os
from datetime import datetime
from database import db_manager


# Column indexes in the trade table
COL_ID       = 0   # hidden
COL_SYMBOL   = 1
COL_DIR      = 2
COL_ENTRY    = 3
COL_EXIT     = 4
COL_QTY      = 5
COL_TP       = 6
COL_SL       = 7
COL_PNL      = 8
COL_IMG      = 9
COL_NOTES    = 10

COLUMNS = ["ID", "Sembol", "Yön", "Entry", "Exit", "Miktar", "TP", "SL", "PnL ($)", "Grafik", "Notlar"]


class TradeFormDialog(QDialog):
    """
    Trade entry / edit dialog.

    Akış:
      1. Sembol, Yön, Entry, Stop Loss gir
      2. Risk % seç  →  pozisyon boyutu otomatik hesaplanır
      3. (İsteğe bağlı) TP gir
      4. Exit gir  →  PnL otomatik hesaplanır (read-only)
      5. Kaydet
    """

    # ── Shared inline styles ──────────────────────────────────
    _SAVE_SS = """
        QPushButton {
            background-color: #00C853; color: #0D1117; border: none;
            border-radius: 8px; padding: 0 22px; font-size: 13px; font-weight: 700;
        }
        QPushButton:hover   { background-color: #00E676; }
        QPushButton:pressed { background-color: #009624; }
    """
    _CANCEL_SS = """
        QPushButton {
            background-color: #21262D; color: #8B949E; border: none;
            border-radius: 8px; padding: 0 16px; font-size: 13px; font-weight: 600;
        }
        QPushButton:hover { background-color: #30363D; color: #E6EDF3; }
    """
    _SPIN_SS = """
        QDoubleSpinBox, QSpinBox {
            background-color: #1C2128; color: #E6EDF3;
            border: 1px solid #30363D; border-radius: 6px;
            padding: 6px 8px; font-size: 13px;
        }
        QDoubleSpinBox:focus, QSpinBox:focus { border: 1px solid #00D4FF; }
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button, QSpinBox::up-button, QSpinBox::down-button {
            background-color: #30363D; width: 16px; border-radius: 3px;
        }
        QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover, QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background-color: #00D4FF;
        }
    """
    _LINE_SS = """
        QLineEdit {
            background-color: #1C2128; color: #E6EDF3;
            border: 1px solid #30363D; border-radius: 6px;
            padding: 6px 10px; font-size: 13px;
        }
        QLineEdit:focus { border: 1px solid #00D4FF; }
    """
    _COMBO_SS = """
        QComboBox {
            background-color: #1C2128; color: #E6EDF3;
            border: 1px solid #30363D; border-radius: 6px;
            padding: 6px 10px; font-size: 13px;
        }
        QComboBox:focus { border: 1px solid #00D4FF; }
        QComboBox::drop-down { border: none; width: 24px; }
        QComboBox QAbstractItemView {
            background-color: #1C2128; border: 1px solid #30363D;
            selection-background-color: rgba(0,212,255,0.15); color: #E6EDF3;
        }
    """
    _RISK_BTN_SS = """
        QPushButton {{
            background-color: {bg}; color: {fg};
            border: 1px solid {border}; border-radius: 6px;
            padding: 4px 10px; font-size: 11px; font-weight: 700;
        }}
        QPushButton:hover {{
            background-color: rgba(0,212,255,0.15); color: #00D4FF;
            border-color: #00D4FF;
        }}
    """
    _PNL_DISPLAY_SS = """
        QLabel {{
            font-size: 20px; font-weight: 800;
            color: {color};
            background-color: {bg};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 10px 16px;
        }}
    """

    RISK_PRESETS = [0.5, 1.0, 2.0, 3.0]

    def __init__(self, trade_date: str, trade_data: dict | None = None, parent=None):
        super().__init__(parent)
        self.trade_date  = trade_date
        self.trade_data  = trade_data
        self.result_data: dict | None = None
        self._block_size_recalc = False   # prevent re-entry during populate

        # Load balance from DB once
        try:
            starting_bal = float(db_manager.get_setting("balance", "0") or "0")
        except ValueError:
            starting_bal = 0.0
        stats = db_manager.get_overall_stats()
        total_pnl = stats.get("total_pnl", 0.0) or 0.0
        self._balance = starting_bal + total_pnl

        self.setWindowTitle("İşlem Ekle" if trade_data is None else "İşlem Düzenle")
        self.setStyleSheet("QDialog { background-color: #0D1117; }")
        self.setMinimumWidth(560)
        self.setModal(True)
        self._build_ui()
        if trade_data:
            self._populate(trade_data)
        
        self._install_clipboard_filter(self)

    def _install_clipboard_filter(self, widget):
        widget.installEventFilter(self)
        from PyQt6.QtWidgets import QWidget
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self)

    # ═══════════════════════════════════════════════════════════
    #  UI BUILD
    # ═══════════════════════════════════════════════════════════
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_title_bar())
        root.addWidget(self._make_form_area())
        root.addWidget(self._make_pnl_area())
        root.addWidget(self._make_btn_bar())

    # ── Title bar ─────────────────────────────────────────────
    def _make_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet("background-color: #161B22; border-bottom: 1px solid #21262D;")
        ly = QHBoxLayout(bar)
        ly.setContentsMargins(24, 14, 24, 14)

        icon = "✏️" if self.trade_data else "➕"
        title = QLabel(f"{icon}  {'İşlem Düzenle' if self.trade_data else 'Yeni İşlem'}")
        title.setStyleSheet("color: #E6EDF3; font-size: 15px; font-weight: 700; background: transparent;")
        ly.addWidget(title)
        ly.addStretch()

        date_lbl = QLabel(self.trade_date)
        date_lbl.setStyleSheet("color: #8B949E; font-size: 12px; background: transparent;")
        ly.addWidget(date_lbl)
        return bar

    # ── Main form ─────────────────────────────────────────────
    def _make_form_area(self) -> QWidget:
        wrap = QWidget()
        wrap.setStyleSheet("background-color: #0D1117;")
        outer = QVBoxLayout(wrap)
        outer.setContentsMargins(24, 20, 24, 12)
        outer.setSpacing(14)

        LS = "color: #8B949E; font-size: 11px; font-weight: 600; background: transparent;"

        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(LS)
            return l

        # ── Row helper: two fields side by side ───────────────
        def row2(lbl1, w1, lbl2, w2):
            r = QHBoxLayout()
            r.setSpacing(12)
            col1 = QVBoxLayout(); col1.setSpacing(4)
            col1.addWidget(lbl1); col1.addWidget(w1)
            col2 = QVBoxLayout(); col2.setSpacing(4)
            col2.addWidget(lbl2); col2.addWidget(w2)
            r.addLayout(col1); r.addLayout(col2)
            return r

        def row3(lbl1, w1, lbl2, w2, lbl3, w3):
            r = QHBoxLayout()
            r.setSpacing(12)
            col1 = QVBoxLayout(); col1.setSpacing(4)
            col1.addWidget(lbl1); col1.addWidget(w1)
            col2 = QVBoxLayout(); col2.setSpacing(4)
            col2.addWidget(lbl2); col2.addWidget(w2)
            col3 = QVBoxLayout(); col3.setSpacing(4)
            col3.addWidget(lbl3); col3.addWidget(w3)
            r.addLayout(col1); r.addLayout(col2); r.addLayout(col3)
            return r

        def row1(lbl1, w1):
            r = QVBoxLayout(); r.setSpacing(4)
            r.addWidget(lbl1); r.addWidget(w1)
            return r

        # ── SYMBOL + YÖN + KALDIRAÇ ───────────────────────────
        self.symbol_edit = QLineEdit()
        self.symbol_edit.setPlaceholderText("örn. BTCUSDT")
        self.symbol_edit.setMaxLength(20)
        self.symbol_edit.setStyleSheet(self._LINE_SS)
        self.symbol_edit.setFixedHeight(36)

        self.dir_combo = QComboBox()
        self.dir_combo.addItems(["LONG", "SHORT"])
        self.dir_combo.setStyleSheet(self._COMBO_SS)
        self.dir_combo.setFixedHeight(36)

        from PyQt6.QtWidgets import QSpinBox
        self.leverage_spin = QSpinBox()
        self.leverage_spin.setRange(1, 200)
        self.leverage_spin.setValue(1)
        self.leverage_spin.setSuffix(" x")
        self.leverage_spin.setKeyboardTracking(False)
        self.leverage_spin.setStyleSheet(self._SPIN_SS)
        self.leverage_spin.setFixedHeight(36)

        outer.addLayout(row3(lbl("SEMBOL *"), self.symbol_edit,
                             lbl("YÖN"),      self.dir_combo,
                             lbl("KALDIRAÇ"), self.leverage_spin))

        # ── ENTRY + STOP LOSS ─────────────────────────────────
        self.entry_spin = self._spin(prefix="$ ", dec=4)
        self.sl_spin    = self._spin(prefix="$ ", dec=4)
        outer.addLayout(row2(lbl("ENTRY FİYATI *"), self.entry_spin,
                             lbl("STOP LOSS *"),    self.sl_spin))

        # (Risk Management section removed)

        # ── POSITION SIZE (auto-filled, editable) ─────────────
        self.size_type_combo = QComboBox()
        self.size_type_combo.addItems(["Miktar (Adet)", "Büyüklük (Notional USD)", "Marjin (Margin USD)"])
        self.size_type_combo.setStyleSheet(self._COMBO_SS)
        self.size_type_combo.setFixedHeight(36)
        self.size_type_combo.setFixedWidth(200)

        self.qty_spin = self._spin(dec=4, max_v=9_999_999)
        self.usd_spin = self._spin(prefix="$ ", dec=2, max_v=9_999_999)
        self.margin_spin = self._spin(prefix="$ ", dec=2, max_v=9_999_999)
        self.usd_spin.hide()
        self.margin_spin.hide()

        size_row = QHBoxLayout()
        size_row.setSpacing(8)
        size_col = QVBoxLayout(); size_col.setSpacing(4)
        size_col.addWidget(lbl("POZİSYON BOYUTU"))
        size_fields = QHBoxLayout(); size_fields.setSpacing(6)
        size_fields.addWidget(self.size_type_combo)
        size_fields.addWidget(self.qty_spin)
        size_fields.addWidget(self.usd_spin)
        size_fields.addWidget(self.margin_spin)
        size_col.addLayout(size_fields)
        size_row.addLayout(size_col)
        outer.addLayout(size_row)


        # ── TAKE PROFIT + EXIT ────────────────────────────────
        self.tp_spin   = self._spin(prefix="$ ", dec=4)
        self.exit_spin = self._spin(prefix="$ ", dec=4)
        outer.addLayout(row2(lbl("TAKE PROFIT"), self.tp_spin,
                             lbl("EXIT FİYATI"), self.exit_spin))

        # ── NOTES ─────────────────────────────────────────────
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notlar, gözlemler, psikoloji...")
        self.notes_edit.setFixedHeight(58)
        self.notes_edit.setStyleSheet(
            "QTextEdit { background-color: #1C2128; color: #E6EDF3; "
            "border: 1px solid #30363D; border-radius: 6px; padding: 6px; font-size: 12px; }"
            "QTextEdit:focus { border: 1px solid #00D4FF; }"
        )
        outer.addLayout(row1(lbl("NOTLAR"), self.notes_edit))

        # ── SCREENSHOT (CHART) ────────────────────────────────
        self.img_path = ""
        
        img_box = QWidget()
        img_box.setStyleSheet("background: transparent;")
        img_ly = QHBoxLayout(img_box)
        img_ly.setContentsMargins(0, 0, 0, 0)
        img_ly.setSpacing(12)
        
        btn_col = QVBoxLayout()
        btn_col.setSpacing(6)
        btn_col.addWidget(lbl("EKRAN GÖRÜNTÜSÜ (GRAFİK)"))
        
        self.img_select_btn = QPushButton("🖼️  Grafik Ekle")
        self.img_select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.img_select_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262D; color: #C9D1D9; border: 1px solid #30363D;
                border-radius: 6px; padding: 8px 12px; font-size: 12px; font-weight: 600;
            }
            QPushButton:hover { background-color: #30363D; color: #E6EDF3; border-color: #8B949E; }
        """)
        self.img_select_btn.clicked.connect(self._select_image)
        btn_col.addWidget(self.img_select_btn)
        
        self.img_remove_btn = QPushButton("🗑️  Kaldır")
        self.img_remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.img_remove_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #FF3D57; border: none;
                font-size: 12px; font-weight: 600; padding: 6px;
            }
            QPushButton:hover { color: #FF667A; }
        """)
        self.img_remove_btn.clicked.connect(self._remove_image)
        self.img_remove_btn.hide()
        btn_col.addWidget(self.img_remove_btn)
        btn_col.addStretch()
        
        img_ly.addLayout(btn_col)
        
        self.img_preview = QLabel()
        self.img_preview.setFixedSize(220, 110)
        self.img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_preview.setText("Grafik eklenmedi")
        self.img_preview.setStyleSheet(
            "color: #8B949E; font-size: 11px; "
            "border: 1px dashed #30363D; border-radius: 8px; "
            "background-color: #161B22;"
        )
        img_ly.addWidget(self.img_preview)
        
        # Click preview to view full screen
        self.img_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        
        outer.addWidget(img_box)

        # ── Connections ───────────────────────────────────────
        self.size_type_combo.currentIndexChanged.connect(self._on_size_type_changed)

        return wrap

    # ── PnL display area ────────────────────────────────────
    def _make_pnl_area(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet("background-color: #0D1117;")
        ly = QHBoxLayout(bar)
        ly.setContentsMargins(24, 4, 24, 12)
        ly.setSpacing(20)

        LS = "color: #8B949E; font-size: 11px; font-weight: 600; background: transparent;"

        # ── PNL TUTARI ────────────────────────────────────────
        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        pnl_cap = QLabel("PNL TUTARI ($) *")
        pnl_cap.setStyleSheet(LS)

        self.pnl_spin = self._spin(prefix="$ ", dec=2, neg=True)
        self.pnl_spin.setFixedWidth(140)
        self.pnl_spin.valueChanged.connect(self._update_pnl_ratio)

        info_col.addWidget(pnl_cap)
        info_col.addWidget(self.pnl_spin)

        # ── KOMİSYON / FEE ───────────────────────────────────
        fee_col = QVBoxLayout()
        fee_col.setSpacing(4)
        fee_cap = QLabel("KOMİSYON / FEE ($)")
        fee_cap.setStyleSheet(LS)

        self.fee_spin = self._spin(prefix="$ ", dec=4, neg=False, max_v=999_999)
        self.fee_spin.setFixedWidth(140)
        self.fee_spin.setToolTip("İşlem komisyonu. Net PnL = PnL − Fee olarak hesaplanır.")
        self.fee_spin.valueChanged.connect(self._update_pnl_ratio)

        fee_col.addWidget(fee_cap)
        fee_col.addWidget(self.fee_spin)

        # ── NET PNL (read-only) ────────────────────────────
        net_col = QVBoxLayout()
        net_col.setSpacing(4)
        net_cap = QLabel("NET PNL ($)")
        net_cap.setStyleSheet(LS)

        self.net_pnl_display = QLabel("$0.00")
        self.net_pnl_display.setStyleSheet(
            "font-size: 14px; font-weight: 800; color: #8B949E;"
            "background-color: #1C2128; border: 1px solid #30363D;"
            "border-radius: 6px; padding: 7px 12px;"
        )
        net_col.addWidget(net_cap)
        net_col.addWidget(self.net_pnl_display)

        # ── BAKİYEYE ORANI ────────────────────────────────
        ratio_col = QVBoxLayout()
        ratio_col.setSpacing(4)
        ratio_cap = QLabel("BAKİYEYE ORANI")
        ratio_cap.setStyleSheet(LS)

        self.pnl_ratio_display = QLabel("%0.00")
        self._set_ratio_display(0.0)

        ratio_col.addWidget(ratio_cap)
        ratio_col.addWidget(self.pnl_ratio_display)

        ly.addLayout(info_col)
        ly.addLayout(fee_col)
        ly.addLayout(net_col)
        ly.addLayout(ratio_col)
        ly.addStretch()
        return bar

    def _update_pnl_ratio(self):
        gross = self.pnl_spin.value()
        fee = self.fee_spin.value()
        net = gross - fee
        # Update net PnL display
        sign = "+" if net > 0 else ""
        if net > 0:
            net_color = "#00C853"
        elif net < 0:
            net_color = "#FF3D57"
        else:
            net_color = "#8B949E"
        self.net_pnl_display.setText(f"{sign}${net:,.2f}")
        self.net_pnl_display.setStyleSheet(
            f"font-size: 14px; font-weight: 800; color: {net_color};"
            "background-color: #1C2128; border: 1px solid #30363D;"
            "border-radius: 6px; padding: 7px 12px;"
        )
        balance = self._balance
        if balance > 0:
            ratio = (net / balance) * 100
        else:
            ratio = 0.0
        self._set_ratio_display(ratio)

    def _set_ratio_display(self, ratio: float):
        if ratio > 0:
            color, bg, border = "#00C853", "rgba(0,200,83,0.08)", "#00C853"
        elif ratio < 0:
            color, bg, border = "#FF3D57", "rgba(255,61,87,0.08)", "#FF3D57"
        else:
            color, bg, border = "#8B949E", "#1C2128", "#30363D"
        sign = "+" if ratio > 0 else ""
        self.pnl_ratio_display.setText(f"%{sign}{ratio:,.2f}")
        self.pnl_ratio_display.setStyleSheet(
            self._PNL_DISPLAY_SS.format(color=color, bg=bg, border=border)
        )

    # ── Button bar ────────────────────────────────────────────
    def _make_btn_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet("background-color: #161B22; border-top: 1px solid #21262D;")
        ly = QHBoxLayout(bar)
        ly.setContentsMargins(24, 12, 24, 12)
        ly.setSpacing(10)
        ly.addStretch()

        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.setFixedHeight(38)
        self.cancel_btn.setStyleSheet(self._CANCEL_SS)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.setDefault(False)
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("💾  Kaydet")
        self.save_btn.setFixedHeight(38)
        self.save_btn.setStyleSheet(self._SAVE_SS)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setAutoDefault(False)
        self.save_btn.setDefault(False)
        self.save_btn.clicked.connect(self._on_save)

        ly.addWidget(self.cancel_btn)
        ly.addWidget(self.save_btn)
        return bar

    # ═══════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════
    def _spin(self, prefix="", dec=2, max_v=9_999_999, neg=False) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(-max_v if neg else 0.0, max_v)
        s.setDecimals(dec)
        s.setKeyboardTracking(False)
        s.setStyleSheet(self._SPIN_SS)
        s.setFixedHeight(36)
        if prefix:
            s.setPrefix(prefix)
        return s



    # ═══════════════════════════════════════════════════════════
    #  SLOTS / LOGIC
    # ═══════════════════════════════════════════════════════════
    def _on_size_type_changed(self, index: int):
        self.qty_spin.setVisible(index == 0)
        self.usd_spin.setVisible(index == 1)
        self.margin_spin.setVisible(index == 2)

    def _effective_qty(self) -> float:
        entry = self.entry_spin.value()
        if entry <= 0:
            return 0.0

        idx = self.size_type_combo.currentIndex()
        leverage = max(1, self.leverage_spin.value())
        if idx == 0:  # ADET: represents margin units
            return self.qty_spin.value() * leverage
        elif idx == 1:  # USD Değeri (Notional)
            return self.usd_spin.value() / entry
        else:  # Marjin USD
            return (self.margin_spin.value() * leverage) / entry

    # ── Populate (edit mode) ──────────────────────────────────
    def _populate(self, d: dict):
        self._block_size_recalc = True

        self.symbol_edit.setText(d.get("symbol", ""))
        idx = self.dir_combo.findText(d.get("direction", "LONG"))
        if idx >= 0:
            self.dir_combo.setCurrentIndex(idx)

        self.leverage_spin.setValue(int(d.get("leverage", 1)))
        self.entry_spin.setValue(d.get("entry_price", 0.0))
        self.sl_spin.setValue(d.get("sl_price",    0.0))
        self.tp_spin.setValue(d.get("tp_price",    0.0))
        self.exit_spin.setValue(d.get("exit_price", 0.0))

        # Restore size
        size_type = d.get("size_type", "ADET")
        if size_type == "USD":
            self.size_type_combo.setCurrentIndex(1)
            self.usd_spin.setValue(d.get("size_value", 0.0))
        elif size_type == "MARGIN":
            self.size_type_combo.setCurrentIndex(2)
            self.margin_spin.setValue(d.get("size_value", 0.0))
        else:
            self.size_type_combo.setCurrentIndex(0)
            self.qty_spin.setValue(d.get("quantity", 0.0))

        # Restore image
        img_filename = d.get("img_path", "")
        if img_filename:
            full_path = os.path.join(db_manager.SCREENSHOTS_DIR, img_filename)
            if os.path.exists(full_path):
                self._set_image(full_path)
            else:
                self._remove_image()
        else:
            self._remove_image()

        self.notes_edit.setPlainText(d.get("notes", ""))
        self.pnl_spin.setValue(d.get("pnl", 0.0))
        self.fee_spin.setValue(d.get("fee", 0.0))
        self._update_pnl_ratio()
        self._block_size_recalc = False

    # ── Image helpers ─────────────────────────────────────────
    def _select_image(self):
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Grafik Seç", "", "Resim Dosyaları (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if file_path:
            self._set_image(file_path)

    def _set_image(self, file_path: str):
        from PyQt6.QtGui import QPixmap
        self.img_path = file_path
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                220, 110,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.img_preview.setPixmap(scaled)
            self.img_preview.setStyleSheet("border: 1px solid #30363D; border-radius: 8px;")
            self.img_remove_btn.show()
            self.img_select_btn.setText("🖼️  Grafik Değiştir")
        else:
            self.img_preview.setText("Resim yüklenemedi")
            self.img_preview.setStyleSheet("color: #FF3D57; font-size: 11px;")
            self.img_remove_btn.hide()

    def _remove_image(self):
        self.img_path = ""
        self.img_preview.clear()
        self.img_preview.setText("Grafik eklenmedi")
        self.img_preview.setStyleSheet(
            "color: #8B949E; font-size: 11px; "
            "border: 1px dashed #30363D; border-radius: 8px; "
            "background-color: #161B22;"
        )
        self.img_remove_btn.hide()
        self.img_select_btn.setText("🖼️  Grafik Ekle")

    def _view_full_image(self, event):
        if not self.img_path or not os.path.exists(self.img_path):
            return
        
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PyQt6.QtGui import QPixmap
        
        viewer = QDialog(self)
        viewer.setWindowTitle("Grafik Görünümü")
        viewer.setStyleSheet("background-color: #0D1117;")
        
        v_ly = QVBoxLayout(viewer)
        v_ly.setContentsMargins(10, 10, 10, 10)
        
        lbl = QLabel()
        pixmap = QPixmap(self.img_path)
        
        scaled = pixmap.scaled(
            1200, 800,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        lbl.setPixmap(scaled)
        v_ly.addWidget(lbl)
        
        viewer.setLayout(v_ly)
        viewer.exec()

    # ── Save ─────────────────────────────────────────────────
    def _on_save(self):
        symbol = self.symbol_edit.text().strip().upper()
        if not symbol:
            QMessageBox.warning(self, "Eksik Bilgi", "Sembol alanı boş bırakılamaz.")
            self.symbol_edit.setFocus()
            return
        if self.entry_spin.value() <= 0:
            QMessageBox.warning(self, "Eksik Bilgi", "Entry fiyatı girilmeden işlem kaydedilemez.")
            self.entry_spin.setFocus()
            return

        entry = self.entry_spin.value()
        exit_p = self.exit_spin.value()

        # Determine size
        idx = self.size_type_combo.currentIndex()
        if idx == 0:
            size_type  = "ADET"
            size_value = self.qty_spin.value()
            quantity   = size_value
        elif idx == 1:
            size_type  = "USD"
            size_value = self.usd_spin.value()
            quantity   = (size_value / entry) if entry > 0 else 0.0
        else:
            size_type  = "MARGIN"
            size_value = self.margin_spin.value()
            leverage   = max(1, self.leverage_spin.value())
            quantity   = (size_value * leverage / entry) if entry > 0 else 0.0

        # PnL — entered manually; fee deducted to get net
        pnl = round(self.pnl_spin.value(), 2)
        fee = round(self.fee_spin.value(), 4)

        # Copy image if selected
        copied_path = ""
        if self.img_path:
            if os.path.exists(self.img_path):
                import shutil
                screenshots_dir = db_manager.SCREENSHOTS_DIR
                
                # Check if already in screenshots folder
                if os.path.abspath(os.path.dirname(self.img_path)) == os.path.abspath(screenshots_dir):
                    # Check if it was pasted from clipboard (starts with temp)
                    if os.path.basename(self.img_path).startswith("temp_paste") or "temp" in os.path.basename(self.img_path):
                        ext = os.path.splitext(self.img_path)[1] or ".png"
                        new_filename = f"chart_{self.trade_date}_{datetime.now().strftime('%H%M%S')}_{os.urandom(4).hex()}{ext}"
                        dest = os.path.join(screenshots_dir, new_filename)
                        try:
                            shutil.move(self.img_path, dest)
                            copied_path = new_filename
                        except Exception:
                            copied_path = os.path.basename(self.img_path)
                    else:
                        copied_path = os.path.basename(self.img_path)
                else:
                    ext = os.path.splitext(self.img_path)[1] or ".png"
                    new_filename = f"chart_{self.trade_date}_{datetime.now().strftime('%H%M%S')}_{os.urandom(4).hex()}{ext}"
                    dest = os.path.join(screenshots_dir, new_filename)
                    try:
                        shutil.copy2(self.img_path, dest)
                        copied_path = new_filename
                    except Exception as e:
                        print("Failed to copy screenshot:", e)
                        copied_path = ""

        self.result_data = {
            "symbol":      symbol,
            "direction":   self.dir_combo.currentText(),
            "entry_price": entry,
            "exit_price":  exit_p,
            "quantity":    quantity,
            "tp_price":    self.tp_spin.value(),
            "sl_price":    self.sl_spin.value(),
            "pnl":         pnl,
            "fee":         fee,
            "notes":       self.notes_edit.toPlainText().strip(),
            "size_type":   size_type,
            "size_value":  size_value,
            "risk_pct":    0.0,
            "leverage":    self.leverage_spin.value(),
            "img_path":    copied_path,
        }
        self.accept()

    # ── Key press block ───────────────────────────────────────
    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.save_btn.hasFocus():
                self._on_save()
            return  # Do nothing otherwise
        if key == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)

    # ── Clipboard Paste Support ──────────────────────────────
    def _paste_from_clipboard(self):
        from PyQt6.QtWidgets import QApplication
        import tempfile
        import os
        from datetime import datetime
        
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        if not image.isNull():
            screenshots_dir = db_manager.SCREENSHOTS_DIR
            
            # Generate a temporary path inside screenshots folder
            temp_file = tempfile.NamedTemporaryFile(
                prefix="temp_paste_", suffix=".png", dir=screenshots_dir, delete=False
            )
            temp_path = temp_file.name
            temp_file.close()
            
            if image.save(temp_path, "PNG"):
                self._set_image(temp_path)
            else:
                QMessageBox.warning(self, "Hata", "Panodaki görsel kaydedilemedi.")

    def eventFilter(self, obj, event) -> bool:
        # Check mouse press on preview label
        if obj is getattr(self, "img_preview", None) and event.type() == QEvent.Type.MouseButtonPress:
            self._view_full_image(event)
            return True

        if event.type() == QEvent.Type.KeyPress:
            key_event = event
            # Intercept Ctrl+V
            if key_event.modifiers() == Qt.KeyboardModifier.ControlModifier and key_event.key() == Qt.Key.Key_V:
                from PyQt6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                mime_data = clipboard.mimeData()
                if mime_data.hasImage():
                    self._paste_from_clipboard()
                    return True # Handled (block event propagation)
        return super().eventFilter(obj, event)






class DayDetailDialog(QDialog):
    """
    Main dialog that opens when a calendar day cell is clicked.
    Shows the list of trades for that day and allows CRUD operations.
    """

    trades_changed = pyqtSignal()  # emitted when trades are added/modified/deleted

    def __init__(self, trade_date: str, parent=None):
        super().__init__(parent)
        self.trade_date = trade_date
        self.setObjectName("TradeDialog")
        self.setMinimumSize(1000, 620)
        self.setModal(True)

        # Parse for display
        from datetime import datetime
        try:
            dt = datetime.strptime(trade_date, "%Y-%m-%d")
            self._date_display = dt.strftime("%d %B %Y")
            TURKISH_MONTHS = {
                "January": "Ocak", "February": "Şubat", "March": "Mart",
                "April": "Nisan", "May": "Mayıs", "June": "Haziran",
                "July": "Temmuz", "August": "Ağustos", "September": "Eylül",
                "October": "Ekim", "November": "Kasım", "December": "Aralık",
            }
            for en, tr in TURKISH_MONTHS.items():
                self._date_display = self._date_display.replace(en, tr)
        except Exception:
            self._date_display = trade_date

        self.setWindowTitle(f"📅  {self._date_display}")
        self._build_ui()
        self._refresh_table()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────
        header = QWidget()
        header.setStyleSheet("background-color: #161B22; border-bottom: 1px solid #21262D;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 18, 28, 18)
        header_layout.setSpacing(12)

        # Title block (left side of header)
        title_block = QVBoxLayout()
        title_block.setSpacing(3)
        title = QLabel(f"📅  {self._date_display}")
        title.setStyleSheet("color: #E6EDF3; font-size: 18px; font-weight: 700; background: transparent;")
        subtitle = QLabel("İşlem kayıtlarını görüntüleyin, ekleyin ve düzenleyin.")
        subtitle.setStyleSheet("color: #8B949E; font-size: 11px; background: transparent;")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        header_layout.addLayout(title_block)
        header_layout.addStretch()

        # ── Add Trade Button (in header, always visible) ───────
        add_btn = QPushButton("＋  Yeni İşlem Ekle")
        add_btn.setFixedHeight(38)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #00D4FF;
                color: #0D1117;
                border: none;
                border-radius: 8px;
                padding: 0px 20px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #33DDFF;
            }
            QPushButton:pressed {
                background-color: #00AACC;
            }
        """)
        add_btn.clicked.connect(self._on_add_trade)
        header_layout.addWidget(add_btn)

        # Close button
        close_btn = QPushButton("✕  Kapat")
        close_btn.setFixedHeight(38)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #8B949E;
                border: none;
                border-radius: 8px;
                padding: 0px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #30363D;
                color: #E6EDF3;
            }
        """)
        close_btn.clicked.connect(self.accept)
        header_layout.addWidget(close_btn)

        root.addWidget(header)

        # ── PnL summary bar ───────────────────────────────────
        self.pnl_bar = QWidget()
        self.pnl_bar.setStyleSheet("""
            QWidget {
                background-color: #1C2128;
                border-bottom: 1px solid #21262D;
            }
        """)
        pnl_layout = QHBoxLayout(self.pnl_bar)
        pnl_layout.setContentsMargins(28, 14, 28, 14)
        pnl_layout.setSpacing(0)

        pnl_info = QVBoxLayout()
        pnl_info.setSpacing(2)
        pnl_lbl = QLabel("Günlük Toplam PnL")
        pnl_lbl.setStyleSheet("color: #8B949E; font-size: 11px; background: transparent;")
        self.pnl_value_lbl = QLabel("$0.00")
        self.pnl_value_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #E6EDF3; background: transparent;")
        pnl_info.addWidget(pnl_lbl)
        pnl_info.addWidget(self.pnl_value_lbl)
        pnl_layout.addLayout(pnl_info)

        pnl_layout.addStretch()

        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(32)

        self.trade_count_lbl  = self._stat_widget("İşlem Sayısı", "0")
        self.win_count_lbl    = self._stat_widget("Kazanan", "0")
        self.loss_count_lbl   = self._stat_widget("Kaybeden", "0")
        self.winrate_lbl      = self._stat_widget("Win Rate", "0%")

        for w in [self.trade_count_lbl, self.win_count_lbl, self.loss_count_lbl, self.winrate_lbl]:
            stats_grid.addWidget(w)
        pnl_layout.addLayout(stats_grid)

        root.addWidget(self.pnl_bar)

        # ── Trade Table ───────────────────────────────────────
        table_container = QWidget()
        table_container.setStyleSheet("background: transparent;")
        tc_layout = QVBoxLayout(table_container)
        tc_layout.setContentsMargins(28, 0, 28, 20)

        self.table = QTableWidget()
        self.table.setObjectName("TradeTable")
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setColumnHidden(COL_ID, True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._on_edit_selected)

        # Column widths
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(COL_SYMBOL, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(COL_SYMBOL, 120)
        hdr.setSectionResizeMode(COL_DIR, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(COL_DIR, 80)
        for col in [COL_ENTRY, COL_EXIT, COL_QTY, COL_TP, COL_SL, COL_PNL]:
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(col, 90)
        hdr.setSectionResizeMode(COL_IMG, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(COL_IMG, 70)
        hdr.setSectionResizeMode(COL_NOTES, QHeaderView.ResizeMode.Stretch)

        tc_layout.addWidget(self.table)
        root.addWidget(table_container)

    def _stat_widget(self, label: str, value: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        ly = QVBoxLayout(w)
        ly.setContentsMargins(0, 0, 0, 0)
        ly.setSpacing(2)
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #8B949E; font-size: 11px; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val = QLabel(value)
        val.setStyleSheet("font-size: 16px; font-weight: 700; color: #E6EDF3; background: transparent;")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ly.addWidget(lbl)
        ly.addWidget(val)
        # store ref to value label inside container for updates
        w._value_label = val  # type: ignore
        return w

    def _refresh_table(self):
        trades = db_manager.get_trades_for_date(self.trade_date)
        self.table.setRowCount(0)

        total_pnl = 0.0
        wins = 0
        losses = 0

        for trade in trades:
            row = self.table.rowCount()
            self.table.insertRow(row)

            def cell(text, align=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft):
                item = QTableWidgetItem(str(text))
                item.setTextAlignment(align)
                return item

            center = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter

            self.table.setItem(row, COL_ID,     cell(str(trade["id"])))
            self.table.setItem(row, COL_SYMBOL, cell(trade["symbol"]))

            dir_item = cell(trade["direction"], center)
            if trade["direction"] == "LONG":
                dir_item.setForeground(QBrush(QColor("#00C853")))
            else:
                dir_item.setForeground(QBrush(QColor("#FF3D57")))
            self.table.setItem(row, COL_DIR, dir_item)

            self.table.setItem(row, COL_ENTRY, cell(f"${trade['entry_price']:,.4f}", center))
            self.table.setItem(row, COL_EXIT,  cell(f"${trade['exit_price']:,.4f}", center))
            self.table.setItem(row, COL_QTY,   cell(f"{trade['quantity']:,.4f}", center))
            self.table.setItem(row, COL_TP,    cell(f"${trade['tp_price']:,.4f}", center))
            self.table.setItem(row, COL_SL,    cell(f"${trade['sl_price']:,.4f}", center))

            pnl = trade["pnl"] - trade.get("fee", 0.0)
            total_pnl += pnl
            pnl_item = cell(f"${pnl:+,.2f}", center)
            if pnl > 0:
                pnl_item.setForeground(QBrush(QColor("#00C853")))
                wins += 1
            elif pnl < 0:
                pnl_item.setForeground(QBrush(QColor("#FF3D57")))
                losses += 1
            self.table.setItem(row, COL_PNL, pnl_item)

            
            # Grafik (Screenshot) column
            has_img = bool(trade.get("img_path", ""))
            self.table.setItem(row, COL_IMG, cell("🖼️" if has_img else "-", center))
            
            self.table.setItem(row, COL_NOTES, cell(trade.get("notes", "")))

            self.table.setRowHeight(row, 40)

        # Update summary
        self._update_pnl_bar(total_pnl, len(trades), wins, losses)

    def _update_pnl_bar(self, total_pnl: float, count: int, wins: int, losses: int):
        color = "#00C853" if total_pnl > 0 else ("#FF3D57" if total_pnl < 0 else "#E6EDF3")
        self.pnl_value_lbl.setText(f"${total_pnl:+,.2f}")
        self.pnl_value_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {color};")

        winrate = (wins / count * 100) if count > 0 else 0
        self.trade_count_lbl._value_label.setText(str(count))   # type: ignore
        self.win_count_lbl._value_label.setText(str(wins))       # type: ignore
        self.loss_count_lbl._value_label.setText(str(losses))    # type: ignore
        self.winrate_lbl._value_label.setText(f"{winrate:.0f}%") # type: ignore

    def _on_add_trade(self):
        dlg = TradeFormDialog(self.trade_date, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result_data:
            d = dlg.result_data
            db_manager.add_trade(
                trade_date=self.trade_date,
                symbol=d["symbol"],
                direction=d["direction"],
                entry_price=d["entry_price"],
                exit_price=d["exit_price"],
                quantity=d["quantity"],
                tp_price=d["tp_price"],
                sl_price=d["sl_price"],
                pnl=d["pnl"],
                notes=d["notes"],
                size_type=d.get("size_type", "ADET"),
                size_value=d.get("size_value", 0.0),
                risk_pct=d.get("risk_pct", 0.0),
                leverage=d.get("leverage", 1),
                img_path=d.get("img_path", ""),
                fee=d.get("fee", 0.0),
            )
            self._refresh_table()
            self.trades_changed.emit()

    def _on_edit_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        trade_id_item = self.table.item(row, COL_ID)
        if not trade_id_item:
            return
        trade_id = int(trade_id_item.text())
        trades = db_manager.get_trades_for_date(self.trade_date)
        trade_data = next((t for t in trades if t["id"] == trade_id), None)
        if not trade_data:
            return

        dlg = TradeFormDialog(self.trade_date, trade_data=trade_data, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result_data:
            d = dlg.result_data
            db_manager.update_trade(
                trade_id=trade_id,
                symbol=d["symbol"],
                direction=d["direction"],
                entry_price=d["entry_price"],
                exit_price=d["exit_price"],
                quantity=d["quantity"],
                tp_price=d["tp_price"],
                sl_price=d["sl_price"],
                pnl=d["pnl"],
                notes=d["notes"],
                size_type=d.get("size_type", "ADET"),
                size_value=d.get("size_value", 0.0),
                risk_pct=d.get("risk_pct", 0.0),
                leverage=d.get("leverage", 1),
                img_path=d.get("img_path", ""),
                fee=d.get("fee", 0.0),
            )
            self._refresh_table()
            self.trades_changed.emit()

    def _show_context_menu(self, pos):
        from PyQt6.QtWidgets import QMenu
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        menu = QMenu(self)
        edit_action  = menu.addAction("✏️  Düzenle")
        copy_action  = menu.addAction("📋  Kopyala")
        menu.addSeparator()
        del_action   = menu.addAction("🗑️  Sil")

        action = menu.exec(self.table.viewport().mapToGlobal(pos))

        if action == edit_action:
            self.table.setCurrentCell(row, 0)
            self._on_edit_selected()
        elif action == copy_action:
            trade_id_item = self.table.item(row, COL_ID)
            if not trade_id_item:
                return
            trade_id = int(trade_id_item.text())
            trades = db_manager.get_trades_for_date(self.trade_date)
            trade_data = next((t for t in trades if t["id"] == trade_id), None)
            if not trade_data:
                return
            
            # Copy screenshot file if it exists
            new_img_path = ""
            old_img_name = trade_data.get("img_path", "")
            if old_img_name:
                import shutil
                from datetime import datetime
                screenshots_dir = db_manager.SCREENSHOTS_DIR
                old_full_path = os.path.join(screenshots_dir, old_img_name)
                if os.path.exists(old_full_path):
                    ext = os.path.splitext(old_img_name)[1] or ".png"
                    new_img_name = f"chart_{self.trade_date}_{datetime.now().strftime('%H%M%S')}_{os.urandom(4).hex()}{ext}"
                    new_full_path = os.path.join(screenshots_dir, new_img_name)
                    try:
                        shutil.copy(old_full_path, new_full_path)
                        new_img_path = new_img_name
                    except Exception:
                        pass
            
            # Save cloned trade to database
            db_manager.add_trade(
                trade_date=self.trade_date,
                symbol=trade_data["symbol"],
                direction=trade_data["direction"],
                entry_price=trade_data["entry_price"],
                exit_price=trade_data["exit_price"],
                quantity=trade_data["quantity"],
                tp_price=trade_data["tp_price"],
                sl_price=trade_data["sl_price"],
                pnl=trade_data["pnl"],
                notes=trade_data.get("notes", "") + " (Kopya)",
                size_type=trade_data.get("size_type", "ADET"),
                size_value=trade_data.get("size_value", 0.0),
                risk_pct=trade_data.get("risk_pct", 0.0),
                leverage=trade_data.get("leverage", 1),
                img_path=new_img_path,
                fee=trade_data.get("fee", 0.0),
            )
            self._refresh_table()
            self.trades_changed.emit()
        elif action == del_action:
            trade_id_item = self.table.item(row, COL_ID)
            if not trade_id_item:
                return
            trade_id = int(trade_id_item.text())
            symbol_item = self.table.item(row, COL_SYMBOL)
            symbol = symbol_item.text() if symbol_item else "?"
            reply = QMessageBox.question(
                self,
                "Silmeyi Onayla",
                f"'{symbol}' işlemini silmek istediğinize emin misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                db_manager.delete_trade(trade_id)
                self._refresh_table()
                self.trades_changed.emit()
