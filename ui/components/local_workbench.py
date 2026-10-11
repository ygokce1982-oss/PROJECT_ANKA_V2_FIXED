"""Usable local analysis and paper portfolio; never labelled live."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.local_settings import DEFAULT_SETTINGS, load_settings
from core.offline_workbench import LocalStore, read_csv, sample_bars


def state_path() -> Path:
    root = os.getenv("ANKA_STATE_DIR")
    if root:
        return Path(root) / "research.sqlite"
    return Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "ANKA_Finans" / "research.sqlite"


class PriceChart(QWidget):
    def __init__(self):
        super().__init__()
        self.values = []
        self.bars = []
        self.mode = "Mum"
        self.group_size = 1
        self.show_sma = True
        self.setMinimumHeight(200)

    def display_bars(self):
        result = []
        for start in range(0, len(self.bars), self.group_size):
            group = self.bars[start : start + self.group_size]
            result.append(
                replace(
                    group[-1],
                    open=group[0].open,
                    high=max(bar.high for bar in group),
                    low=min(bar.low for bar in group),
                    volume=sum(bar.volume for bar in group),
                )
            )
        return result

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#101b2b"))
        if len(self.values) < 2:
            painter.setPen(QColor("#a6b5c8"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Analiz için veri yükleyin")
            return
        grouped = self.display_bars()
        visible = grouped[-180:]
        values = [bar.close for bar in visible] if visible else self.values[-180:]
        lower = min(bar.low for bar in visible) if visible else min(values)
        upper = max(bar.high for bar in visible) if visible else max(values)
        spread = upper - lower or 1

        def y(value):
            return self.height() - 25 - (value - lower) * (self.height() - 50) / spread

        def x(index):
            return 25 + index * (self.width() - 50) / max(1, len(values) - 1)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor("#29364b"))
        for index in range(5):
            level = lower + spread * index / 4
            painter.drawLine(QPointF(15, y(level)), QPointF(self.width() - 15, y(level)))
        painter.setPen(QColor("#a6b5c8"))
        painter.drawText(20, 15, f"{upper:.4f}")
        painter.drawText(20, self.height() - 5, f"{lower:.4f} · son {len(values)} birleşik mum")
        if self.mode == "Mum" and visible:
            width = min(12, (self.width() - 50) / max(len(visible), 1) * 0.65)
            for index, bar in enumerate(visible):
                color = QColor("#52c6b2" if bar.close >= bar.open else "#ed7787")
                painter.setPen(QPen(color, 1))
                painter.setBrush(color)
                painter.drawLine(QPointF(x(index), y(bar.high)), QPointF(x(index), y(bar.low)))
                painter.drawRect(
                    QRectF(
                        x(index) - width / 2,
                        min(y(bar.open), y(bar.close)),
                        width,
                        max(1, abs(y(bar.close) - y(bar.open))),
                    )
                )
        else:
            painter.setPen(QPen(QColor("#52c6b2"), 2))
            points = [QPointF(x(index), y(value)) for index, value in enumerate(values)]
            for start, end in zip(points, points[1:], strict=False):
                painter.drawLine(start, end)
        if not self.show_sma or not grouped:
            return
        closes = [bar.close for bar in grouped]
        offset = len(grouped) - len(visible)
        for window, color in ((20, "#f1bf64"), (35, "#9f94f8")):
            painter.setPen(QPen(QColor(color), 1.5))
            previous = None
            for index in range(offset, len(closes)):
                if index + 1 < window:
                    continue
                value = sum(closes[index + 1 - window : index + 1]) / window
                point = QPointF(x(index - offset), y(value))
                if previous is not None:
                    painter.drawLine(previous, point)
                previous = point


class LocalWorkbenchPage(QWidget):
    def __init__(self):
        super().__init__()
        self.result = None
        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel("Yerel araştırma · Örnek / CSV · Canlı bağlantı ve emir iletimi yok")
        )
        actions = QHBoxLayout()
        self.symbol = QLineEdit("DEMO1")
        self.symbol.setMaxLength(32)
        self.symbol.setPlaceholderText("Sembol")
        self.currency = QComboBox()
        self.currency.addItems(["TRY", "USD", "EUR"])
        try:
            defaults = load_settings(state_path().with_name("settings.json"))
        except ValueError:
            defaults = DEFAULT_SETTINGS
        self.symbol.setText(defaults["default_symbol"])
        self.currency.setCurrentText(defaults["default_currency"])
        identity = QHBoxLayout()
        identity.addWidget(QLabel("Varlık"))
        identity.addWidget(self.symbol)
        identity.addWidget(QLabel("Para birimi"))
        identity.addWidget(self.currency)
        layout.addLayout(identity)
        sample = QPushButton("Örnek veriyi analiz et")
        sample.clicked.connect(self.run_sample)
        csv_button = QPushButton("CSV içe aktar")
        csv_button.clicked.connect(self.import_csv)
        export = QPushButton("Sonucu dışa aktar")
        export.clicked.connect(self.export_result)
        for button in (sample, csv_button, export):
            actions.addWidget(button)
        layout.addLayout(actions)
        self.status = QLabel("Veri yüklenmedi")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.chart = PriceChart()
        chart_controls = QHBoxLayout()
        self.chart_mode = QComboBox()
        self.chart_mode.addItems(["Mum", "Çizgi"])
        self.chart_mode.currentTextChanged.connect(self.set_chart_mode)
        self.chart_group = QComboBox()
        for label, size in (("Her mum", 1), ("5 mum birleştir", 5), ("20 mum birleştir", 20)):
            self.chart_group.addItem(label, size)
        self.chart_group.currentIndexChanged.connect(self.set_chart_group)
        self.sma_overlay = QCheckBox("SMA20/35 · görüntülenen mumlarda")
        self.sma_overlay.setChecked(True)
        self.sma_overlay.toggled.connect(self.set_sma_overlay)
        chart_controls.addWidget(self.chart_mode)
        chart_controls.addWidget(self.chart_group)
        chart_controls.addWidget(self.sma_overlay)
        layout.addLayout(chart_controls)
        layout.addWidget(self.chart, 1)
        self.table = QTableWidget(0, 2)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(["Ölçüm", "Sonuç"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        from ui.components.risk_planner import RiskPlannerWidget

        self.risk_planner = RiskPlannerWidget(self)
        layout.addWidget(self.risk_planner)

    def set_chart_mode(self, mode):
        self.chart.mode = mode
        self.chart.update()

    def set_chart_group(self, index):
        self.chart.group_size = self.chart_group.itemData(index)
        self.chart.update()

    def set_sma_overlay(self, enabled):
        self.chart.show_sma = enabled
        self.chart.update()

    def clear_analysis(self):
        self.result = None
        self.chart.values = []
        self.chart.bars = []
        self.chart.update()
        self.table.setRowCount(0)

    def run_sample(self):
        self.run_bars(sample_bars(), "SAMPLE")

    def run_bars(self, bars, origin):
        store = None
        try:
            store = LocalStore(state_path())
            result = store.execute(
                bars,
                symbol=self.symbol.text().strip().upper(),
                origin=origin,
                currency=self.currency.currentText(),
            )
            self.result = result
            self.chart.values = [bar.close for bar in bars]
            self.chart.bars = bars
            self.chart.update()
            data, strategy = result["analysis"], result["strategy"]
            rows = [
                (
                    "Veri",
                    "ÖRNEK" if origin == "SAMPLE" else "YEREL CSV · doğrulanmış canlı veri değil",
                ),
                ("Mum sayısı", str(data["rows"])),
                (f"Son fiyat ({result['currency']})", f"{data['close']:.4f}"),
                ("SMA20 / SMA35", f"{data['sma20']:.4f} / {data['sma35']:.4f}"),
                ("RSI14 · basit", f"{data['rsi14_simple']:.2f}"),
                ("Piyasa rejimi", data["regime"]),
                ("Mum volatilitesi", f"{data['bar_volatility']:.2%}"),
                ("Maksimum fiyat düşüşü", f"{data['maximum_drawdown']:.2%}"),
                ("SMA20 deneme getirisi", f"{strategy['return']:.2%}"),
                ("Strateji düşüşü", f"{strategy['maximum_drawdown']:.2%}"),
                ("Deneme işlem sayısı", str(strategy["orders"])),
                ("Komisyon", f"{strategy['fee_rate']:.2%}"),
            ]
            self.table.setRowCount(len(rows))
            for index, (name, value) in enumerate(rows):
                self.table.setItem(index, 0, QTableWidgetItem(name))
                self.table.setItem(index, 1, QTableWidgetItem(value))
            self.status.setText(
                "Analiz kalıcı kayda yazıldı. " + data["explanation"] + " " + strategy["method"]
            )
        except (ValueError, OSError, sqlite3.Error) as error:
            self.status.setText("Analiz başarısız: " + str(error))
            self.clear_analysis()
        finally:
            if store is not None:
                store.close()

    def import_csv(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Yerel fiyat verisi", "", "CSV (*.csv)")
        if filename:
            try:
                self.run_bars(read_csv(Path(filename)), "LOCAL_CSV")
            except (ValueError, OSError) as error:
                self.status.setText("CSV reddedildi: " + str(error))
                self.clear_analysis()

    def export_result(self):
        if not self.result:
            self.status.setText("Önce başarılı bir analiz çalıştırın")
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Analiz kaydı", "anka-yerel.json", "JSON (*.json)"
        )
        if filename:
            try:
                Path(filename).write_text(
                    json.dumps(self.result, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                self.status.setText("Yerel analiz dışa aktarıldı")
            except OSError as error:
                self.status.setText("Dışa aktarım başarısız: " + str(error))


class PaperPortfolioPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Deneme portföyü · TRY · Gerçek hesap veya emir bağlantısı yok"))
        self.status = QLabel("Yerel analiz fiyatıyla deneme yapın; ilk bakiye 100.000 TRY")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.quantity = QDoubleSpinBox()
        self.quantity.setRange(0.01, 100000)
        self.quantity.setValue(1)
        self.symbol = QComboBox()
        self.symbol.setPlaceholderText("Önce analiz kaydedin")
        selection = QHBoxLayout()
        selection.addWidget(QLabel("Analiz kaydı"))
        selection.addWidget(self.symbol)
        layout.addLayout(selection)
        fx_controls = QHBoxLayout()
        self.fx_inputs = {}
        for currency in ("USD", "EUR"):
            value = QDoubleSpinBox()
            value.setDecimals(6)
            value.setRange(0, 1000000)
            value.setSpecialValueText("Kur girilmedi")
            self.fx_inputs[currency] = value
            fx_controls.addWidget(QLabel(f"1 {currency} / TRY · elle girilen deneme kuru"))
            fx_controls.addWidget(value)
        layout.addLayout(fx_controls)
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(0.01, 1000000)
        self.threshold.setValue(120)
        row = QHBoxLayout()
        row.addWidget(QLabel("Miktar"))
        row.addWidget(self.quantity)
        for title, side in (("Deneme al", "BUY"), ("Deneme sat", "SELL")):
            button = QPushButton(title)
            button.clicked.connect(lambda checked=False, value=side: self.trade(value))
            row.addWidget(button)
        layout.addLayout(row)
        alerts = QHBoxLayout()
        alerts.addWidget(QLabel("Yukarı geçiş alarmı"))
        alerts.addWidget(self.threshold)
        add = QPushButton("Alarm kaydet")
        add.clicked.connect(self.add_alert)
        alerts.addWidget(add)
        layout.addLayout(alerts)
        refresh = QPushButton("Portföyü ve alarmları kontrol et")
        refresh.clicked.connect(self.refresh)
        layout.addWidget(refresh)
        self.table = QTableWidget(0, 2)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(["Ölçüm", "Deneme değeri"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def with_latest(self, operation):
        store = None
        try:
            store = LocalStore(state_path())
            available = store.latest_by_symbol()
            selected = self.symbol.currentData()
            self.symbol.blockSignals(True)
            self.symbol.clear()
            for symbol, item in available.items():
                self.symbol.addItem(f"{symbol} · {item['currency']}", symbol)
            if selected in available:
                self.symbol.setCurrentIndex(self.symbol.findData(selected))
            elif available:
                self.symbol.setCurrentIndex(0)
            self.symbol.blockSignals(False)
            result = available.get(self.symbol.currentData())
            if not result:
                raise ValueError("Önce Grafik bölümünde yerel analiz çalıştırın")
            operation(store, result)
            return True
        except (ValueError, OSError, sqlite3.Error) as error:
            self.status.setText(str(error))
            return False
        finally:
            if store is not None:
                store.close()

    def trade(self, side):
        successful = self.with_latest(
            lambda store, result: store.trade(
                result["symbol"],
                side,
                self.quantity.value(),
                result["analysis"]["close"],
                currency=result["currency"],
                fx_rates=self.fx_rates(),
            )
        )
        if successful:
            self.refresh()

    def fx_rates(self):
        return {
            currency: widget.value()
            for currency, widget in self.fx_inputs.items()
            if widget.value() > 0
        }

    def add_alert(self):
        def operation(store, result):
            store.add_alert(result["symbol"], self.threshold.value(), result["analysis"]["close"])
            self.status.setText("Alarm yerel kayda yazıldı; cihaz bildirimi bağlı değil")

        self.with_latest(operation)

    def refresh(self):
        def operation(store, result):
            records = store.latest_by_symbol()
            prices = {symbol: item["analysis"]["close"] for symbol, item in records.items()}
            report = store.portfolio(prices, fx_rates=self.fx_rates())
            count = store.check_alerts(
                result["symbol"], result["analysis"]["close"], result["analysis"]["last_bar_at"]
            )
            self.status.setText(
                f"Deneme portföyü · Yeni alarm: {count} · "
                f"Fiyatlanamayan pozisyonlar: {', '.join(report['unpriced']) or 'yok'} · "
                f"Kuru eksik: {', '.join(report.get('missing_fx', [])) or 'yok'} · "
                "Kurlar yalnız bu oturumda elle girilen deneme değerleridir."
            )
            rows = [
                ("Nakit", report["cash"]),
                ("Bilinen toplam değer", report["known_equity"]),
                ("%20 varlık düşüşü senaryosu", report["stress_equity"]),
            ]
            rows += [
                (position["symbol"] + " miktar", position["quantity"])
                for position in report["positions"]
            ]
            self.table.setRowCount(len(rows))
            for index, (name, value) in enumerate(rows):
                self.table.setItem(index, 0, QTableWidgetItem(name))
                self.table.setItem(index, 1, QTableWidgetItem(f"{value:.4f}"))

        self.with_latest(operation)
