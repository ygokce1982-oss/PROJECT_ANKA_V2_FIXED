# ANKA Finans — EMA ve Wilder RSI sayısal doğrulaması

**Tarih:** 11 Ekim 2026
**Çalışma dalı:** `feature/anka-verified-chart-indicators-20261011` (ana kod tabanından izole).

## Değişiklikler

- `core/chart_indicators.py`: OHLCV doğrulama; NaN/Inf, uygunsuz yüksek/düşük, negatif hacim ve sıfır/negatif fiyat reddi.
- EMA: ilk geçerli değer, periyot uzunluğundaki fiyatların basit ortalamasıyla başlatılır; sonraki değerlerde katsayı `2/(period+1)` uygulanır. Isınma döneminde `None`.
- RSI (Wilder): önce 14 fiyat farkından ortalama kazanç/kayıp hesaplanır; devamında Wilder yumuşatma `(previous*(period-1)+current)/period`. Kayıp ve kazanç sıfırsa RSI=50, yalnız kazanç varsa 100, yalnız kayıp varsa 0.
- `scripts/anka_professional_toolchain_demo.py`: mum grafiklerindeki eski görsel amaçlı sinüs RSI çizgisi kaldırıldı; gerçek RSI çıktı değerleri kullanılıyor. Üç EMA serisi de yalnızca ekranda görünen mumlardan değil **bütün mevcut mum geçmişinden** hesaplanıp görünür kesite aktarılıyor. Yakınlaştırma göstergenin hesap temelini sıfırlamıyor.
- `tests/test_chart_indicators.py`: 8 matematiksel ve veri güvenliği kabul testi (Wilder referansı, ısınma, trend, yatay fiyat, geçersiz OHLCV, viewport kararlılığı). Önceki 292 regresyon testi korunuyor.
- `docs/previews/ANKA_QtDesigner_DockChart_Real_20261011.png`: yeni hesaplarla gerçek Qt pencere yakalaması.

## Doğrulama

- Sayısal ve Qt hedefli test: **14/14 PASS**.
- Tam çevrimdışı Python unittest: **300/300 PASS**, çıkış kodu 0.
- Qt offscreen ekran oluşturma: **PASS**, 5 dock ve Qt Designer dosyası başarıyla yüklendi.
- Test loglarında beklenen çevrimdışı veri/model hataları ve eski `datetime.utcnow` kullanımlarına yönelik uyarılar bulunuyor; bunlar ayrı bakım alanlarıdır.

## Sınırlar

Piyasa OHLCV verisi **simülasyondur**. Bu değişiklik gösterge formüllerini gerçek fiyatlardan hesaplar ama lisanslı canlı veri bağlamaz, alım-satım başlatmaz. Görüntüdeki risk ve haber değerleri hâlâ örnektir. `FULL_AUTONOMY` ve `PRODUCTION_ACCEPTANCE` henüz PASS değildir.

Ana Windows kaynağındaki 28 yerel kullanıcı değişikliği korunur; kod `main` dalına birleştirilmez. Sıradaki doğrulanabilir işler gerçek veri kaynağı/tazelik damgası, zaman serisi kesintileri ve bağımsız model kod denetimidir.
