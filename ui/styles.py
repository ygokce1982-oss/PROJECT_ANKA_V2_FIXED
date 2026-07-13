STYLE = """
QMainWindow, QWidget {
    background:#181A20;
    color:#FFFFFF;
    font-family:"Segoe UI";
    font-size:10pt;
}

QLabel { color:white; }

QListWidget {
    background:#20242B;
    border:none;
    outline:none;
    padding:8px;
}

QListWidget::item {
    padding:12px;
    margin:4px;
    border-radius:8px;
}

QListWidget::item:selected {
    background:#0D6EFD;
    color:white;
}

QListWidget::item:hover { background:#303742; }

QStackedWidget {
    background:#1F232A;
    border:1px solid #343B45;
    border-radius:10px;
}

QFrame {
    background:#2A3038;
    border:1px solid #404854;
    border-radius:10px;
}

QPushButton {
    background:#0D6EFD;
    color:white;
    border:none;
    border-radius:7px;
    padding:8px 14px;
    font-weight:bold;
}

QPushButton:hover { background:#2B7FFF; }
QPushButton:pressed { background:#0A58CA; }
QPushButton:disabled { background:#3A414C;color:#9098A3; }

QStatusBar {
    background:#14161A;
    color:#C8C8C8;
    border-top:1px solid #333;
}

QToolTip {
    background:#2D323C;
    color:white;
    border:1px solid #555;
}
"""
