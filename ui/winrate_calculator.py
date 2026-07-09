from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QFrame, QGridLayout, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor

import random
import math


class SimulationWorker(QThread):
    finished = pyqtSignal(dict, dict)  # (theoretical_results, monte_carlo_results)

    def __init__(self, initial_balance, risk_pct, rr, trades, runs=10000):
        super().__init__()
        self.initial_balance = initial_balance
        self.risk_pct = risk_pct
        self.rr = rr
        self.trades = trades
        self.runs = runs
        self.winrates = [0.33, 0.40, 0.50, 0.60]

    def run(self):
        theoretical = {}
        monte_carlo = {}

        for wr in self.winrates:
            # --- Theoretical ---
            wins_exact = self.trades * wr
            losses_exact = self.trades * (1 - wr)

            # Fixed Risk
            fixed_risk_amount = self.initial_balance * self.risk_pct
            fixed_profit_per_win = fixed_risk_amount * self.rr
            fixed_loss_per_loss = fixed_risk_amount
            
            fixed_net_pnl = (wins_exact * fixed_profit_per_win) - (losses_exact * fixed_loss_per_loss)
            fixed_final_balance = self.initial_balance + fixed_net_pnl
            fixed_net_return_pct = (fixed_net_pnl / self.initial_balance) * 100

            # Compound Risk
            win_mult = 1.0 + (self.risk_pct * self.rr)
            loss_mult = 1.0 - self.risk_pct
            compound_final_balance = self.initial_balance * (win_mult ** wins_exact) * (loss_mult ** losses_exact)
            compound_net_return_pct = ((compound_final_balance - self.initial_balance) / self.initial_balance) * 100

            theoretical[wr] = {
                "wins": round(wins_exact),
                "losses": round(losses_exact),
                "fixed_bal": fixed_final_balance,
                "fixed_ret": fixed_net_return_pct,
                "comp_bal": compound_final_balance,
                "comp_ret": compound_net_return_pct
            }

            # --- Monte Carlo ---
            balances = []
            drawdowns = []

            for _ in range(self.runs):
                bal = self.initial_balance
                peak = bal
                max_dd = 0.0
                
                # Pre-calculate to speed up loop
                for _ in range(int(self.trades)):
                    if random.random() < wr:
                        bal *= win_mult
                    else:
                        bal *= loss_mult
                    
                    if bal > peak:
                        peak = bal
                    
                    dd = (peak - bal) / peak
                    if dd > max_dd:
                        max_dd = dd
                
                balances.append(bal)
                drawdowns.append(max_dd)

            balances.sort()
            avg_bal = sum(balances) / self.runs
            med_bal = balances[self.runs // 2]
            min_bal = balances[0]
            max_bal = balances[-1]
            avg_dd = sum(drawdowns) / self.runs

            monte_carlo[wr] = {
                "avg_bal": avg_bal,
                "med_bal": med_bal,
                "min_bal": min_bal,
                "max_bal": max_bal,
                "avg_dd": avg_dd * 100
            }

        self.finished.emit(theoretical, monte_carlo)


class WinrateCalculator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WinrateCalculator")
        self.sim_worker = None
        self._build_ui()
        self._calculate_general()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header
        header = QLabel("Winrate & RR Hesaplayıcı")
        header.setStyleSheet("color: #E6EDF3; font-size: 28px; font-weight: 800;")
        layout.addWidget(header)

        sub_header = QLabel("İşlem stratejinizin uzun vadeli getirisini hesaplayın ve simülasyon yapın.")
        sub_header.setStyleSheet("color: #8B949E; font-size: 14px;")
        layout.addWidget(sub_header)

        layout.addSpacing(10)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #30363D; border-radius: 12px; background: #0D1117; }
            QTabBar::tab { background: #161B22; color: #8B949E; padding: 10px 20px; border: 1px solid #30363D; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 4px; font-weight: 600; font-size: 14px; }
            QTabBar::tab:selected { background: #0D1117; color: #E6EDF3; border-bottom: 1px solid #0D1117; }
        """)
        
        self.tab_general = QWidget()
        self.tab_sim = QWidget()
        
        self.tabs.addTab(self.tab_general, "Genel Hesaplama")
        self.tabs.addTab(self.tab_sim, "Strateji Simülasyonu")
        
        layout.addWidget(self.tabs)

        self._build_general_tab()
        self._build_sim_tab()

    def _build_general_tab(self):
        c_layout = QHBoxLayout(self.tab_general)
        c_layout.setContentsMargins(30, 30, 30, 30)
        c_layout.setSpacing(40)

        # LEFT: Inputs
        left_widget = QWidget()
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
            QLineEdit:focus { border: 1px solid #8A2BE2; }
        """
        self.tab_general.setStyleSheet(input_style)

        left_layout.addWidget(self._create_label("Toplam İşlem Sayısı"))
        self.le_total = QLineEdit()
        self.le_total.setText("100")
        left_layout.addWidget(self.le_total)

        left_layout.addWidget(self._create_label("Kazanan İşlem Sayısı"))
        self.le_wins = QLineEdit()
        self.le_wins.setText("50")
        left_layout.addWidget(self.le_wins)

        left_layout.addWidget(self._create_label("Risk / Ödül Oranı (RR) — Örn: 1'e 2 için '2' yazın"))
        self.le_rr = QLineEdit()
        self.le_rr.setText("2")
        left_layout.addWidget(self.le_rr)

        left_layout.addStretch()
        c_layout.addWidget(left_widget, 1)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setStyleSheet("color: #30363D; background: #30363D;")
        c_layout.addWidget(divider)

        # RIGHT: Outputs
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(25)

        self.lbl_current_winrate = self._create_result_box("Mevcut Winrate (Kazanma Oranı):", "%0.00")
        self.lbl_req_winrate = self._create_result_box("Bu RR İçin Gereken Min. Winrate:", "%0.00", color="#A277FF")

        right_layout.addWidget(self.lbl_current_winrate)
        right_layout.addWidget(self.lbl_req_winrate)
        
        right_layout.addSpacing(20)

        self.lbl_status = QLabel("Durum: Hesaplama Bekleniyor")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("padding: 20px; border-radius: 10px; font-size: 18px; font-weight: 800; background-color: #161B22; color: #8B949E; border: 1px solid #30363D;")
        right_layout.addWidget(self.lbl_status)

        right_layout.addStretch()
        c_layout.addWidget(right_widget, 1)

        self.le_total.textChanged.connect(self._calculate_general)
        self.le_wins.textChanged.connect(self._calculate_general)
        self.le_rr.textChanged.connect(self._calculate_general)

    def _build_sim_tab(self):
        s_layout = QVBoxLayout(self.tab_sim)
        s_layout.setContentsMargins(30, 30, 30, 30)
        s_layout.setSpacing(20)

        # Settings Row
        settings_widget = QWidget()
        settings_layout = QHBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(15)

        self.tab_sim.setStyleSheet("""
            QLineEdit { background-color: #161B22; color: #E6EDF3; border: 1px solid #30363D; border-radius: 6px; padding: 8px 12px; font-size: 14px; }
            QLineEdit:focus { border: 1px solid #4863F7; }
        """)

        # Start Balance
        settings_layout.addWidget(self._create_label("Başlangıç Bakiyesi ($)"))
        self.le_sim_bal = QLineEdit("1000")
        settings_layout.addWidget(self.le_sim_bal)

        # Risk %
        settings_layout.addWidget(self._create_label("İşlem Başı Risk (%)"))
        self.le_sim_risk = QLineEdit("2.0")
        settings_layout.addWidget(self.le_sim_risk)

        # Total Trades
        settings_layout.addWidget(self._create_label("İşlem Sayısı"))
        self.le_sim_trades = QLineEdit("100")
        settings_layout.addWidget(self.le_sim_trades)

        # Run Button
        self.btn_run_sim = QPushButton("Simülasyonu Başlat")
        self.btn_run_sim.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run_sim.setStyleSheet("""
            QPushButton {
                background-color: #4863F7; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-size: 14px; font-weight: 700;
            }
            QPushButton:hover { background-color: #5A74FF; }
            QPushButton:disabled { background-color: #30363D; color: #8B949E; }
        """)
        self.btn_run_sim.clicked.connect(self._run_simulation)
        settings_layout.addWidget(self.btn_run_sim)

        s_layout.addWidget(settings_widget)

        # Tables Style
        table_style = """
            QTableWidget { background-color: #0D1117; color: #E6EDF3; border: 1px solid #30363D; border-radius: 8px; gridline-color: #21262D; }
            QHeaderView::section { background-color: #161B22; color: #8B949E; padding: 6px; border: none; border-bottom: 1px solid #30363D; border-right: 1px solid #30363D; font-weight: bold; }
            QTableWidget::item { padding: 4px; border-bottom: 1px solid #21262D; }
        """

        # Table 1: Theoretical
        s_layout.addWidget(self._create_label("1. Teorik Sonuçlar Tablosu (Tam Dağılım)", color="#4863F7", bold=True))
        self.table_theory = QTableWidget(4, 6)
        self.table_theory.setHorizontalHeaderLabels(["Başarı Oranı", "G/M Dağılımı", "Sabit Risk Bakiye", "Sabit Risk Kazanç", "Bileşik Risk Bakiye", "Bileşik Risk Kazanç"])
        self.table_theory.setStyleSheet(table_style)
        self.table_theory.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_theory.verticalHeader().setVisible(False)
        self.table_theory.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        s_layout.addWidget(self.table_theory)

        # Table 2: Monte Carlo
        s_layout.addWidget(self._create_label("2. Monte Carlo Simülasyonu Sonuçları (10.000 İterasyon)", color="#A277FF", bold=True))
        self.table_mc = QTableWidget(4, 6)
        self.table_mc.setHorizontalHeaderLabels(["Başarı Oranı", "Ortalama Bakiye", "Medyan Bakiye", "En Kötü Senaryo", "En İyi Senaryo", "Ort. Max Düşüş (DD)"])
        self.table_mc.setStyleSheet(table_style)
        self.table_mc.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_mc.verticalHeader().setVisible(False)
        self.table_mc.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        s_layout.addWidget(self.table_mc)

    def _create_label(self, text, color="#8B949E", bold=False):
        lbl = QLabel(text)
        weight = "800" if bold else "500"
        lbl.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: {weight}; border: none; background: transparent;")
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
        v_lbl.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: 800; border: none;")
        l.addWidget(t_lbl)
        l.addWidget(v_lbl)
        w.val_lbl = v_lbl
        return w

    def _get_float(self, le):
        try:
            return float(le.text().replace(",", "."))
        except ValueError:
            return -1.0

    def _calculate_general(self):
        total = self._get_float(self.le_total)
        wins = self._get_float(self.le_wins)
        rr = self._get_float(self.le_rr)

        if total <= 0 or wins < 0 or rr <= 0 or wins > total:
            self.lbl_current_winrate.val_lbl.setText("%0.00")
            self.lbl_req_winrate.val_lbl.setText("%0.00")
            self.lbl_status.setText("Geçersiz Veri")
            self.lbl_status.setStyleSheet("padding: 20px; border-radius: 10px; font-size: 18px; font-weight: 800; background-color: #161B22; color: #8B949E; border: 1px solid #30363D;")
            return

        current_winrate = (wins / total) * 100
        required_winrate = (1 / (1 + rr)) * 100

        self.lbl_current_winrate.val_lbl.setText(f"%{current_winrate:.2f}")
        self.lbl_req_winrate.val_lbl.setText(f"%{required_winrate:.2f}")

        if current_winrate > required_winrate + 0.01:
            self.lbl_status.setText("KÂRDASINIZ (Pozitif Beklenti) 🚀")
            self.lbl_status.setStyleSheet("padding: 20px; border-radius: 10px; font-size: 18px; font-weight: 800; background-color: rgba(0,200,83,0.1); color: #00C853; border: 1px solid #00C853;")
        elif abs(current_winrate - required_winrate) <= 0.01:
            self.lbl_status.setText("BAŞA BAŞ (Kâr/Zarar Yok) ⚖️")
            self.lbl_status.setStyleSheet("padding: 20px; border-radius: 10px; font-size: 18px; font-weight: 800; background-color: rgba(255,193,7,0.1); color: #FFC107; border: 1px solid #FFC107;")
        else:
            self.lbl_status.setText("ZARARDASINIZ (Negatif Beklenti) 📉")
            self.lbl_status.setStyleSheet("padding: 20px; border-radius: 10px; font-size: 18px; font-weight: 800; background-color: rgba(255,82,82,0.1); color: #FF5252; border: 1px solid #FF5252;")

    def _run_simulation(self):
        bal = self._get_float(self.le_sim_bal)
        risk = self._get_float(self.le_sim_risk)
        trades = self._get_float(self.le_sim_trades)
        rr = self._get_float(self.le_rr)  # From General tab

        if bal <= 0 or risk <= 0 or trades <= 0 or rr <= 0:
            return

        self.btn_run_sim.setText("Hesaplanıyor...")
        self.btn_run_sim.setEnabled(False)

        self.sim_worker = SimulationWorker(bal, risk / 100.0, rr, trades)
        self.sim_worker.finished.connect(self._on_sim_finished)
        self.sim_worker.start()

    def _create_item(self, text, color=None):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if color:
            item.setForeground(QColor(color))
        return item

    def _on_sim_finished(self, theory, mc):
        self.btn_run_sim.setText("Simülasyonu Başlat")
        self.btn_run_sim.setEnabled(True)

        winrates = [0.33, 0.40, 0.50, 0.60]
        
        # Populate Theoretical
        for i, wr in enumerate(winrates):
            data = theory[wr]
            self.table_theory.setItem(i, 0, self._create_item(f"%{wr*100:.0f}"))
            self.table_theory.setItem(i, 1, self._create_item(f"{data['wins']} G / {data['losses']} M"))
            self.table_theory.setItem(i, 2, self._create_item(f"${data['fixed_bal']:,.2f}"))
            
            f_ret_col = "#00C853" if data['fixed_ret'] >= 0 else "#FF5252"
            f_ret_sign = "+" if data['fixed_ret'] > 0 else ""
            self.table_theory.setItem(i, 3, self._create_item(f"{f_ret_sign}%{data['fixed_ret']:,.2f}", f_ret_col))
            
            self.table_theory.setItem(i, 4, self._create_item(f"${data['comp_bal']:,.2f}"))
            
            c_ret_col = "#00C853" if data['comp_ret'] >= 0 else "#FF5252"
            c_ret_sign = "+" if data['comp_ret'] > 0 else ""
            self.table_theory.setItem(i, 5, self._create_item(f"{c_ret_sign}%{data['comp_ret']:,.2f}", c_ret_col))

        # Populate Monte Carlo
        for i, wr in enumerate(winrates):
            data = mc[wr]
            self.table_mc.setItem(i, 0, self._create_item(f"%{wr*100:.0f}"))
            self.table_mc.setItem(i, 1, self._create_item(f"${data['avg_bal']:,.2f}"))
            self.table_mc.setItem(i, 2, self._create_item(f"${data['med_bal']:,.2f}"))
            
            min_col = "#FF5252" if data['min_bal'] < self._get_float(self.le_sim_bal) else "#E6EDF3"
            self.table_mc.setItem(i, 3, self._create_item(f"${data['min_bal']:,.2f}", min_col))
            
            max_col = "#00C853" if data['max_bal'] > self._get_float(self.le_sim_bal) else "#E6EDF3"
            self.table_mc.setItem(i, 4, self._create_item(f"${data['max_bal']:,.2f}", max_col))
            
            self.table_mc.setItem(i, 5, self._create_item(f"%{data['avg_dd']:,.2f}", "#FF7043"))
