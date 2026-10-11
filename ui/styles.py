"""Reference-driven design tokens for ANKA Finans terminal (Figma sync pending)."""
STYLE = """
QMainWindow, QWidget {
  background:#0B1420; color:#DCE8F7; font-family:"Segoe UI";
  font-size:11px;
}
QWidget#TerminalRoot {background:#0B1420;}
QFrame#TerminalTopBar {background:#0D1725;border:none;border-bottom:1px solid #203449;border-radius:0;}
QLabel#Mark {background:#0B655D;color:#60F7C6;font-size:20px;font-weight:900;border-radius:7px;}
QLabel#BrandLabel {color:#E9F3FF;font-size:21px;font-weight:900;letter-spacing:1px;}
QLabel#UserBadge {background:#294465;color:#DCEBFF;border-radius:16px;font-weight:800;}
QFrame#TopDivider {background:#253B52;border:0;}
QFrame#PriceStrip {background:#0C1B2B;border:0;border-bottom:1px solid #1B3147;border-radius:0;}
QLabel#TickerItem {font-size:10px;color:#D4E4F6;font-weight:650;}
QListWidget#TerminalSidebar {background:#0C1828;border:0;border-right:1px solid #1D3147;padding:14px 5px;outline:none;}
QListWidget#TerminalSidebar::item {color:#7199C3;border-radius:4px;margin:2px;padding:11px 2px;}
QListWidget#TerminalSidebar::item:selected {background:#103C41;color:#5DF0BC;border-left:2px solid #22C7A4;font-weight:900;}
QListWidget#TerminalSidebar::item:hover {background:#1B334C;}
QStackedWidget {background:#0B1420;padding:0px;border:0;}
QFrame#SymbolQuote {background:#111E30;border:1px solid #233A56;border-radius:4px;}
QFrame#TerminalPanel {background:#101C2C;border:1px solid #253B54;border-radius:5px;}
QFrame#PanelHeader {background:#132438;border:0;border-bottom:1px solid #263B52;border-radius:0;}
QFrame#MetricDivider {background:#243950;border:0;}
QFrame#DayRangeTrack {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #127F67,stop:0.45 #28BA93,stop:0.65 #67797F,stop:1 #946A35);border-radius:1px;}
QSplitter::handle {background:#0B1420;}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDoubleSpinBox, QSpinBox {
    background:#101E30;color:#E6F0FC;border:1px solid #30465E;
    border-radius:3px;padding:5px;selection-background-color:#274D70;
}
QLineEdit:focus,QComboBox:focus {border:1px solid #3F95BD;}
QLineEdit#SymbolSearch {background:#0C1928;border:1px solid #2B4964;min-height:23px;padding-left:9px;}
QPushButton {
    background:#1B324B;color:#CDDFEF;border:1px solid #304860;
    border-radius:4px;min-height:20px;padding:5px 11px;font-weight:650;
}
QPushButton:hover {background:#234562;color:#F0F8FF;}
QPushButton:pressed {background:#26577B;}
QPushButton#SecondaryButton {background:#122438;border-color:#2A4159;}
QPushButton#WorkspaceShortcut {background:#11243A;border-color:#213950;color:#8DB8E3;padding:3px 8px;}
QPushButton#ScreenerFilter {background:#102135;color:#8298B3;border-color:#2E4155;padding:3px 6px;font-size:10px;}
QPushButton#ScreenerFilter:checked {background:#123D39;color:#40E6AF;border-color:#27695E;}
QTableWidget#MarketGrid {background:#101C2C;alternate-background-color:#16283C;gridline-color:#233750;border:0;color:#DCE9F8;selection-background-color:#214462;selection-color:#FFFFFF;}
QHeaderView::section {background:#102136;color:#8DA6BE;padding:4px;border:0;border-bottom:1px solid #2C425B;font-size:10px;font-weight:700;}
QTableCornerButton::section {background:#102136;border:0;}
QScrollBar:vertical {width:8px;background:#101C2C;}
QScrollBar::handle:vertical {background:#36516D;border-radius:3px;min-height:18px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0px;}
QScrollBar:horizontal {height:7px;background:#101C2C;}
QScrollBar::handle:horizontal {background:#36516D;}
QStatusBar {background:#0C1828;color:#7C9BB5;border-top:1px solid #21374E;font-size:10px;}
QToolTip {background:#183048;color:#FFFFFF;border:1px solid #47718F;}
"""
