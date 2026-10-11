"""Actual Qt Designer + Qt docking + QPainter chart workstation prototype.

Not a rendered mockup: buttons, floating dock panels, hotkeys, chart zoom,
symbol selection, table filtering and layout state are real PySide6 components.
Market data is synthetic and every trading control is disabled.
"""
from __future__ import annotations
import math
import os
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PySide6.QtCore import Qt, QPointF, QRectF, QRect, QSettings
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPainter, QPainterPath, QPen, QShortcut, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QDockWidget, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QPushButton,
    QSizePolicy, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)
from PySide6.QtUiTools import QUiLoader
from core.chart_indicators import validate_ohlcv, ema_series, rsi_wilder_series

BG = "#08121E"
SURFACE = "#0D1A2A"
BORDER = "#1E3249"
PRIMARY = "#E8F1FC"
MUTED = "#7892AF"
GREEN = "#23D9AC"
RED = "#EE6777"
CYAN = "#4AC9F2"
AMBER = "#F0B85F"

QSS = """
QMainWindow{background:#08121E;}
QWidget{color:#E8F1FC;font-family:'Segoe UI';font-size:11px;}
QLabel{background:transparent;border:none;}
QWidget#ChartWorkbench,QWidget#DockContent{background:#08121E;}
QMainWindow::separator{background:#1B2A3E;width:5px;height:5px;}
QToolBar{background:#091A29;color:#D6E7F8;border:0;border-bottom:1px solid #233950;spacing:8px;padding:5px;}
QToolButton{background:#102A3F;color:#D6E7F8;border:1px solid #23445F;border-radius:3px;padding:5px 7px;}
QToolButton:hover{background:#20536D;}
QTabBar{background:#081827;color:#D6E7F8;}
QTabBar::tab{background:#10253A;color:#A9C2D9;border:1px solid #274259;padding:6px 11px;}
QTabBar::tab:selected{background:#173C56;color:#F0F8FF;border-bottom:2px solid #27C9B0;}
QDockWidget{color:#C6DBED;font-size:11px;font-weight:700;titlebar-close-icon:none;titlebar-normal-icon:none;}
QDockWidget::title{background:#112136;padding:9px 12px;text-align:left;border:1px solid #263E57;}
QDockWidget::close-button,QDockWidget::float-button{background:#20384E;border:0;}
QFrame#ShellTop{background:#091A29;border-bottom:1px solid #233950;}
QLabel#AppName{font-size:22px;font-weight:800;color:#F4FAFF;letter-spacing:1px;}
QLabel#DemoBanner{background:#3A2D21;color:#F0C37D;border-radius:4px;padding:5px 10px;font-weight:700;}
QFrame#MarketRibbon{background:#0B1E30;border-bottom:1px solid #1C3549;}
QFrame#SymbolHeader{background:#0E2033;border:1px solid #1E3954;border-radius:2px;}
QLabel#symbolTitle{font-size:17px;font-weight:750;color:#DCEBFA;}
QLabel#symbolPrice{font-size:29px;font-weight:850;color:#E9F5FF;}
QLabel#symbolChange{font-size:15px;font-weight:800;color:#23D9AC;}
QLabel#symbolDemo{font-size:10px;font-weight:750;color:#F0B85F;}
QFrame#ChartToolbar{background:#11253A;border:1px solid #263C54;}
QLabel#chartModeLabel{font-weight:800;color:#77B5D8;}
QLabel#indicatorLabel{color:#83A2C6;font-size:10px;}
QFrame#ChartFooter{background:#112239;border-top:1px solid #243A54;}
QLabel#legendLabel,QLabel#dataSourceLabel{color:#718EA8;font-size:10px;}
QPushButton{background:#19364B;color:#CADCEC;border:1px solid #2C4A63;border-radius:4px;padding:5px 10px;min-height:19px;}
QPushButton:hover{background:#21516B;}
QPushButton:disabled{background:#25303C;color:#677D90;border-color:#334354;}
QPushButton#PrimaryAction{background:#0C786A;color:#E1FFF4;border-color:#11AA93;font-weight:750;}
QPushButton#FloatAction{background:#133855;color:#85CFF5;border-color:#2D6282;font-weight:700;}
QLineEdit,QComboBox{background:#0C1B2A;color:#DCE9F5;border:1px solid #2D485F;padding:6px 8px;border-radius:3px;}
QTableWidget{background:#0C1B2A;alternate-background-color:#112438;color:#DDEBF8;border:0;gridline-color:#20374D;selection-background-color:#205073;selection-color:#ECFAFF;}
QHeaderView::section{background:#10253A;color:#83A1BC;border:0;border-bottom:1px solid #2B465F;padding:7px 4px;font-size:10px;font-weight:700;}
QScrollBar:vertical{background:#0D1B2B;width:8px;}
QScrollBar::handle:vertical{background:#30506B;min-height:28px;border-radius:3px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px;}
QStatusBar{background:#0B1B2A;color:#9AADC2;border-top:1px solid #28435B;}
QSplitter::handle{background:#1D344B;}
"""

TICKERS = [
    ("THYAO","Türk Hava Yolları",312.75,2.18,8.42),
    ("ASELS","Aselsan",168.40,3.06,6.81),
    ("GARAN","Garanti BBVA",148.20,1.44,5.23),
    ("AKBNK","Akbank",72.65,0.97,4.78),
    ("TUPRS","Tüpraş",188.90,-0.63,3.96),
    ("EREGL","Ereğli",29.84,-1.12,2.88),
    ("BIMAS","BİM",596.50,0.84,2.65),
    ("KCHOL","Koç Holding",214.60,1.36,2.12),
    ("SISE","Şişecam",46.82,-0.42,1.94),
    ("PGSUS","Pegasus",246.60,2.80,2.21),
    ("SASA","Sasa Polyester",3.59,-0.28,1.47),
    ("ISCTR","İş Bankası C",14.28,2.49,2.16),
]


def tl(value, digits=2):
    return f"{value:,.{digits}f}".replace(",", "~").replace(".", ",").replace("~",".")


def qt_label(text, size=11, color=MUTED, bold=False):
    l = QLabel(text)
    l.setStyleSheet(f"color:{color};font-size:{size}px;font-weight:{800 if bold else 400};")
    return l


def table(headers):
    t = QTableWidget(0,len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    t.verticalHeader().hide()
    t.verticalHeader().setDefaultSectionSize(30)
    t.setShowGrid(False)
    t.setAlternatingRowColors(True)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    return t


def fill(t, row):
    i = t.rowCount()
    t.insertRow(i)
    for col,v in enumerate(row):
        c=QTableWidgetItem(str(v))
        if col==0:
            f=c.font()
            f.setBold(True)
            c.setFont(f)
        if str(v).startswith("+"): c.setForeground(QColor(GREEN))
        if str(v).startswith("-"): c.setForeground(QColor(RED))
        t.setItem(i,col,c)


def panel_widget(layout_builder=None):
    w=QWidget()
    w.setObjectName("DockContent")
    l=QVBoxLayout(w)
    l.setContentsMargins(10,9,10,10)
    l.setSpacing(8)
    if layout_builder:layout_builder(l)
    return w


def demo_candles(symbol, count=125):
    rnd=random.Random(sum(ord(c) for c in symbol)*11)
    base=next((x[2] for x in TICKERS if x[0]==symbol), 100)
    closes=[]
    price=base*.83
    for i in range(count):
        drift=.00085+math.sin(i/12)*.002
        delta=price*(drift+rnd.uniform(-.012,.012))
        op=price
        close=max(1,op+delta)
        high=max(op,close)*(1+rnd.uniform(.002,.008))
        low=min(op,close)*(1-rnd.uniform(.002,.008))
        vol=int(50000*(.4+rnd.random()*1.6))
        closes.append((op,high,low,close,vol))
        price=close
    return closes


class Canvas(QWidget):
    def __init__(self, symbol="THYAO"):
        super().__init__()
        self.setMouseTracking(True)
        self.setMinimumSize(460,330)
        self.symbol=symbol
        self.series=demo_candles(symbol)
        self.visible=78
        self.cursor_x=None

    def choose(self, symbol):
        self.symbol=symbol
        self.series=demo_candles(symbol)
        self.update()

    def wheelEvent(self,event):
        self.visible=max(32,min(125,self.visible+(-7 if event.angleDelta().y()>0 else 7)))
        self.update()

    def mouseMoveEvent(self,event):
        self.cursor_x=event.position().x()
        self.update()

    def leaveEvent(self,event):
        self.cursor_x=None
        self.update()

    def paintEvent(self,event):
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing,True)
        width,height=self.width(),self.height()
        p.fillRect(self.rect(), QColor("#081725"))
        left,top,right=55,43,75
        usable=max(100,width-left-right)
        main_h=(height-top-52)*.64
        volume_top=top+main_h+9
        vol_h=(height-top-52)*.13
        rsi_top=volume_top+vol_h+15
        rsi_h=max(32,(height-45)-rsi_top)
        # Indicators use the *full* candle history, independent of zoom.
        closes = validate_ohlcv(self.series)
        ema_tracks = {
            period: ema_series(closes, period)[-self.visible:]
            for period in (12, 26, 48)
        }
        rsi_track = rsi_wilder_series(closes, 14)[-self.visible:]
        series=self.series[-self.visible:]
        maxp=max(x[1] for x in series)*1.025
        minp=min(x[2] for x in series)*.975
        ys=lambda v:top+(maxp-v)/(maxp-minp)*main_h
        step=usable/len(series)
        for i in range(6):
            y=top+i*(main_h/5)
            p.setPen(QPen(QColor("#1D3043"),1,Qt.PenStyle.DashLine))
            p.drawLine(int(left),int(y),int(width-right+5),int(y))
            p.setPen(QColor("#7C97B3"))
            p.setFont(QFont("Segoe UI",8))
            p.drawText(int(width-right+10),int(y)+3,f"{maxp-i*(maxp-minp)/5:.2f}")
        for k,name,color in ((12,"EMA 12",CYAN),(26,"EMA 26",AMBER),(48,"EMA 48","#745EEE")):
            path=QPainterPath()
            started=False
            for i,v in enumerate(ema_tracks[k]):
                if v is None:
                    started=False
                    continue
                x=left+(i+.5)*step
                y=ys(v)
                if not started:
                    path.moveTo(x,y)
                    started=True
                else:
                    path.lineTo(x,y)
            p.setPen(QPen(QColor(color),1.5))
            p.drawPath(path)
        for i,(o,h,l,c,v) in enumerate(series):
            x=left+(i+.5)*step
            color=QColor(GREEN if c>=o else RED)
            p.setPen(QPen(color,1.1))
            p.drawLine(QPointF(x,ys(h)),QPointF(x,ys(l)))
            bw=max(2,step*.64)
            p.fillRect(QRectF(x-bw/2,min(ys(o),ys(c)),bw,max(1.4,abs(ys(o)-ys(c)))),color)
            p.fillRect(QRectF(x-bw/2,volume_top+vol_h*(1-v/145000),bw,max(1,vol_h*v/145000)),color.darker(140))
        p.setPen(QColor("#8297B2"));p.setFont(QFont("Segoe UI",9))
        p.drawText(left,22,f"{self.symbol}  |  DEMO MUM GRAFİĞİ")
        p.setPen(QColor(CYAN));p.drawText(left+185,22,"EMA 12")
        p.setPen(QColor(AMBER));p.drawText(left+245,22,"EMA 26")
        p.setPen(QColor("#9074FF"));p.drawText(left+310,22,"EMA 48")
        p.setPen(QColor("#718DA6"));p.drawText(left,int(volume_top-3),"HACİM")
        for i in range(4):
            y=rsi_top+i*rsi_h/3
            p.setPen(QPen(QColor("#213B50"),1,Qt.PenStyle.DashLine))
            p.drawLine(left,int(y),width-right,int(y))
        p.setPen(QColor("#718DA6"));p.drawText(left,int(rsi_top+12),"RSI (14) / DEMO FİYATLARDAN HESAP")
        path=QPainterPath()
        started=False
        for i,val in enumerate(rsi_track):
            if val is None:
                started=False
                continue
            x=left+(i+.5)*step
            y=rsi_top+rsi_h*(1-val/100)
            if not started:
                path.moveTo(x,y)
                started=True
            else:
                path.lineTo(x,y)
        p.setPen(QPen(QColor("#C178D9"),1.4))
        p.drawPath(path)
        if self.cursor_x is not None and left<self.cursor_x<width-right:
            p.setPen(QPen(QColor("#80B5D3"),1,Qt.PenStyle.DashLine))
            p.drawLine(int(self.cursor_x),top,int(self.cursor_x),height-15)
        p.end()


class Terminal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ANKA Finans | Profesyonel Araçlarla Gerçek Qt Prototipi")
        self.resize(1660,980)
        self.setMinimumSize(1100,700)
        self.setDockOptions(QMainWindow.DockOption.AllowNestedDocks | QMainWindow.DockOption.AllowTabbedDocks | QMainWindow.DockOption.AnimatedDocks)
        self.chart=Canvas()
        self._dock={}
        self._layout_file = self._settings_file()
        self._build()
        self._load_layout()
        self.statusBar().showMessage("SİMÜLASYON · GERÇEK VERİ YOK · EMİR GÖNDERİMİ KAPALI     |     Paneller sürüklenebilir, ayrılabilir ve kaydedilebilir.")
        QShortcut(QKeySequence("Ctrl+K"),self,activated=self.symbolSearch.setFocus)

    def _build(self):
        loader=QUiLoader()
        path=ROOT/"ui"/"anka_chart_workbench.ui"
        form=loader.load(str(path))
        if form is None:raise RuntimeError("Qt Designer .ui could not load")
        self.form=form
        self.symbol_title=form.findChild(QLabel,"symbolTitle")
        self.symbol_price=form.findChild(QLabel,"symbolPrice")
        self.symbol_change=form.findChild(QLabel,"symbolChange")
        slot=form.findChild(QWidget,"chartSlot")
        slot.layout().addWidget(self.chart)
        self.setCentralWidget(form)
        self._create_toolbars()
        self._create_watchlist()
        self._create_depth()
        self._create_risk()
        self._create_news()
        self._create_analysis()
        form.findChild(QPushButton,"saveLayoutButton").clicked.connect(self.save_layout)
        for val,visible in ((1,48),(2,78),(3,100),(4,125)):
            form.findChild(QPushButton,f"range{val}").clicked.connect(
                lambda checked=False,n=visible:self.set_chart_zoom(n)
            )
        self.resizeDocks([self._dock["İzleme Listesi"],self._dock["Piyasa Derinliği"]],[285,285],Qt.Orientation.Horizontal)
        self.resizeDocks([self._dock["Haber ve Araştırma"]],[185],Qt.Orientation.Vertical)

    def _create_toolbars(self):
        bar=self.addToolBar("Terminal Komutları")
        bar.setMovable(False)
        bar.setIconSize(__import__("PySide6").QtCore.QSize(14,14))
        badge=qt_label("◈  ANKA FİNANS",18,PRIMARY,True)
        bar.addWidget(badge)
        bar.addSeparator()
        bar.addWidget(qt_label("KURUMSAL ANALİZ TERMINALİ",10,MUTED))
        bar.addSeparator()
        self.symbolSearch=QLineEdit()
        self.symbolSearch.setPlaceholderText("Sembol ara veya komut yaz  ·  Ctrl+K")
        self.symbolSearch.setFixedWidth(315)
        self.symbolSearch.returnPressed.connect(self.search_enter)
        bar.addWidget(self.symbolSearch)
        bar.addSeparator()
        for item in ("Piyasa","Grafik","Tarayıcı","Portföy","Risk","Haberler","ANKA AI"):
            action=bar.addAction(item)
            if item=="Risk":action.triggered.connect(lambda checked=False:self._dock["Portföy ve Risk"].raise_())
            if item=="Haberler":action.triggered.connect(lambda checked=False:self._dock["Haber ve Araştırma"].raise_())
        spacer=QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred)
        bar.addWidget(spacer)
        demo=qt_label("● DEMO /  GÜVENLİ ANALİZ",10,AMBER,True)
        bar.addWidget(demo)
        self.floatAction=bar.addAction("Panelleri Ayır")
        self.floatAction.triggered.connect(self.float_panels)
        self.restoreAction=bar.addAction("Düzeni Geri Al")
        self.restoreAction.triggered.connect(self.restore_default)

        stripe=self.addToolBar("Örnek Piyasa Bandı")
        stripe.setMovable(False)
        stripe.setObjectName("RibbonBar")
        for txt in ("BIST 100   11.765,42   +1,24%",
                    "BIST 30   13.428,16   +1,48%",
                    "USD/TRY   43,28   +0,08%",
                    "ALTIN   5.842,60   +0,67%",
                    "BRENT   77,18   +0,52%",
                    "NASDAQ   18.372,14   -0,21%"):
            stripe.addWidget(qt_label("  "+txt+"   |",10,PRIMARY,True))
        stripe.addWidget(qt_label("  TEMSİLİ",9,AMBER,True))

    def _dockWidget(self, name,widget,area,minw=185):
        dock=QDockWidget(name,self)
        dock.setObjectName("Dock_"+str(len(self._dock)))
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                         QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                         QDockWidget.DockWidgetFeature.DockWidgetClosable)
        widget.setMinimumWidth(minw)
        dock.setWidget(widget)
        self.addDockWidget(area,dock)
        self._dock[name]=dock
        return dock

    def _create_watchlist(self):
        def content(l):
            l.addWidget(qt_label("İZLEME LİSTESİ  /  BIST · ABD · DÖVİZ",11,CYAN,True))
            self.watchSearch=QLineEdit()
            self.watchSearch.setPlaceholderText("Sembol / şirket filtrele")
            self.watchSearch.textChanged.connect(self.filter_watch)
            l.addWidget(self.watchSearch)
            self.watch=table(["Sembol","Son","Değişim","Hacim"])
            for sym,name,price,change,vol in TICKERS:
                fill(self.watch,[sym,tl(price),f"{change:+.2f}%",f"{vol:.2f}M"])
            self.watch.cellClicked.connect(self.select_row)
            l.addWidget(self.watch)
            l.addWidget(qt_label("Örnek piyasa tablosu · 12 varlık",10,MUTED))
        self._dockWidget("İzleme Listesi",panel_widget(content),Qt.DockWidgetArea.LeftDockWidgetArea,260)

    def _create_depth(self):
        def content(l):
            l.addWidget(qt_label("THYAO   ·   ALIŞ / SATIŞ MERDİVENİ",11,CYAN,True))
            grid=table(["Alış adet","Alış","Satış","Satış adet"])
            for i in range(12):
                b=312.5-i*.25
                a=312.75+i*.25
                fill(grid,[f"{171400-i*5620:,}",tl(b),tl(a),f"{140200+i*3480:,}"])
                grid.item(i,1).setForeground(QColor(GREEN))
                grid.item(i,2).setForeground(QColor(RED))
            l.addWidget(grid)
            l.addWidget(qt_label("DERİNLİK VERİSİ: TAMAMEN SİMÜLE",10,AMBER,True))
            l.addWidget(qt_label("Alış hacmi  ███████░░     Satış hacmi  ██████░░░",10,MUTED))
        self._dockWidget("Piyasa Derinliği",panel_widget(content),Qt.DockWidgetArea.RightDockWidgetArea,260)

    def _create_risk(self):
        def content(l):
            l.addWidget(qt_label("PORTFÖY / RİSK GÖSTERGELERİ",11,CYAN,True))
            for title,value,color in (
                ("Sanal portföy","₺ 1.248.320,50",PRIMARY),
                ("Günlük değişim","+%1,19",GREEN),
                ("VaR (%95)","-%2,18",RED),
                ("Beta","1,14",PRIMARY),
                ("Maks. düşüş","-%8,42",RED),
                ("Sharpe oranı","1,32",GREEN),
            ):
                line=QHBoxLayout()
                line.addWidget(qt_label(title,11,MUTED))
                line.addStretch()
                line.addWidget(qt_label(value,12,color,True))
                l.addLayout(line)
            l.addWidget(qt_label("İşlem paneli devre dışı",10,AMBER,True))
            order=QPushButton("AL / SAT  ·  GERÇEK EMİR KAPALI")
            order.setEnabled(False)
            l.addWidget(order)
        w=panel_widget(content)
        dock=self._dockWidget("Portföy ve Risk",w,Qt.DockWidgetArea.RightDockWidgetArea,265)
        self.splitDockWidget(self._dock["Piyasa Derinliği"],dock,Qt.Orientation.Vertical)

    def _create_news(self):
        def content(l):
            l.addWidget(qt_label("HABER AKIŞI  /  ARAŞTIRMA   ·   ÖRNEK KAYITLAR",11,CYAN,True))
            news=table(["Zaman","Kaynak","Başlık","Etiket"])
            for row in (
                ("19:12","Örnek","TCMB faiz kararı öncesi piyasa beklentileri","MAKRO"),
                ("18:47","Örnek","THYAO kapasite ve yolcu büyümesi değerlendirmesi","ŞİRKET"),
                ("18:31","Örnek","Bankacılık sektörü net faiz marjı karşılaştırması","ARAŞTIRMA"),
                ("18:18","Örnek","Küresel volatilite ve risk iştahında güncel görünüm","RİSK"),
                ("18:03","Örnek","BIST 100 teknik seviyeler ve sektör eğilimleri","TEKNİK"),
            ):
                fill(news,row)
            l.addWidget(news)
        self._dockWidget("Haber ve Araştırma",panel_widget(content),Qt.DockWidgetArea.BottomDockWidgetArea,450)

    def _create_analysis(self):
        def content(l):
            l.addWidget(qt_label("ANKA AI  /  BAĞIMSIZ ANALİZ TASLAĞI",11,CYAN,True))
            l.addWidget(qt_label("Model: Claude / Gemini  ·  burada çağrı yapılmıyor",10,MUTED))
            for t in (
                "• THYAO · çoklu zaman dilimi eğilim karşılaştırması",
                "• Kritik destek / direnç bölgelerini denetle",
                "• Portföy yoğunlaşma ve korelasyon riskini incele",
                "• Bilgi kaynakları ve gecikme durumunu kontrol et",
            ):
                l.addWidget(qt_label(t,11,PRIMARY))
            l.addStretch()
            l.addWidget(qt_label("Bu panel tasarım amaçlıdır. Model çıktısı değildir.",10,AMBER))
        self._dockWidget("ANKA AI / Denetim",panel_widget(content),Qt.DockWidgetArea.BottomDockWidgetArea,350)
        self.tabifyDockWidget(self._dock["Haber ve Araştırma"],self._dock["ANKA AI / Denetim"])
        self._dock["Haber ve Araştırma"].raise_()

    def select_row(self,row,column):
        if 0<=row<self.watch.rowCount():
            sym=self.watch.item(row,0).text()
            self.choose_symbol(sym)

    def choose_symbol(self,sym):
        found=next((v for v in TICKERS if v[0]==sym),None)
        if found is None:return
        code,name,price,change,vol=found
        self.symbol_title.setText(f"{code}   {name.upper()}")
        self.symbol_price.setText(tl(price))
        self.symbol_change.setText(f"{change:+.2f}%")
        self.symbol_change.setStyleSheet(f"color:{GREEN if change>=0 else RED};font-weight:800;font-size:15px;")
        self.chart.choose(code)
        self.statusBar().showMessage(f"{code} seçildi · örnek mum grafiği güncellendi · gerçek veri veya emir yok")

    def filter_watch(self,txt):
        value=txt.casefold().strip()
        for i,item in enumerate(TICKERS):
            visible=not value or value in item[0].casefold() or value in item[1].casefold()
            self.watch.setRowHidden(i,not visible)

    def search_enter(self):
        sym=self.symbolSearch.text().strip().upper()
        self.choose_symbol(sym)

    def set_chart_zoom(self,visible):
        self.chart.visible=visible
        self.chart.update()

    def float_panels(self):
        self._dock["Piyasa Derinliği"].setFloating(True)
        self._dock["Portföy ve Risk"].setFloating(True)
        self.statusBar().showMessage("Paneller ayrıldı. Diğer monitöre sürükleyebilir veya başlığa çift tıklayarak yerleştirebilirsiniz.")

    def restore_default(self):
        try:
            if self._layout_file.is_file():
                self._layout_file.unlink()
        except OSError:
            self.statusBar().showMessage("Kayıtlı düzen temizlenemedi; geçerli görünüm korunuyor", 7500)
            return False
        for dock in self._dock.values():
            dock.setFloating(False)
            dock.show()
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._dock["İzleme Listesi"])
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._dock["Piyasa Derinliği"])
        self.splitDockWidget(
            self._dock["Piyasa Derinliği"],
            self._dock["Portföy ve Risk"],
            Qt.Orientation.Vertical,
        )
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._dock["Haber ve Araştırma"])
        self.tabifyDockWidget(self._dock["Haber ve Araştırma"], self._dock["ANKA AI / Denetim"])
        self._dock["Haber ve Araştırma"].raise_()
        self.choose_symbol("THYAO")
        self.set_chart_zoom(78)
        self.statusBar().showMessage("Varsayılan çalışma alanına dönüldü; kayıtlı düzen temizlendi", 7500)
        return True

    def _settings_file(self):
        supplied = os.environ.get("ANKA_LAYOUT_FILE", "").strip()
        if supplied:
            return Path(supplied).expanduser()
        profile = os.environ.get("APPDATA") or str(Path.home() / ".config")
        return Path(profile) / "ANKA Finans" / "workstation-layout.ini"

    def _load_layout(self):
        if not self._layout_file.is_file():
            return False
        try:
            config = QSettings(str(self._layout_file), QSettings.Format.IniFormat)
            if config.value("layout/schema", 0, type=int) != 1:
                return False
            geometry = config.value("layout/geometry")
            state = config.value("layout/state")
            if geometry is None or state is None:
                return False
            # QT restores native dock positions, floating states and visibility.
            restored = self.restoreState(state, 1)
            if not restored:
                return False
            self.restoreGeometry(geometry)
            sym = str(config.value("layout/symbol", "THYAO"))
            if sym in {row[0] for row in TICKERS}:
                self.choose_symbol(sym)
            zoom = config.value("layout/chart_count", 78, type=int)
            if isinstance(zoom, int) and 32 <= zoom <= 125:
                self.set_chart_zoom(zoom)
            return config.status() == QSettings.Status.NoError
        except (OSError, TypeError, ValueError, RuntimeError):
            return False

    def save_layout(self):
        try:
            self._layout_file.parent.mkdir(parents=True, exist_ok=True)
            config = QSettings(str(self._layout_file), QSettings.Format.IniFormat)
            config.setAtomicSyncRequired(True)
            config.setValue("layout/schema", 1)
            config.setValue("layout/geometry", self.saveGeometry())
            config.setValue("layout/state", self.saveState(1))
            config.setValue("layout/symbol", self.chart.symbol)
            config.setValue("layout/chart_count", self.chart.visible)
            config.sync()
            if config.status() != QSettings.Status.NoError:
                raise OSError("Layout persistence I/O failed")
            self.statusBar().showMessage("Çalışma alanı kaydedildi; bir sonraki açılışta geri yüklenecek", 7500)
            return True
        except (OSError, TypeError, ValueError, RuntimeError):
            self.statusBar().showMessage("Çalışma alanı kaydedilemedi; geçerli düzen korunuyor", 7500)
            return False

    def closeEvent(self,event):
        for d in self._dock.values():
            d.setFloating(False)
        super().closeEvent(event)


def main():
    offscreen = "--screenshot" in sys.argv or "--multi-screenshot" in sys.argv
    os.environ.setdefault("QT_QPA_PLATFORM","offscreen" if offscreen else "windows")
    app=QApplication([])
    fonts=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
    for font_name in ('segoeui.ttf','segoeuib.ttf','arial.ttf','arialbd.ttf'):
        font_path=fonts/font_name
        if font_path.exists():
            QFontDatabase.addApplicationFont(str(font_path))
    app.setFont(QFont('Segoe UI', 9))
    app.setApplicationName("ANKA Finans - Gerçek Qt Araç Entegrasyonu")
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)
    win=Terminal()
    win.show()
    app.processEvents()
    if "--screenshot" in sys.argv:
        dest=ROOT/"docs"/"previews"/"ANKA_QtDesigner_DockChart_Real_20261011.png"
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not win.grab().save(str(dest),"PNG"):
            raise SystemExit("SCREENSHOT_SAVE_FAILED")
        print("SCREENSHOT_PASS="+str(dest),flush=True)
        print("DOCKS="+str(len(win._dock))+";QT_DESIGNER_LOADED="+str(bool(win.form)),flush=True)
        win.close()
        return 0
    if "--multi-screenshot" in sys.argv:
        win.float_panels()
        app.processEvents()
        main_image=win.grab()
        depth_image=win._dock["Piyasa Derinliği"].grab()
        risk_image=win._dock["Portföy ve Risk"].grab()
        news_image=win._dock["Haber ve Araştırma"].grab()
        win._dock["ANKA AI / Denetim"].raise_()
        app.processEvents()
        ai_image=win._dock["ANKA AI / Denetim"].grab()
        composite=QPixmap(2780,990)
        composite.fill(QColor("#08121E"))
        painter=QPainter(composite)
        painter.setPen(QColor("#56C3E9"))
        f=QFont("Segoe UI",13)
        f.setBold(True)
        painter.setFont(f)
        painter.drawText(25,34,"MONİTÖR 1  /  GRAFİK VE İZLEME")
        painter.drawText(1500,34,"MONİTÖR 2  /  DERİNLİK VE RİSK")
        painter.drawText(2180,34,"MONİTÖR 3  /  HABER VE ANKA AI")
        for x,y,w,h,pic in (
            (16,52,1450,860,main_image),
            (1490,52,665,392,depth_image),
            (1490,488,665,425,risk_image),
            (2180,52,575,392,news_image),
            (2180,488,575,425,ai_image),
        ):
            painter.setPen(QPen(QColor("#2B536E"),2))
            painter.drawRect(x-2,y-2,w+4,h+4)
            if not pic.isNull():
                painter.drawPixmap(QRect(x,y,w,h),pic)
        painter.end()
        target=ROOT/"docs"/"previews"/"ANKA_QtDock_MultiMonitor_Real_20261011.png"
        target.parent.mkdir(parents=True,exist_ok=True)
        if not composite.save(str(target),"PNG"):
            raise SystemExit("MULTI_SCREENSHOT_SAVE_FAILED")
        print("MULTI_SCREENSHOT_PASS="+str(target),flush=True)
        print("FLOATING_DOCKS="+str(sum(d.isFloating() for d in win._dock.values())),flush=True)
        win.close()
        return 0
    return app.exec()


if __name__=="__main__":
    raise SystemExit(main())
