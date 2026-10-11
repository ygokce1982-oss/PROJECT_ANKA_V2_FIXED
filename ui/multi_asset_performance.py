"""Native, interactive Qt multi-asset comparison and risk-adjusted performance.

No image-generation mockups, imported chart screenshots or web calls.
The demo generator intentionally produces SYNTHETIC USD-normalized series.
Live feeds must be wired via AssetHistory with verified provenance later.
"""
from __future__ import annotations
from datetime import date, timedelta
import math
import random

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from core.multi_asset_comparison import AssetHistory, Comparison, compare_assets
from core.multi_asset_csv import load_price_csv

COLORS = ("#47BCF2", "#F0B654", "#31D9B1", "#D97AB9", "#A08AFA", "#EE7181")
DEMO_SYMBOLS = (
    ("GOLD", "Altın / USD (DEMO)", .00103, .0124),
    ("SP500", "S&P 500 / USD (DEMO)", .00058, .0100),
    ("SILVER", "Gümüş / USD (DEMO)", .00066, .0151),
    ("BIST100", "BIST 100 / USD temsili (DEMO)", .00034, .0140),
    ("DXY", "Dolar endeksi / temsili (DEMO)", .00005, .0065),
    ("US20Y", "20Y ABD tahvil / temsili (DEMO)", .00011, .0080),
)


def demo_histories() -> tuple[AssetHistory, ...]:
    """Data is synthetic (not implied licensed market history). No weekends."""
    start = date(2024, 2, 1)
    end = date(2026, 10, 9)
    days = []
    day = start
    while day <= end:
        if day.weekday() < 5:
            days.append(day.isoformat())
        day += timedelta(days=1)
    result = []
    for idx, (symbol, label, trend, volatility) in enumerate(DEMO_SYMBOLS):
        rnd = random.Random(4000 + idx * 17)
        price = 100.0
        rows = []
        for k, current in enumerate(days):
            cycle = math.sin(k/31.0 + idx) * .002
            shock = rnd.gauss(0, volatility)
            price *= max(.75, 1+trend+cycle+shock)
            rows.append((current, price))
        result.append(AssetHistory(
            symbol, "USD", tuple(rows), "SENTETİK / YALNIZ DEMO",
            "2026-10-11T00:00:00+00:00", True,
        ))
    return tuple(result)


def text_label(value, color="#D9E7F7", size=11, bold=False):
    item = QLabel(value)
    item.setStyleSheet(
        f"color:{color};background:transparent;font-size:{size}px;"
        f"font-weight:{750 if bold else 400};border:0;"
    )
    return item


class PerformanceChart(QWidget):
    def __init__(self, mode: str):
        super().__init__()
        self.mode = mode
        self.comparison: Comparison | None = None
        self.selected = set()
        self.setMinimumHeight(185)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def show_comparison(self, result: Comparison):
        self.comparison = result
        self.selected = {r.symbol for r in result.series}
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), QColor("#0C1B2D"))
        w,h=self.width(),self.height()
        left,right,top,bottom=72,37,55,32
        chart_w=max(90,w-left-right)
        chart_h=max(30,h-top-bottom)
        if not self.comparison:
            p.setPen(QColor("#A9BACB"))
            p.drawText(20,35,"Veri bekleniyor")
            return
        result=self.comparison
        p.setPen(QColor("#E8F5FF"))
        title="KÜMÜLATİF GETİRİ (%)" if self.mode=="returns" else (
            f"HAREKETLİ SHARPE ORANI  ·  {result.window} ORTAK İŞLEM GÜNÜ"
        )
        p.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        p.drawText(18,24,title)
        p.setFont(QFont("Segoe UI",8))
        for index,series in enumerate(result.series):
            if series.symbol not in self.selected:
                continue
            color=QColor(COLORS[index%len(COLORS)])
            lx=19+(index%3)*int(max(200,w-50)/3)
            ly=44+(index//3)*12
            p.setPen(QPen(color,2))
            p.drawLine(lx,ly-3,lx+17,ly-3)
            p.setPen(QColor("#AAC0D4"))
            p.drawText(lx+22,ly,series.symbol)
        top=max(top,62+max(0,(len(result.series)-1)//3)*10)
        chart_h=max(30,h-top-bottom)
        points=(
            [series.cumulative_percent for series in result.series]
            if self.mode=="returns"
            else [series.rolling_sharpe for series in result.series]
        )
        finite=[v for series in points for v in series if v is not None and math.isfinite(v)]
        if not finite:
            p.setPen(QColor("#F0B654"))
            p.drawText(left,top+chart_h//2,"Yetersiz veri / hesaplanabilir Sharpe bulunamadı")
            p.end()
            return
        lo,hi=min(finite),max(finite)
        spread=max(1.0,hi-lo)
        lo-=spread*.13
        hi+=spread*.13
        if self.mode=="returns":
            lo=min(lo,0)
            hi=max(hi,0)
        else:
            lo=min(lo,0)
            hi=max(hi,0)
        scale=(hi-lo)
        for i in range(5):
            y=top+chart_h*i/4
            value=hi-scale*i/4
            p.setPen(QPen(QColor("#254056"),.85,Qt.PenStyle.DashLine))
            p.drawLine(QPointF(left,y),QPointF(w-right,y))
            p.setPen(QColor("#A2B7CD"))
            p.drawText(6,int(y)+3,f"{value:+.1f}")
        length=len(result.dates)
        if length<2:
            return
        for i in range(5):
            idx=min(length-1,round(i*(length-1)/4))
            x=left+chart_w*idx/(length-1)
            label=result.dates[idx][:7]
            p.setPen(QColor("#7F9AB4"))
            p.drawText(int(x)-22,h-8,label)
        for index, series in enumerate(result.series):
            if series.symbol not in self.selected:
                continue
            values=points[index]
            path=QPainterPath()
            started=False
            for k,value in enumerate(values):
                if value is None or not math.isfinite(value):
                    started=False
                    continue
                x=left+k/(length-1)*chart_w
                y=top+(hi-value)/scale*chart_h
                if not started:
                    path.moveTo(x,y)
                    started=True
                else:
                    path.lineTo(x,y)
            p.setPen(QPen(QColor(COLORS[index%len(COLORS)]),1.65))
            p.drawPath(path)
        p.setFont(QFont("Segoe UI",9,QFont.Weight.Bold))
        p.setPen(QColor("#D99E54"))
        p.drawText(w-223,20,"SENTETİK / DEMO" if result.demo else "YEREL CSV / DOĞRULANMADI")
        p.end()


class PerformancePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MultiAssetPerformancePanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#MultiAssetPerformancePanel {background-color:#0B1B2C;}")
        self.histories=demo_histories()
        self.comparison: Comparison | None = None
        self.checks: dict[str,QCheckBox]={}
        self._setup()
        self.refresh()

    def _setup(self):
        layout=QVBoxLayout(self)
        layout.setContentsMargins(16,12,16,11)
        layout.setSpacing(10)
        heading=QHBoxLayout()
        heading.addWidget(text_label("VARLIK PERFORMANSI  /  RİSK AYARLI KARŞILAŞTIRMA","#EDF6FF",17,True))
        heading.addStretch()
        self.source_banner=text_label("SENTETİK VERİ · GERÇEK PİYASA BAĞLANTISI YOK","#F0B654",10,True)
        heading.addWidget(self.source_banner)
        layout.addLayout(heading)
        controls=QHBoxLayout()
        controls.addWidget(text_label("DÖNEM","#8CB5CC",10,True))
        self.period=QComboBox()
        self.period.addItems(["1 yıl","2 yıl","Tüm tarih"])
        self.period.setCurrentIndex(1)
        controls.addWidget(self.period)
        controls.addSpacing(18)
        controls.addWidget(text_label("SHARPE PENCERESİ","#8CB5CC",10,True))
        self.window=QComboBox()
        self.window.addItems(["30","60","90","120"])
        self.window.setCurrentText("90")
        controls.addWidget(self.window)
        controls.addSpacing(18)
        controls.addWidget(text_label("YILLIK RİSKSİZ FAİZ %","#8CB5CC",10,True))
        self.rf=QDoubleSpinBox()
        self.rf.setRange(0,30)
        self.rf.setDecimals(2)
        self.rf.setSingleStep(.5)
        self.rf.setSuffix(" %")
        self.rf.setValue(3.0)
        controls.addWidget(self.rf)
        controls.addStretch()
        self.csv_button=QPushButton("Yerel CSV Yükle")
        controls.addWidget(self.csv_button)
        self.refresh_button=QPushButton("Hesaplamayı Yenile")
        self.refresh_button.setObjectName("PrimaryAction")
        controls.addWidget(self.refresh_button)
        layout.addLayout(controls)

        selector=QHBoxLayout()
        selector.addWidget(text_label("VARLIKLAR","#86B6CE",10,True))
        self.asset_select_row=QHBoxLayout()
        selector.addLayout(self.asset_select_row)
        selector.addStretch()
        layout.addLayout(selector)
        self._rebuild_choices(self.histories)
        self.summary=text_label("Hesaplama bekleniyor","#B6D1E5",10)
        layout.addWidget(self.summary)
        self.top_plot=PerformanceChart("returns")
        self.bottom_plot=PerformanceChart("sharpe")
        layout.addWidget(self.top_plot,3)
        layout.addWidget(self.bottom_plot,2)
        self.notice=text_label(
            "KAYNAK: sentetik / demo  •  Para birimi: USD (temsili)  •  Ortak işlem günleri  •  Eksik tarih doldurulmaz",
            "#E9BB72",10
        )
        layout.addWidget(self.notice)
        self.csv_button.clicked.connect(self.choose_csv)
        self.refresh_button.clicked.connect(self.refresh)
        self.period.currentIndexChanged.connect(self.refresh)
        self.window.currentTextChanged.connect(self.refresh)
        self.rf.valueChanged.connect(self.refresh)
    def _rebuild_choices(self,histories):
        while self.asset_select_row.count():
            item=self.asset_select_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.checks={}
        for idx,history in enumerate(histories):
            checkbox=QCheckBox(history.symbol)
            checkbox.setChecked(idx<5)
            checkbox.setStyleSheet(f"color:{COLORS[idx%len(COLORS)]};font-weight:700;")
            checkbox.toggled.connect(self.refresh)
            self.asset_select_row.addWidget(checkbox)
            self.checks[history.symbol]=checkbox

    def choose_csv(self):
        selected,_=QFileDialog.getOpenFileName(
            self,"Geçmiş günlük kapanış CSV dosyası seç","","CSV Dosyaları (*.csv)"
        )
        if selected:
            self.load_csv(selected)

    def load_csv(self,filepath):
        try:
            imported=load_price_csv(filepath)
        except ValueError as exc:
            self.summary.setText("CSV YÜKLEME ENGELLENDİ: "+str(exc))
            return False
        self.histories=imported
        self._rebuild_choices(self.histories)
        self.source_banner.setText("YEREL CSV / BAĞIMSIZ DOĞRULANMADI · CANLI DEĞİL")
        self.refresh()
        return True

    def refresh(self,*unused):
        checked=[h for h in self.histories if self.checks[h.symbol].isChecked()]
        if len(checked)<2:
            self.summary.setText("Karşılaştırma için en az iki varlık seçin.")
            self.top_plot.comparison=None
            self.bottom_plot.comparison=None
            self.top_plot.update()
            self.bottom_plot.update()
            self.comparison=None
            return
        days={0:365,1:730,2:9999}[self.period.currentIndex()]
        max_day=date.fromisoformat(checked[0].observations[-1][0])
        min_day=max_day-timedelta(days=days)
        subset=[]
        for history in checked:
            rows=tuple((d,p) for d,p in history.observations if date.fromisoformat(d)>=min_day)
            subset.append(AssetHistory(history.symbol,history.currency,rows,history.source,history.asof_utc,history.demo))
        try:
            comparison=compare_assets(
                subset,
                window=int(self.window.currentText()),
                risk_free_annual=self.rf.value()/100,
            )
        except ValueError as exc:
            self.summary.setText("HESAPLAMA ENGELLENDİ: "+str(exc))
            self.comparison=None
            self.top_plot.comparison=None
            self.bottom_plot.comparison=None
            self.top_plot.update()
            self.bottom_plot.update()
            return
        self.comparison=comparison
        if comparison.demo:
            self.notice.setText("KAYNAK: sentetik / demo · Para birimi: USD (temsili) · Ortak işlem günleri · Eksik tarih doldurulmaz")
        else:
            self.notice.setText(
                "KAYNAK: Kullanıcının yerel CSV dosyası · Bağımsız doğrulanmadı / canlı değil · "
                f"Son fiyat tarihi: {comparison.dates[-1]} · Dosya zamanı: {checked[0].asof_utc}"
            )
        self.top_plot.show_comparison(comparison)
        self.bottom_plot.show_comparison(comparison)
        self.summary.setText(
            f"{len(comparison.series)} varlık  |  {len(comparison.dates)} ortak fiyat günü  |  "
            f"{comparison.dates[0]} — {comparison.dates[-1]}  |  "
            f"{comparison.window} günlük örnek Sharpe  |  "
            f"Yıllık risksiz faiz %{self.rf.value():.2f}  |  √252 yıllıklandırma"
        )
