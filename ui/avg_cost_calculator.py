from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QFrame, QGridLayout
)
from PyQt6.QtCore import Qt


class AvgCostCalculator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AvgCostCalculator")
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header
        header = QLabel("Maliyet Ortalama Hesaplayıcı")
        header.setStyleSheet("color: #E6EDF3; font-size: 28px; font-weight: 800;")
        layout.addWidget(header)

        sub_header = QLabel("Mevcut pozisyonunuza yeni ekleme yaptığınızda oluşacak yeni maliyetinizi hesaplayın.")
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
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)

        input_style = """
            QLineEdit {
                background-color: #161B22;
                color: #E6EDF3;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #4863F7;
            }
        """
        self.setStyleSheet(self.styleSheet() + input_style)

        # Section 1: Alım (Mevcut Durum)
        sec1_lbl = QLabel("1. ALIM (MEVCUT DURUM)")
        sec1_lbl.setStyleSheet("color: #4863F7; font-size: 14px; font-weight: 800; border: none; background: transparent;")
        left_layout.addWidget(sec1_lbl)

        grid1 = QGridLayout()
        grid1.setSpacing(15)
        grid1.addWidget(self._create_label("Miktar (Adet/Coin)"), 0, 0)
        self.le_qty1 = QLineEdit()
        self.le_qty1.setPlaceholderText("örn. 25.5")
        grid1.addWidget(self.le_qty1, 1, 0)

        grid1.addWidget(self._create_label("Alış Fiyatı"), 0, 1)
        self.le_price1 = QLineEdit()
        self.le_price1.setPlaceholderText("örn. 152.5")
        grid1.addWidget(self.le_price1, 1, 1)
        left_layout.addLayout(grid1)

        left_layout.addSpacing(10)

        # Section 2: Alım (Yeni Ekleme)
        sec2_lbl = QLabel("2. ALIM (YENİ EKLEME)")
        sec2_lbl.setStyleSheet("color: #4863F7; font-size: 14px; font-weight: 800; border: none; background: transparent;")
        left_layout.addWidget(sec2_lbl)

        grid2 = QGridLayout()
        grid2.setSpacing(15)
        grid2.addWidget(self._create_label("Yatırılacak Tutar ($)"), 0, 0)
        self.le_budget2 = QLineEdit()
        self.le_budget2.setPlaceholderText("örn. 6000")
        grid2.addWidget(self.le_budget2, 1, 0)

        grid2.addWidget(self._create_label("Güncel Fiyat"), 0, 1)
        self.le_price2 = QLineEdit()
        self.le_price2.setPlaceholderText("örn. 117.3")
        grid2.addWidget(self.le_price2, 1, 1)
        left_layout.addLayout(grid2)

        left_layout.addStretch()
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

        self.lbl_cost1 = self._create_result_box("1. Alım Toplam Maliyet", "$0.00")
        self.lbl_qty2 = self._create_result_box("2. Alımdan Gelecek Miktar", "0.0000")
        self.lbl_total_qty = self._create_result_box("Toplam Yeni Miktar", "0.0000")
        self.lbl_avg = self._create_result_box("Yeni Ortalama Maliyet", "$0.00", color="#00C853")

        right_layout.addWidget(self.lbl_cost1)
        right_layout.addWidget(self.lbl_qty2)
        right_layout.addWidget(self.lbl_total_qty)
        right_layout.addWidget(self.lbl_avg)
        right_layout.addStretch()

        c_layout.addWidget(right_widget, 1)

        layout.addWidget(container)
        layout.addStretch()

    def _create_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #8B949E; font-size: 13px; border: none; background: transparent;")
        return lbl

    def _create_result_box(self, title, default_val, color="#E6EDF3"):
        w = QWidget()
        w.setStyleSheet("background: transparent; border: none;")
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #8B949E; font-size: 14px; border: none; font-weight: 600;")
        v_lbl = QLabel(default_val)
        v_lbl.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 800; border: none;")
        l.addWidget(t_lbl)
        l.addWidget(v_lbl)
        w.val_lbl = v_lbl
        return w

    def _connect_signals(self):
        self.le_qty1.textChanged.connect(self._calculate)
        self.le_price1.textChanged.connect(self._calculate)
        self.le_budget2.textChanged.connect(self._calculate)
        self.le_price2.textChanged.connect(self._calculate)

    def _get_float(self, le):
        try:
            return float(le.text().replace(",", "."))
        except ValueError:
            return 0.0

    def _calculate(self, *args):
        qty1 = self._get_float(self.le_qty1)
        price1 = self._get_float(self.le_price1)
        budget2 = self._get_float(self.le_budget2)
        price2 = self._get_float(self.le_price2)

        # Calculate
        total_cost1 = qty1 * price1
        qty2 = 0.0
        if price2 > 0:
            qty2 = budget2 / price2
            
        total_qty = qty1 + qty2
        total_budget = total_cost1 + budget2
        
        final_avg = 0.0
        if total_qty > 0:
            final_avg = total_budget / total_qty

        # Display
        self.lbl_cost1.val_lbl.setText(f"${total_cost1:,.2f}")
        self.lbl_qty2.val_lbl.setText(f"{qty2:,.4f}")
        self.lbl_total_qty.val_lbl.setText(f"{total_qty:,.4f}")
        self.lbl_avg.val_lbl.setText(f"${final_avg:,.4f}")
