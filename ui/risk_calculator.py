from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QFrame, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator

from database import db_manager


class RiskCalculator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RiskCalculator")
        self._build_ui()
        self._connect_signals()
        self.update_balance()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header
        header = QLabel("Risk Hesaplayıcı")
        header.setStyleSheet("color: #E6EDF3; font-size: 28px; font-weight: 800;")
        layout.addWidget(header)

        sub_header = QLabel("İşleme girmeden önce riskinizi ve pozisyon büyüklüğünüzü hesaplayın.")
        sub_header.setStyleSheet("color: #8B949E; font-size: 14px;")
        layout.addWidget(sub_header)

        layout.addSpacing(10)

        # Container
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #0D1117;
                border: 1px solid #30363D;
                border-radius: 12px;
            }
        """)
        c_layout = QHBoxLayout(container)
        c_layout.setContentsMargins(30, 30, 30, 30)
        c_layout.setSpacing(40)

        # LEFT: Inputs
        left_widget = QWidget()
        left_widget.setStyleSheet("background: transparent;")
        left_layout = QGridLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setVerticalSpacing(20)
        left_layout.setHorizontalSpacing(15)

        input_style = """
            QLineEdit, QComboBox {
                background-color: #161B22;
                color: #E6EDF3;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #00D4FF;
            }
        """
        self.setStyleSheet(self.styleSheet() + input_style)

        # Current Balance
        self.lbl_balance = QLabel("Güncel Bakiye: $0.00")
        self.lbl_balance.setStyleSheet("color: #00D4FF; font-size: 14px; font-weight: bold; border: none; background: transparent;")
        left_layout.addWidget(self.lbl_balance, 0, 0, 1, 2)

        left_layout.addWidget(self._create_label("İşlem Yönü"), 1, 0)
        self.cb_direction = QComboBox()
        self.cb_direction.addItems(["Long", "Short"])
        dropdown_style = "QComboBox QAbstractItemView { color: #E6EDF3; background-color: #161B22; selection-background-color: #30363D; outline: none; }"
        self.cb_direction.setStyleSheet(f"QComboBox {{ color: #00C853; background-color: #161B22; border: 1px solid #30363D; border-radius: 6px; padding: 8px 12px; font-size: 14px; }} {dropdown_style}")
        self.cb_direction.currentTextChanged.connect(self._on_direction_change)
        left_layout.addWidget(self.cb_direction, 1, 1)

        left_layout.addWidget(self._create_label("Giriş Fiyatı"), 2, 0)
        self.le_entry = QLineEdit()
        self.le_entry.setPlaceholderText("örn. 65000")
        left_layout.addWidget(self.le_entry, 2, 1)

        left_layout.addWidget(self._create_label("Zarar Kes (Stoploss)"), 3, 0)
        stop_layout = QHBoxLayout()
        stop_layout.setContentsMargins(0, 0, 0, 0)
        stop_layout.setSpacing(10)
        
        self.cb_stop_type = QComboBox()
        self.cb_stop_type.addItems(["Fiyat", "%"])
        self.cb_stop_type.setFixedWidth(70)
        self.cb_stop_type.setStyleSheet("QComboBox { background-color: #161B22; color: #E6EDF3; border: 1px solid #30363D; border-radius: 6px; padding: 4px 8px; font-size: 14px; } QComboBox QAbstractItemView { color: #E6EDF3; background-color: #161B22; selection-background-color: #30363D; outline: none; }")
        self.cb_stop_type.currentTextChanged.connect(self._on_stop_type_change)
        
        self.le_stop = QLineEdit()
        self.le_stop.setPlaceholderText("örn. 64000")
        
        stop_layout.addWidget(self.cb_stop_type)
        stop_layout.addWidget(self.le_stop)
        left_layout.addLayout(stop_layout, 3, 1)

        left_layout.addWidget(self._create_label("Risk Yüzdesi (%)"), 4, 0)
        self.le_risk_pct = QLineEdit()
        self.le_risk_pct.setText("1.0")
        left_layout.addWidget(self.le_risk_pct, 4, 1)

        left_layout.addWidget(self._create_label("Hedef RR (Risk/Ödül)"), 5, 0)
        self.le_rr = QLineEdit()
        self.le_rr.setText("2.0")
        left_layout.addWidget(self.le_rr, 5, 1)

        c_layout.addWidget(left_widget, 1)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setStyleSheet("color: #30363D; background: #30363D;")
        c_layout.addWidget(divider)

        # RIGHT: Outputs
        right_widget = QWidget()
        right_widget.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(25)

        self.lbl_risk_amt = self._create_result_box("Risk Edilen Tutar", "$0.00")
        self.lbl_pos_usdt = self._create_result_box("Pozisyon Büyüklüğü (USDT)", "$0.00")
        self.lbl_pos_coin = self._create_result_box("Pozisyon Büyüklüğü (Adet)", "0.000")
        self.lbl_leverage = self._create_result_box("Önerilen Kaldıraç", "1x")
        self.lbl_tp = self._create_result_box("Hedef Fiyat (TP)", "0.00", color="#00C853")

        right_layout.addWidget(self.lbl_risk_amt)
        right_layout.addWidget(self.lbl_pos_usdt)
        right_layout.addWidget(self.lbl_pos_coin)
        right_layout.addWidget(self.lbl_leverage)
        right_layout.addWidget(self.lbl_tp)
        right_layout.addStretch()

        c_layout.addWidget(right_widget, 1)

        layout.addWidget(container)
        layout.addStretch()

        self._balance = 0.0

    def _create_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #C9D1D9; font-size: 14px; font-weight: 500; border: none; background: transparent;")
        return lbl

    def _create_result_box(self, title, default_val, color="#E6EDF3"):
        w = QWidget()
        w.setStyleSheet("background: transparent; border: none;")
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #8B949E; font-size: 13px; border: none; font-weight: 600;")
        v_lbl = QLabel(default_val)
        v_lbl.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: 800; border: none;")
        l.addWidget(t_lbl)
        l.addWidget(v_lbl)
        w.val_lbl = v_lbl
        return w

    def _on_direction_change(self, text):
        base_style = "background-color: #161B22; border: 1px solid #30363D; border-radius: 6px; padding: 8px 12px; font-size: 14px;"
        dropdown_style = "QComboBox QAbstractItemView { color: #E6EDF3; background-color: #161B22; selection-background-color: #30363D; outline: none; }"
        if text == "Long":
            self.cb_direction.setStyleSheet(f"QComboBox {{ color: #00C853; {base_style} }} {dropdown_style}")
        else:
            self.cb_direction.setStyleSheet(f"QComboBox {{ color: #FF5252; {base_style} }} {dropdown_style}")
        self._calculate()

    def _on_stop_type_change(self, text):
        if text == "%":
            self.le_stop.setPlaceholderText("örn. 1.5")
        else:
            self.le_stop.setPlaceholderText("örn. 64000")
        self._calculate()

    def _connect_signals(self):
        self.le_entry.textChanged.connect(self._calculate)
        self.le_stop.textChanged.connect(self._calculate)
        self.le_risk_pct.textChanged.connect(self._calculate)
        self.le_rr.textChanged.connect(self._calculate)

    def update_balance(self):
        starting_bal_str = db_manager.get_setting("balance", "0")
        try:
            starting_bal = float(starting_bal_str)
        except ValueError:
            starting_bal = 0.0

        stats = db_manager.get_overall_stats()
        total_pnl = stats.get("total_pnl", 0.0) or 0.0
        self._balance = starting_bal + total_pnl
        self.lbl_balance.setText(f"Güncel Bakiye: ${self._balance:,.2f}")
        self._calculate()

    def _get_float(self, le):
        try:
            return float(le.text().replace(",", "."))
        except ValueError:
            return 0.0

    def _calculate(self, *args):
        entry = self._get_float(self.le_entry)
        stop_val = self._get_float(self.le_stop)
        risk_pct = self._get_float(self.le_risk_pct)
        rr = self._get_float(self.le_rr)
        direction = self.cb_direction.currentText()

        if entry <= 0 or stop_val <= 0 or risk_pct <= 0 or rr <= 0 or self._balance <= 0:
            self._reset_results()
            return
            
        is_pct = hasattr(self, "cb_stop_type") and self.cb_stop_type.currentText() == "%"
        if is_pct:
            if direction == "Long":
                stop = entry * (1 - (stop_val / 100.0))
            else:
                stop = entry * (1 + (stop_val / 100.0))
        else:
            stop = stop_val

        # Check validity
        if direction == "Long" and stop >= entry:
            self.lbl_tp.val_lbl.setText("Hata: Stop > Giriş")
            self.lbl_tp.val_lbl.setStyleSheet("color: #FF5252; font-size: 18px; font-weight: 800; border: none;")
            return
        if direction == "Short" and stop <= entry:
            self.lbl_tp.val_lbl.setText("Hata: Stop < Giriş")
            self.lbl_tp.val_lbl.setStyleSheet("color: #FF5252; font-size: 18px; font-weight: 800; border: none;")
            return

        # Calculations
        risk_amount = self._balance * (risk_pct / 100.0)
        
        risk_per_coin = abs(entry - stop)
        if risk_per_coin == 0:
            self._reset_results()
            return

        pos_coin = risk_amount / risk_per_coin
        pos_usdt = pos_coin * entry
        
        # TP Calculation
        if direction == "Long":
            tp = entry + (risk_per_coin * rr)
            self.lbl_tp.val_lbl.setStyleSheet("color: #00C853; font-size: 26px; font-weight: 800; border: none;")
        else:
            tp = entry - (risk_per_coin * rr)
            self.lbl_tp.val_lbl.setStyleSheet("color: #FF5252; font-size: 26px; font-weight: 800; border: none;")

        # Suggested Leverage (based on using entire balance as margin)
        leverage = pos_usdt / self._balance
        
        # Display
        self.lbl_risk_amt.val_lbl.setText(f"${risk_amount:,.2f}")
        self.lbl_pos_usdt.val_lbl.setText(f"${pos_usdt:,.2f}")
        
        if pos_coin < 1:
            self.lbl_pos_coin.val_lbl.setText(f"{pos_coin:,.5f}")
        else:
            self.lbl_pos_coin.val_lbl.setText(f"{pos_coin:,.3f}")
            
        self.lbl_leverage.val_lbl.setText(f"{leverage:.1f}x")
        self.lbl_tp.val_lbl.setText(f"${tp:,.4f}")

    def _reset_results(self):
        self.lbl_risk_amt.val_lbl.setText("$0.00")
        self.lbl_pos_usdt.val_lbl.setText("$0.00")
        self.lbl_pos_coin.val_lbl.setText("0.000")
        self.lbl_leverage.val_lbl.setText("1x")
        self.lbl_tp.val_lbl.setText("0.00")
        self.lbl_tp.val_lbl.setStyleSheet("color: #E6EDF3; font-size: 26px; font-weight: 800; border: none;")
