"""Reference-driven ANKA Finans market workstation.

Interactive, resizable, dense desktop layout. All displayed market examples are
explicitly synthetic: never misrepresent them as licensed or live prices.
"""
from __future__ import annotations

import os
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSplitter, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QSizePolicy,
)
from core.market_data import MarketData, MarketSnapshot
from ui.components.info_card import InfoCard

SYMBOLS = [
    ("XU100", "BIST 100", "11.765,42", "+1,24%", "128,40", "11.806,40", "11.580,23", "11.621,08"),
    ("THYAO", "Türk Hava Yolları", "312,75", "+2,18%", "8,42", "314,63", "304,24", "306,08"),
    ("ASELS", "Aselsan", "168,40", "+3,06%", "6,81", "169,90", "161,00", "163,40"),
    ("GARAN", "Garanti BBVA", "148,20", "+1,44%", "5,23", "149,50", "144,00", "146,10"),
    ("AKBNK", "Akbank", "72,65", "+0,97%", "4,78", "73,20", "71,15", "71,95"),
    ("TUPRS", "Tüpraş", "188,90", "-0,63%", "3,96", "192,80", "187,05", "190,10"),
    ("EREGL", "Ereğli Demir Çelik", "29,84", "-1,12%", "2,88", "30,61", "29,55", "30,18"),
    ("BIMAS", "BİM Mağazalar", "596,50", "+0,84%", "2,65", "598,00", "586,00", "591,50"),
    ("KCHOL", "Koç Holding", "214,60", "+1,36%", "2,12", "215,70", "211,20", "211,72"),
    ("SISE", "Şişecam", "46,82", "-0,42%", "1,94", "47,50", "46,55", "47,02"),
    ("PGSUS", "Pegasus", "246,60", "+2,80%", "2,21", "247,50", "239,10", "239,90"),
    ("SASA", "Sasa Polyester", "3,59", "-0,28%", "1,47", "3,64", "3,56", "3,60"),
]


def label(text, *, size=11, tone="#C7D9ED", weight=400, name=None):
    widget = QLabel(str(text))
    widget.setStyleSheet(
        f"color:{tone};font-size:{size}px;font-weight:{weight};"
        "background:transparent;border:none;"
    )
    if name:
        widget.setObjectName(name)
    return widget


def small_button(title, *, name=None, checked=False):
    button = QPushButton(title)
    button.setObjectName(name or "PanelButton")
    button.setCheckable(checked)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setMinimumHeight(25)
    return button


class MarketDataWorker(QThread):
    completed = Signal(object)

    def run(self):
        try:
            self.completed.emit(MarketData.get_snapshot())
        except Exception:
            self.completed.emit(MarketData.error_snapshot("Piyasa veri hatası"))


class Panel(QFrame):
    def __init__(self, title, hint=""):
        super().__init__()
        self.setObjectName("TerminalPanel")
        self.setMinimumSize(185, 140)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(0)
        bar = QFrame()
        bar.setObjectName("PanelHeader")
        heading = QHBoxLayout(bar)
        heading.setContentsMargins(11, 0, 11, 0)
        heading.setSpacing(8)
        heading.addWidget(label("▣", size=10, tone="#5B90C4"))
        heading.addWidget(label(title, size=12, tone="#E1EBF7", weight=700))
        heading.addStretch()
        if hint:
            heading.addWidget(label(hint, size=10, tone="#8196AE"))
        heading.addWidget(label("−   ↔", size=11, tone="#6884A5"))
        bar.setFixedHeight(34)
        self.body.addWidget(bar)


def market_table(columns, headersize=10):
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setObjectName("MarketGrid")
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setMinimumSectionSize(45)
    table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setShowGrid(False)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.verticalHeader().setDefaultSectionSize(31)
    table.setSortingEnabled(False)
    return table


def cell(value, *, change=False, symbol=False):
    it = QTableWidgetItem(str(value))
    color = (
        "#34D5A2" if str(value).startswith("+") else "#F27A86"
    ) if change else ("#E1EFFF" if symbol else "#B8CDE4")
    it.setForeground(QColor(color))
    if symbol:
        font = QFont("Segoe UI", 9)
        font.setBold(True)
        it.setFont(font)
    return it


class Dashboard(QWidget):
    navigate_to = Signal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("DenseMarketTerminal")
        self._worker = None
        self._selected = "THYAO"
        self._tabs = {}
        self._mode = "Hacim artışı"
        self.quick_buttons = {}
        # Backwards compatibility with market data contracts.
        self.cards = {k: InfoCard(k, value="—") for k in ("xu100", "usdtry", "eurtry", "gold", "btc")}
        for widget in self.cards.values():
            widget.hide()
        self._build()
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._shutdown_worker)
        self.refresh()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 0, 10, 7)
        outer.setSpacing(8)

        titlebar = QHBoxLayout()
        titlebar.setSpacing(10)
        titlebar.addWidget(label("EKRAN 2", size=10, tone="#6CB2F3", weight=700))
        titlebar.addWidget(label("Piyasa izleme", size=14, tone="#F1F5FC", weight=800))
        titlebar.addWidget(label("Fiyat, derinlik ve tarama", size=10, tone="#8198AE"))
        titlebar.addStretch()
        titlebar.addWidget(label("● Bağ: DEMO", size=10, tone="#6D9DEA"))
        self.refresh_button = small_button("Yenile", name="WorkspaceShortcut")
        self.refresh_button.clicked.connect(self.refresh)
        titlebar.addWidget(self.refresh_button)
        for text, page in (("Grafik", 1), ("Ajan", 2), ("Araştırma", 3), ("Portföy", 4)):
            b = small_button(text, name="WorkspaceShortcut")
            b.clicked.connect(lambda checked=False, n=page: self.navigate_to.emit(n))
            self.quick_buttons[page] = b
            titlebar.addWidget(b)
        outer.addLayout(titlebar)

        quote = QFrame()
        quote.setObjectName("SymbolQuote")
        quote.setFixedHeight(74)
        q = QHBoxLayout(quote)
        q.setContentsMargins(17, 8, 17, 8)
        q.setSpacing(13)
        brand = QVBoxLayout()
        brand.setSpacing(3)
        self.symbol_label = label("THYAO", size=19, tone="#F0F6FF", weight=850)
        self.symbol_full = label("Türk Hava Yolları", size=10, tone="#7795B6")
        brand.addWidget(self.symbol_label)
        brand.addWidget(self.symbol_full)
        q.addLayout(brand)
        q.addStretch(1)
        self.last_label = label("312,75", size=26, tone="#F6FAFF", weight=800)
        q.addWidget(self.last_label)
        q.addWidget(label("TL", size=10, tone="#8CA5BD"))
        self.change_label = label("+2,18%", size=12, tone="#35D6A8", weight=800)
        q.addWidget(self.change_label)
        for title, attr, initial in (
            ("Gün yüksek", "high_label", "314,63"),
            ("Gün düşük", "low_label", "304,24"),
            ("Hacim (M)", "vol_label", "8,42"),
            ("Önceki kapanış", "close_label", "306,08"),
        ):
            col = QVBoxLayout()
            col.setSpacing(6)
            col.addWidget(label(title, size=10, tone="#7890AA"))
            node = label(initial, size=12, tone="#D9EAF7", weight=750)
            setattr(self, attr, node)
            col.addWidget(node)
            q.addSpacing(6)
            q.addLayout(col)
        q.addStretch(1)
        demo = QVBoxLayout()
        demo.setSpacing(6)
        demo.addWidget(label("ÖRNEK VERİ  ·  EMİR KAPALI", size=10, tone="#E7B966", weight=800))
        demo.addWidget(label("Gerçek fiyat değildir", size=9, tone="#7290A8"))
        q.addLayout(demo)
        outer.addWidget(quote)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("WorkstationSplitter")
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(7)
        splitter.addWidget(self._watchlist_panel())
        central = QSplitter(Qt.Orientation.Vertical)
        central.setChildrenCollapsible(False)
        central.setHandleWidth(7)
        central.addWidget(self._screener_panel())
        central.addWidget(self._movers_panel())
        central.setSizes([310, 225])
        splitter.addWidget(central)
        right = QSplitter(Qt.Orientation.Vertical)
        right.setChildrenCollapsible(False)
        right.setHandleWidth(7)
        right.addWidget(self._technical_panel())
        right.addWidget(self._news_panel())
        right.setSizes([315, 220])
        splitter.addWidget(right)
        splitter.setSizes([325, 600, 290])
        outer.addWidget(splitter, 1)

        footer = QHBoxLayout()
        self.status_label = label("Çevrimdışı · Örnek piyasa ekranı", size=10, tone="#92A9BC")
        footer.addWidget(self.status_label)
        footer.addStretch()
        footer.addWidget(label("Yerel prototip  ·  Gerçek emir iletimi kapalı", size=10, tone="#7188A1"))
        outer.addLayout(footer)

        self.setMinimumWidth(780)

    def _watchlist_panel(self):
        p = Panel("İzleme listesi", "İzleme 15")
        tabs = QHBoxLayout()
        tabs.setContentsMargins(11, 9, 11, 6)
        tabs.addWidget(label("İzlemem", size=11, tone="#74B0F1", weight=700))
        tabs.addSpacing(16)
        tabs.addWidget(label("BIST hisseleri", size=10, tone="#7F94AD"))
        tabs.addStretch()
        p.body.addLayout(tabs)
        self.search = QLineEdit()
        self.search.setObjectName("SymbolSearch")
        self.search.setPlaceholderText("Sembol veya şirket ara…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.filter_watchlist)
        searchbox = QHBoxLayout()
        searchbox.setContentsMargins(10, 1, 10, 8)
        searchbox.addWidget(self.search)
        p.body.addLayout(searchbox)
        self.watch = market_table(["Sembol", "Son", "Değ. %", "Hacim"])
        self.watch.setColumnWidth(0, 87)
        for row, data in enumerate(SYMBOLS):
            self.watch.insertRow(row)
            for i, value in enumerate([data[0], data[2], data[3], data[4]]):
                self.watch.setItem(row, i, cell(value, change=i == 2, symbol=i == 0))
            self.watch.item(row, 0).setToolTip(data[1])
        self.watch.cellClicked.connect(self._selected_watch_row)
        self.watch.selectRow(1)
        p.body.addWidget(self.watch, 1)
        return p

    def _selected_watch_row(self, row, col):
        if 0 <= row < self.watch.rowCount():
            self.select_symbol(self.watch.item(row, 0).text())

    def filter_watchlist(self, text):
        needle = text.strip().casefold()
        for r, data in enumerate(SYMBOLS):
            self.watch.setRowHidden(r, bool(needle and
                needle not in data[0].casefold() and needle not in data[1].casefold()))

    def select_symbol(self, symbol):
        data = next((x for x in SYMBOLS if x[0] == symbol), None)
        if data is None:
            return
        self._selected = symbol
        self.symbol_label.setText(data[0])
        self.symbol_full.setText(data[1])
        self.last_label.setText(data[2])
        self.change_label.setText(data[3])
        self.change_label.setStyleSheet(
            "color:" + ("#34D5A2" if data[3].startswith("+") else "#F27A86")
            + ";font-size:12px;font-weight:800;background:transparent;"
        )
        for attr, index in (("high_label", 5), ("low_label", 6),
                            ("vol_label", 4), ("close_label", 7)):
            getattr(self, attr).setText(data[index])

    def _filter_buttons(self):
        line = QHBoxLayout()
        line.setContentsMargins(12, 8, 12, 7)
        line.setSpacing(5)
        for title in ("Hacim artışı", "Momentum", "Gerileyenler"):
            button = small_button(title, name="ScreenerFilter", checked=True)
            button.setChecked(title == self._mode)
            button.clicked.connect(lambda checked=False, mode=title: self.set_scan_mode(mode))
            line.addWidget(button)
            self._tabs[title] = button
        line.addStretch()
        line.addWidget(label("ÖRNEK  ·  5 sonuç", size=10, tone="#6886A5"))
        return line

    def set_scan_mode(self, mode):
        if mode not in self._tabs:
            return
        self._mode = mode
        for name, button in self._tabs.items():
            button.setChecked(name == mode)
        samples = [x for x in SYMBOLS if x[0] != "XU100"]
        if mode == "Gerileyenler":
            samples = [x for x in samples if x[3].startswith("-")]
        elif mode == "Momentum":
            samples = sorted(samples, key=lambda row: float(row[3][1:-1].replace(",", ".")), reverse=True)
        else:
            samples = sorted(samples, key=lambda row: float(row[4].replace(",", ".")), reverse=True)
        self.screener.setRowCount(0)
        for data in samples[:5]:
            row = self.screener.rowCount()
            self.screener.insertRow(row)
            for j, item in enumerate((data[0], data[2], data[3], data[4], "Örnek")):
                self.screener.setItem(row, j, cell(item, change=j==2, symbol=j==0))

    def _screener_panel(self):
        p = Panel("Piyasa taraması", "BIST / örnek")
        p.body.addLayout(self._filter_buttons())
        self.screener = market_table(["Sembol", "Son", "Değ. %", "Hacim M", "Durum"])
        p.body.addWidget(self.screener, 1)
        self.set_scan_mode(self._mode)
        self.screener.cellClicked.connect(
            lambda row, col: self.select_symbol(self.screener.item(row,0).text())
        )
        return p

    def _movers_panel(self):
        p = Panel("Hacim ve sektör görünümü", "Demo veri")
        self.movers = market_table(["Sembol", "Sektör", "Değişim", "Göreli hacim"])
        sectors = [
            ("THYAO", "Ulaştırma", "+2,18%", "2,80×"),
            ("ASELS", "Savunma", "+3,06%", "2,56×"),
            ("GARAN", "Bankacılık", "+1,44%", "2,32×"),
            ("AKBNK", "Bankacılık", "+0,97%", "2,08×"),
            ("TUPRS", "Enerji", "-0,63%", "1,84×"),
            ("EREGL", "Sanayi", "-1,12%", "1,57×"),
        ]
        for row, data in enumerate(sectors):
            self.movers.insertRow(row)
            for i, value in enumerate(data):
                self.movers.setItem(row, i, cell(value, change=i==2, symbol=i==0))
        p.body.addWidget(self.movers, 1)
        self.movers.cellClicked.connect(
            lambda row, col: self.select_symbol(self.movers.item(row,0).text())
        )
        return p

    def _technical_panel(self):
        p = Panel("Teknik görünüm", "Örnek")
        body = QWidget()
        l = QVBoxLayout(body)
        l.setContentsMargins(13, 10, 13, 7)
        l.setSpacing(8)
        for top, value, tone in (
            ("MA 20 / MA 50", "Üzerinde", "#D8E6FA"),
            ("ATR (14)", "1,42%", "#D8E6FA"),
            ("RSI (14)", "58,7", "#61A9D8"),
            ("Momentum", "Pozitif", "#35D6A8"),
        ):
            line = QHBoxLayout()
            line.addWidget(label(top, size=11, tone="#8EA7C2"))
            line.addStretch()
            line.addWidget(label(value, size=11, tone=tone, weight=750))
            l.addLayout(line)
            divider = QFrame()
            divider.setObjectName("MetricDivider")
            divider.setFixedHeight(1)
            l.addWidget(divider)
        l.addWidget(label("GÜN İÇİ FİYAT ARALIĞI", size=10, tone="#83A0BA"))
        track = QFrame()
        track.setFixedHeight(7)
        track.setObjectName("DayRangeTrack")
        l.addWidget(track)
        l.addWidget(label("Düşük                                             Yüksek", size=9, tone="#657E9B"))
        l.addStretch()
        l.addWidget(label(
            "Göstergeler sabit örnek değerlerdir; teknik analiz "
            "motoru çıktısı değildir.",
            size=9, tone="#758CA5",
        ))
        p.body.addWidget(body, 1)
        return p

    def _news_panel(self):
        p = Panel("Haber akışı", "Yerel örnekler")
        wrap = QWidget()
        l = QVBoxLayout(wrap)
        l.setContentsMargins(13, 8, 13, 9)
        l.setSpacing(12)
        sample = [
            ("16:24   MAKRO", "Haftalık veri takvimi: sanayi ve dış ticaret"),
            ("16:12   ŞİRKET", "Ulaştırma sektöründe aylık trafik görünümü"),
            ("15:56   SEKTÖR", "Sanayi şirketlerinde maliyet dinamikleri"),
            ("15:30   MAKRO", "Piyasa izleme: hafta özeti"),
        ]
        for kicker, headline in sample:
            item = QVBoxLayout()
            item.setSpacing(4)
            item.addWidget(label(kicker, size=9, tone="#72A2CE", weight=700))
            text = label(headline, size=11, tone="#DFEBF9", weight=600)
            text.setWordWrap(True)
            item.addWidget(text)
            l.addLayout(item)
            divider = QFrame()
            divider.setObjectName("MetricDivider")
            divider.setFixedHeight(1)
            l.addWidget(divider)
        l.addStretch()
        l.addWidget(label("Örnek haberler; gerçek haber servisi değildir.", size=9, tone="#758CA5"))
        scroll = QScrollArea()
        scroll.setObjectName("NewsScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(wrap)
        p.body.addWidget(scroll, 1)
        return p

    def refresh(self):
        if os.getenv("ANKA_OFFLINE") == "1":
            self.status_label.setText("Çevrimdışı  ·  Örnek veriler  ·  Canlı fiyat yok")
            return
        if self._worker is not None and self._worker.isRunning():
            return
        self._worker = MarketDataWorker(self)
        self._worker.completed.connect(self._apply_snapshot)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def _apply_snapshot(self, snapshot: MarketSnapshot):
        for key, item in self.cards.items():
            item.set_value(snapshot.values.get(key, "—"))
        self.status_label.setText(
            "Veri hatası: " + " / ".join(snapshot.errors)
            if snapshot.errors else "Dış piyasa verileri alındı; lisanslı BIST bağlantısı yok"
        )

    def _worker_finished(self):
        if self._worker is not None:
            self._worker.deleteLater()
        self._worker = None

    def _shutdown_worker(self):
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(9000)
