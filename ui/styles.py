"""
LuckyHelper - Dark Theme QSS Styles
"""

MAIN_STYLE = """
/* ============================================================
   GLOBAL
   ============================================================ */
QWidget {
    background-color: #0D1117;
    color: #E6EDF3;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
    border: none;
    outline: none;
}

QMainWindow {
    background-color: #0D1117;
}

/* ============================================================
   SCROLLBARS
   ============================================================ */
QScrollBar:vertical {
    background: #161B22;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #30363D;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #00D4FF;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #161B22;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #30363D;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #00D4FF;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ============================================================
   SIDEBAR
   ============================================================ */
#Sidebar {
    background-color: #161B22;
    border-right: 1px solid #21262D;
    min-width: 220px;
    max-width: 220px;
}

#SidebarLogo {
    color: #00D4FF;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 24px 20px 8px 20px;
}

#SidebarSubtitle {
    color: #8B949E;
    font-size: 10px;
    letter-spacing: 2px;
    padding: 0px 20px 24px 20px;
    text-transform: uppercase;
}

#SidebarDivider {
    background-color: #21262D;
    max-height: 1px;
    margin: 0 16px;
}

#SidebarNavLabel {
    color: #8B949E;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 2px;
    padding: 20px 20px 8px 20px;
    text-transform: uppercase;
}

#SidebarBtn {
    background-color: transparent;
    color: #8B949E;
    text-align: left;
    padding: 10px 20px;
    border-radius: 8px;
    margin: 2px 10px;
    font-size: 13px;
    font-weight: 500;
}
#SidebarBtn:hover {
    background-color: #21262D;
    color: #E6EDF3;
}
#SidebarBtn[active="true"] {
    background-color: rgba(0, 212, 255, 0.12);
    color: #00D4FF;
    border-left: 3px solid #00D4FF;
    padding-left: 17px;
}

#SidebarFooter {
    color: #484F58;
    font-size: 10px;
    padding: 16px 20px;
}

/* ============================================================
   CONTENT AREA
   ============================================================ */
#ContentArea {
    background-color: #0D1117;
    padding: 0px;
}

/* ============================================================
   CALENDAR VIEW
   ============================================================ */
#CalendarHeader {
    background-color: #0D1117;
    padding: 24px 32px 16px 32px;
}

#CalendarTitle {
    color: #E6EDF3;
    font-size: 24px;
    font-weight: 700;
}

#CalendarSubtitle {
    color: #8B949E;
    font-size: 12px;
}

#NavBtn {
    background-color: #21262D;
    color: #E6EDF3;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 14px;
    font-weight: 700;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
}
#NavBtn:hover {
    background-color: #30363D;
    color: #00D4FF;
}

#TodayBtn {
    background-color: transparent;
    color: #00D4FF;
    border: 1px solid #00D4FF;
    border-radius: 8px;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 600;
}
#TodayBtn:hover {
    background-color: rgba(0, 212, 255, 0.12);
}

#DayHeader {
    color: #8B949E;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    padding: 8px 4px;
    text-align: center;
    text-transform: uppercase;
}

/* Day cells */
DayCell {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 6px;
}
DayCell:hover {
    border: 1px solid #8B949E;
    background-color: #1C2128;
}
DayCell[pnl_state="profit"] {
    background-color: rgba(0, 200, 83, 0.08);
    border: 1px solid rgba(0, 200, 83, 0.35);
}
DayCell[pnl_state="profit"]:hover {
    background-color: rgba(0, 200, 83, 0.16);
    border: 1px solid rgba(0, 200, 83, 0.6);
}
DayCell[pnl_state="loss"] {
    background-color: rgba(255, 61, 87, 0.08);
    border: 1px solid rgba(255, 61, 87, 0.35);
}
DayCell[pnl_state="loss"]:hover {
    background-color: rgba(255, 61, 87, 0.16);
    border: 1px solid rgba(255, 61, 87, 0.6);
}
DayCell[is_today="true"] {
    border: 1.5px solid #00D4FF;
}
DayCell[is_empty="true"] {
    background-color: transparent;
    border: 1px solid transparent;
}

#DayNumber {
    color: #E6EDF3;
    font-size: 14px;
    font-weight: 600;
}
#DayNumberToday {
    color: #00D4FF;
    font-size: 14px;
    font-weight: 700;
}
#DayNumberOtherMonth {
    color: #484F58;
    font-size: 14px;
}

#DayPnlLabel {
    font-size: 11px;
    font-weight: 700;
}
#DayTradeCountLabel {
    color: #8B949E;
    font-size: 10px;
}

/* Summary bar */
#SummaryBar {
    background-color: #161B22;
    border-top: 1px solid #21262D;
    padding: 12px 32px;
}
#SummaryItem {
    color: #8B949E;
    font-size: 12px;
}
#SummaryValue {
    font-size: 15px;
    font-weight: 700;
}
#SummaryValuePositive {
    color: #00C853;
    font-size: 15px;
    font-weight: 700;
}
#SummaryValueNegative {
    color: #FF3D57;
    font-size: 15px;
    font-weight: 700;
}

/* ============================================================
   TRADE DIALOG
   ============================================================ */
#TradeDialog {
    background-color: #0D1117;
}

#DialogHeader {
    background-color: #161B22;
    border-bottom: 1px solid #21262D;
    padding: 20px 28px;
}

#DialogTitle {
    color: #E6EDF3;
    font-size: 18px;
    font-weight: 700;
}

#DialogSubtitle {
    color: #8B949E;
    font-size: 12px;
}

#DialogPnlBar {
    background-color: #1C2128;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 16px 28px 8px 28px;
}

#DialogPnlLabel {
    color: #8B949E;
    font-size: 12px;
}
#DialogPnlValue {
    font-size: 22px;
    font-weight: 800;
}

#TradeTable {
    background-color: #161B22;
    alternate-background-color: #1C2128;
    border: 1px solid #21262D;
    border-radius: 8px;
    gridline-color: #21262D;
    selection-background-color: rgba(0, 212, 255, 0.15);
    selection-color: #E6EDF3;
}
#TradeTable::item {
    padding: 6px 8px;
    border: none;
}
#TradeTable::item:selected {
    background-color: rgba(0, 212, 255, 0.15);
}

QHeaderView::section {
    background-color: #0D1117;
    color: #8B949E;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    padding: 8px 8px;
    border: none;
    border-bottom: 1px solid #21262D;
    text-transform: uppercase;
}

QHeaderView::section:first {
    border-left: none;
}

/* Buttons */
#AddTradeBtn {
    background-color: #00D4FF;
    color: #0D1117;
    border-radius: 8px;
    padding: 9px 20px;
    font-size: 13px;
    font-weight: 700;
}
#AddTradeBtn:hover {
    background-color: #33DDFF;
}
#AddTradeBtn:pressed {
    background-color: #00AACC;
}

#SaveBtn {
    background-color: #00C853;
    color: #0D1117;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 700;
}
#SaveBtn:hover {
    background-color: #00E676;
}

#CancelBtn {
    background-color: #21262D;
    color: #8B949E;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}
#CancelBtn:hover {
    background-color: #30363D;
    color: #E6EDF3;
}

#DeleteBtn {
    background-color: transparent;
    color: #FF3D57;
    border: 1px solid #FF3D57;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 600;
}
#DeleteBtn:hover {
    background-color: rgba(255, 61, 87, 0.12);
}

/* Form inputs */
QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit {
    background-color: #1C2128;
    color: #E6EDF3;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 13px;
    selection-background-color: #00D4FF;
    selection-color: #0D1117;
}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
    border: 1px solid #00D4FF;
    background-color: #1f2c3a;
}
QLineEdit::placeholder {
    color: #484F58;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8B949E;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #1C2128;
    border: 1px solid #30363D;
    selection-background-color: rgba(0, 212, 255, 0.15);
    color: #E6EDF3;
    border-radius: 6px;
}

QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #30363D;
    width: 16px;
    border-radius: 3px;
}
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #00D4FF;
}

QLabel {
    color: #8B949E;
    font-size: 12px;
}

/* ============================================================
   TOOLTIP
   ============================================================ */
QToolTip {
    background-color: #1C2128;
    color: #E6EDF3;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ============================================================
   CONTEXT MENU
   ============================================================ */
QMenu {
    background-color: #1C2128;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 8px 20px;
    border-radius: 4px;
    color: #E6EDF3;
}
QMenu::item:selected {
    background-color: rgba(0, 212, 255, 0.15);
    color: #00D4FF;
}
QMenu::separator {
    background-color: #30363D;
    height: 1px;
    margin: 4px 12px;
}
"""

# Color constants for Python code use
COLOR_BG = "#0D1117"
COLOR_SIDEBAR = "#161B22"
COLOR_PANEL = "#1C2128"
COLOR_BORDER = "#21262D"
COLOR_BORDER2 = "#30363D"
COLOR_TEXT = "#E6EDF3"
COLOR_TEXT_DIM = "#8B949E"
COLOR_TEXT_DIMMER = "#484F58"
COLOR_ACCENT = "#00D4FF"
COLOR_PROFIT = "#00C853"
COLOR_LOSS = "#FF3D57"
