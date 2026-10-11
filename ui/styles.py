"""Dark professional desktop terminal design tokens and Qt styling."""

STYLE = """
QMainWindow, QWidget {
    background-color: #0D1420;
    color: #E9F1FB;
    font-family: "Segoe UI";
    font-size: 11pt;
}
QWidget#TerminalRoot { background: #0D1420; }
QFrame#TerminalTopBar {
    background: #101C2A;
    border-bottom: 1px solid #263548;
}
QLabel#BrandLabel {
    font-size: 21pt; font-weight: 800; color: #E5F6FF; letter-spacing: 1px;
}
QLabel#BrandSubTitle { font-size: 9pt; color: #7897AF; }
QLabel#OfflineBadge {
    color: #E8BA70;
    background-color: #322A25;
    border: 1px solid #67553D;
    padding: 9px 15px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 9pt;
}
QListWidget#TerminalSidebar {
    background: #121E2D;
    border: none;
    border-right: 1px solid #27384A;
    padding: 20px 8px;
    outline: none;
}
QListWidget#TerminalSidebar::item {
    padding: 15px 12px;
    margin: 2px 4px;
    color: #AABDD0;
    border-radius: 8px;
}
QListWidget#TerminalSidebar::item:selected {
    background: #1C3C4B;
    border-left: 3px solid #56CBE1;
    color: #E7FCFF;
    font-weight: bold;
}
QListWidget#TerminalSidebar::item:hover {
    background: #203449;
    color: #FFFFFF;
}
QStackedWidget { background: #0D1420; border: none; padding: 16px; }
QFrame {
    background-color: #162437;
    border: 1px solid #27374A;
    border-radius: 10px;
}
QLabel { color: #EAF2FC; border: none; }
QPushButton {
    color: #061A27;
    background-color: #63D1E4;
    border: 1px solid #4DBCCD;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 700;
    min-height: 17px;
}
QPushButton:hover { background-color: #82E4EE; }
QPushButton:pressed { background-color: #4EB9CB; }
QPushButton:disabled { background-color: #314354; color: #96A4B1; }
QPushButton#SecondaryButton {
    color: #D9EAF5;
    background-color: #213144;
    border: 1px solid #354B62;
}
QPushButton#SecondaryButton:hover { background-color: #2B4258; }
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    color: #EFF6FD;
    background-color: #111D2C;
    border: 1px solid #35465B;
    border-radius: 7px;
    padding: 8px;
    selection-background-color: #275A70;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #58CEE0;
}
QTableWidget, QTableView {
    background-color: #111C2A;
    alternate-background-color: #16283A;
    color: #EAF4FE;
    border: 1px solid #2A4054;
    gridline-color: #26384A;
    selection-background-color: #244A5B;
}
QHeaderView::section {
    background-color: #22354A; color: #C2D9E8;
    border: none; padding: 8px; font-weight: bold;
}
QScrollBar:vertical {
    width: 9px; background: #12202E;
}
QScrollBar::handle:vertical { background: #395168; border-radius: 4px; }
QStatusBar {
    background: #0F1A28; border-top: 1px solid #263849;
    color: #91B5C8; font-size: 9pt;
}
QToolTip {
    background: #1C3447; color: white;
    border: 1px solid #4F6F84;
}
"""
