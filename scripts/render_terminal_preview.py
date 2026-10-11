"""Capture an offline, blank-state screenshot for ANKA Finans acceptance."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["ANKA_OFFLINE"] = "1"
os.environ["ANKA_DISABLE_LIVE"] = "1"

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.styles import STYLE


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="anka-preview-") as tmp:
        os.environ["ANKA_STATE_DIR"] = tmp
        app = QApplication([])
        windows_fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for name in ("segoeui.ttf", "arial.ttf"):
            font_path = windows_fonts / name
            if font_path.exists():
                QFontDatabase.addApplicationFont(str(font_path))
        app.setFont(QFont("Segoe UI", 10))
        app.setStyleSheet(STYLE)
        window = MainWindow()
        window.resize(1480, 890)
        window.show()
        app.processEvents()
        picture = window.grab()
        target = ROOT / "docs" / "previews" / "ANKA_Finans_Terminal_20261011.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        if picture.isNull() or not picture.save(str(target), "PNG"):
            print("SCREENSHOT=FAIL")
            window.close()
            return 2
        print("SCREENSHOT=PASS")
        print("IMAGE=" + str(target))
        print("IMAGE_BYTES=" + str(target.stat().st_size))
        print("TITLE=" + window.windowTitle())
        print("WORKSPACES=" + str(window.workspace.count()))
        window.resize(1366, 768)
        app.processEvents()
        reference_image = target.with_name("ANKA_Finans_Terminal_1366x768.png")
        if not window.grab().save(str(reference_image), "PNG"):
            print("REFERENCE_SCREENSHOT=FAIL")
            window.close()
            return 4
        print("REFERENCE_SCREENSHOT=PASS")
        print("REFERENCE_IMAGE=" + str(reference_image))
        window.workspace.setCurrentIndex(2)
        app.processEvents()
        ai_image = target.with_name("ANKA_Finans_Yapay_Zeka_20261011.png")
        if not window.grab().save(str(ai_image), "PNG"):
            print("AI_SCREENSHOT=FAIL")
            window.close()
            return 3
        print("AI_SCREENSHOT=PASS")
        print("AI_IMAGE=" + str(ai_image))
        window.close()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
