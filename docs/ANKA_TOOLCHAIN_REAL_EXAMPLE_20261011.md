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

## 2026-10-11 — Görsel arşiv ve kaydedilebilir çalışma alanı

- **Görsel arşiv:** `docs/visual_archive/MANIFEST.json` ile Windows ANKA geliştirme klasörlerinde erişilebilir **10 dosya / 7 farklı ekran görüntüsü** kaydedildi. Her özgün PNG için SHA-256, boyut, kaynak proje ve tekrar eden dosyalar kayıtlı.
- **Tek paket:** `docs/ANKA_Finans_Gorsel_Arsivi_20261011.zip` ve Windows `Documents/ANKA_Finans_Gorsel_Arsivi_20261011.zip`. ZIP bütünlük ve kaynak hash kontrolü PASS. Chat geçmişinde yalnızca görsel olarak üretilen ve dosyası bulunmayan tasarımlar bu arşivde **yok**; onları elde etmiş gibi gösterme.
- **Kaydedilebilir çalışma alanı:** `Düzeni Kaydet` düğmesi artık gerçek `QSettings`/INI dosyasına pencere geometrisi, Qt dock yerleşimi, ayrılmış panel durumu, seçili sembol ve grafik yakınlaştırması kaydeder. Uygulama yeniden açıldığında uyumlu kayıt geri yüklenir.
- **Varsayılana dönüş:** `Düzeni Geri Al` kayıtlı düzeni kaldırıp dock panellerini ana pencereye taşır, THYAO ve varsayılan yakınlaştırmaya döner.
- **Depolama:** Windows kullanıcı profili altında `AppData/Roaming/ANKA Finans/workstation-layout.ini`; testler `ANKA_LAYOUT_FILE` ile izole geçici dosya kullanır. Ayarlar dosyasında API anahtarı tutulmaz.
- **Testler:** `tests/test_toolchain_layout_persistence.py` beş yeni kabul testi ile kayıt/geri yükleme, dosyasız çalışma, eski/sorunlu ayar dosyası ve varsayılan düzeni kontrol eder. **292/292 çevrimdışı bütünleşik birim testi PASS** (exit 0). Geçiş uyarıları ve test içindeki beklenen çevrimdışı/model hataları bu sonuçtan ayrıdır.
- **Sınır:** Genel otonomi / nihai üretim kabulü hâlâ `BLOCKED`. Piyasa verileri, risk ve haberler örnektir; gerçek emir gönderme kapalıdır.
