# ANKA Finans — Gerçek araçlarla çalışan kurumsal terminal örneği

**Durum:** Gerçek PySide6/Qt masaüstü prototipi, *yalnızca simülasyon verisi*; nihai ANKA Finans ürünü değildir.

## Araçlar ve doğrulanmış katkıları

| Araç | Gerçek durum | Örneğe katkı |
|---|---|---|
| Qt Widgets Designer | Kurulu (`pyside6-designer`); `pyside6-uic` dosyayı başarıyla derliyor | `ui/anka_chart_workbench.ui`: düzenlenebilir merkezi grafik ve enstrüman bilgi formu. Gerçek uygulama QUiLoader ile bu formu yüklüyor. |
| PySide6 / Qt Widgets | Kurulu ve çalışıyor | Gerçek tablolardan oluşan izleme listesi, arama, kısayollar ve olay işleme. |
| Qt QDockWidget | PySide6 ile birlikte var; **5 adet gerçek dock** | Derinlik ve risk panellerinin ayrılması, sürüklenip ikinci/üçüncü ekrana götürülmesi, haber ve AI sekmeleri. |
| Qt QPainter | PySide6 ile birlikte var; çalışıyor | Örnek OHLC dizisinden *gerçek kodla çizilmiş* mum, hacim, EMA ve RSI grafikleri; fare ile dikey imleç ve tekerlekle yakınlaştırma. |
| Axure RP 11 | Bu PC'de bulunmadı | Şartlı prototip, karmaşık tasarım etkileşimleri için ileride ayrı çalışma; kullanılmış gibi gösterilmedi. |
| KDDockWidgets | Bu PC'de bulunmadı | Ticari/paket uyumluluğu değerlendirilecek; örnekte eşdeğer *yerleşik QDockWidget* kullanıldı. |
| LightningChart Python Trader | Bu PC'de bulunmadı, lisans doğrulanmadı | Örnekte profesyonel grafiğin ticari motoru yerine *yerel Qt QPainter* var. |
| Figma | Önceki dosya mevcut; Starter MCP sınırı | Bu örnek Figma tarafından üretilmedi. |

## Görüntüler

- **Gerçek tek ekran görüntüsü:** `docs/previews/ANKA_QtDesigner_DockChart_Real_20261011.png`
- **Gerçek pencerelerden oluşturulmuş üç ekran düzeni:** `docs/previews/ANKA_QtDock_MultiMonitor_Real_20261011.png`. Bu görsel üç fiziksel monitörün fotoğrafı değil, birbirinden ayrılabilen gerçek Qt pencerelerinin bir araya getirilmiş yakalamalarıdır.

## Çalıştırma

Windows masaüstünde bu klasördeki `ANKA_Gercek_Qt_Ornek_Baslat.cmd` dosyasını açın. Python 3.14 + PySide6 kurulu olmalıdır.

İşlevler: izleme listesi seçimi, Ctrl+K komut araması, sembol arama, kodla çizilen dinamik mum grafiği, fare tekerleğiyle yakınlaştırma, **Panelleri Ayır / Düzeni Geri Al**, sekmeli alt araştırma ve ANKA AI paneli. Emir düğmeleri devre dışı.

## Kabul ve sınırlar

- `tests/test_toolchain_designer_demo.py` altında 6 otomatik test: Designer formunun gerçekten yüklendiği, 5 dock olduğu, sembol seçiminin grafiği değiştirdiği, filtreleme, ayrılabilir ve geri alınabilir dock, gerçek grafik yakalama, devre dışı emirler.
- Tüm değerler, risk hesapları ve haberler **temsili/DEMO**. Canlı veri, lisanslı derinlik, gerçek haber servisi veya gerçek AI yanıtı yok.
- Ana çalışma projesindeki kullanıcıya ait 28 eski dosya değişikliği korunur; `main` dalına otomatik birleştirilmez.
- `FULL_AUTONOMY` ve `PRODUCTION_ACCEPTANCE` henüz PASS değildir.
