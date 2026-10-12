"""Actual main-menu route to the offline advanced terminal and its lifecycle."""
from __future__ import annotations

import builtins
from contextlib import ExitStack
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent, QSettings, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QLabel, QPushButton
from shiboken6 import isValid

from ui.components.dashboard import Dashboard
from ui.main_window import MainWindow


class IntegratedTerminalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.directory = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.layout_file = self.directory / "layout.ini"
        self.stack.enter_context(patch.dict(os.environ, {
            "ANKA_OFFLINE": "1", "ANKA_STATE_DIR": str(self.directory),
            "ANKA_LAYOUT_FILE": str(self.layout_file),
        }))
        self.stack.enter_context(patch.object(Dashboard, "refresh", return_value=None))
        self.stack.enter_context(patch(
            "requests.sessions.Session.request", side_effect=AssertionError("NETWORK_FORBIDDEN")
        ))
        self.window = MainWindow()
        self.window.show()
        self.app.processEvents()
        self.addCleanup(self.close_main)

    def flush_deletes(self):
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def close_main(self):
        if isValid(self.window):
            self.window.close()
            self.window.deleteLater()
        self.flush_deletes()

    def menu_action(self, window=None):
        owner = window or self.window
        action = owner.findChild(QAction, "openAdvancedTerminalAction")
        self.assertIsNotNone(action, "Normal MainWindow must expose the advanced terminal QAction")
        self.assertEqual(action.text(), "Gelişmiş grafikler (Demo / CSV)")
        self.assertTrue(action.isEnabled())
        self.assertTrue(any(
            item.menu() and action in item.menu().actions()
            for item in owner.menuBar().actions()
        ), "The action must be discoverable in the normal menu")
        return action

    def open_terminal(self, window=None):
        owner = window or self.window
        self.menu_action(owner).trigger()
        self.app.processEvents()
        terminal = owner._advanced_terminal
        self.assertIsNotNone(terminal)
        self.assertTrue(terminal.isVisible())
        self.assertIs(terminal.parentWidget(), owner)
        self.assertTrue(terminal.isWindow())
        return terminal

    def test_menu_route_preserves_pages_and_shows_demo_charts_and_disabled_orders(self):
        pages = tuple(self.window.workspace.widget(i) for i in range(6))
        self.window.sidebar.setCurrentRow(4)
        terminal = self.open_terminal()
        self.assertEqual(self.window.workspace.count(), 6)
        self.assertEqual(tuple(self.window.workspace.widget(i) for i in range(6)), pages)
        self.assertEqual(self.window.workspace.currentIndex(), 4)
        self.assertEqual(terminal.workspace_tabs.count(), 2)
        self.assertIn("Mum", terminal.workspace_tabs.tabText(0))
        self.assertIn("Sharpe", terminal.workspace_tabs.tabText(1))
        self.assertFalse(terminal.chart.grab().isNull())
        self.assertIn("GERÇEK VERİ YOK", terminal.statusBar().currentMessage())
        self.assertIn("ÖRNEK VERİ", terminal.form.findChild(QLabel, "symbolDemo").text())
        self.assertIn("EMİR KAPALI", terminal.form.findChild(QLabel, "symbolDemo").text())
        orders = [b for b in terminal.findChildren(QPushButton) if "GERÇEK EMİR" in b.text()]
        self.assertEqual(len(orders), 1)
        self.assertFalse(orders[0].isEnabled())
        terminal.workspace_tabs.setCurrentIndex(1)
        self.app.processEvents()
        panel = terminal.performance_panel
        self.assertTrue(panel.comparison.demo)
        self.assertTrue(panel.comparison.sources)
        self.assertIn("SENTETİK", panel.source_banner.text())
        self.assertIn("sentetik / demo", panel.notice.text())
        self.assertFalse(panel.top_plot.grab().isNull())
        self.assertFalse(panel.bottom_plot.grab().isNull())
        terminal.workspace_tabs.setCurrentIndex(0)
        self.assertTrue(terminal.form.isVisible())

    def test_repeated_action_reuses_and_restores_minimized_terminal(self):
        first = self.open_terminal()
        first.choose_symbol("ASELS")
        first.showMinimized()
        self.app.processEvents()
        with (
            patch.object(first, "raise_", wraps=first.raise_) as raised,
            patch.object(first, "activateWindow", wraps=first.activateWindow) as activated,
        ):
            self.assertIs(self.open_terminal(), first)
            raised.assert_called_once_with()
            activated.assert_called_once_with()
        self.assertFalse(first.isMinimized())
        self.assertEqual(first.chart.symbol, "ASELS")
        self.assertEqual(len([w for w in self.window.children() if w is first]), 1)

    def test_close_and_immediate_reopen_releases_old_reference_and_deletes_docks(self):
        first = self.open_terminal()
        first.float_panels()
        docks = list(first._dock.values())
        self.assertTrue(first.close())
        self.assertIsNone(self.window._advanced_terminal)
        # Reopen before Qt processes the previous window's deferred deletion.
        self.menu_action().trigger()
        second = self.window._advanced_terminal
        self.assertIsNot(second, first)
        self.flush_deletes()
        self.assertFalse(isValid(first))
        self.assertTrue(all(not isValid(dock) for dock in docks))
        self.assertIs(self.window._advanced_terminal, second)
        self.assertTrue(second.isVisible())

    def test_main_close_cleans_owned_terminal_and_auxiliary_terminal(self):
        first = self.open_terminal()
        first.float_panels()
        extra = self.window.open_workspace_window()
        second = self.open_terminal(extra)
        second.float_panels()
        docks = list(first._dock.values()) + list(second._dock.values())
        self.window.close()
        self.flush_deletes()
        self.assertIsNone(self.window._advanced_terminal)
        self.assertIsNone(extra._advanced_terminal)
        self.assertFalse(extra.isVisible())
        self.assertFalse(isValid(first))
        self.assertFalse(isValid(second))
        self.assertTrue(all(not isValid(dock) for dock in docks))
        extra.deleteLater()

    def test_action_preserves_csv_loading_and_unverified_source_labels(self):
        terminal = self.open_terminal()
        terminal.workspace_tabs.setCurrentIndex(1)
        panel = terminal.performance_panel
        source = self.directory / "prices.csv"
        source.write_text(
            "symbol,date,close,currency\n"
            "AAA,2026-01-01,100,USD\nAAA,2026-01-02,105,USD\nAAA,2026-01-05,110,USD\n"
            "BBB,2026-01-01,100,USD\nBBB,2026-01-02,101,USD\nBBB,2026-01-05,102,USD\n",
            encoding="utf-8",
        )
        with patch("ui.multi_asset_performance.QFileDialog.getOpenFileName",
                   return_value=(str(source), "CSV")) as dialog:
            panel.csv_button.click()
            dialog.assert_called_once()
        self.assertIsNotNone(panel.comparison, panel.summary.text())
        self.assertFalse(panel.comparison.demo)
        self.assertEqual({s.symbol for s in panel.comparison.series}, {"AAA", "BBB"})
        self.assertIn("DOĞRULANMADI", panel.source_banner.text())
        self.assertIn("CANLI DEĞİL", panel.source_banner.text())
        self.assertIn("Kullanıcının yerel CSV", panel.notice.text())
        self.assertIn("Dosya zamanı:", panel.notice.text())

    def test_saved_layout_survives_close_reopen_without_implicit_writes(self):
        first = self.open_terminal()
        self.assertFalse(self.layout_file.exists())
        first.choose_symbol("GARAN")
        first.set_chart_zoom(100)
        first.float_panels()
        first.form.findChild(QPushButton, "saveLayoutButton").click()
        self.assertTrue(self.layout_file.is_file())
        saved = self.layout_file.read_bytes()
        first.close()
        second = self.open_terminal()
        self.assertEqual(second.chart.symbol, "GARAN")
        self.assertEqual(second.chart.visible, 100)
        self.assertTrue(second._dock["Piyasa Derinliği"].isFloating())
        second.close()
        self.flush_deletes()
        self.assertEqual(self.layout_file.read_bytes(), saved)

    def test_terminal_style_and_settings_are_local_to_its_window(self):
        def globals_snapshot():
            return (self.app.styleSheet(), self.app.font().toString(),
                    self.app.style().objectName(), self.app.applicationName(),
                    self.app.organizationName(), self.app.organizationDomain(),
                    QSettings.defaultFormat(), dict(os.environ))

        before = globals_snapshot()
        main_style = self.window.styleSheet()
        terminal = self.open_terminal()
        from scripts.anka_professional_toolchain_demo import QSS
        self.assertEqual(terminal.styleSheet(), QSS)
        self.assertTrue(terminal.testAttribute(Qt.WidgetAttribute.WA_DeleteOnClose))
        self.assertEqual(self.window.styleSheet(), main_style)
        terminal.close()
        self.flush_deletes()
        self.assertEqual(globals_snapshot(), before)
        self.assertFalse(self.layout_file.exists())

    def test_main_window_defers_advanced_import_until_menu_action(self):
        imported = []
        original = builtins.__import__

        def record(name, *args, **kwargs):
            if name in {"ui.advanced_terminal", "scripts.anka_professional_toolchain_demo"}:
                imported.append(name)
            return original(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=record):
            extra = MainWindow()
            try:
                self.assertEqual(imported, [])
                self.assertIsNone(extra._advanced_terminal)
                self.open_terminal(extra)
                self.assertIn("ui.advanced_terminal", imported)
            finally:
                extra.close()
                extra.deleteLater()
                self.flush_deletes()
