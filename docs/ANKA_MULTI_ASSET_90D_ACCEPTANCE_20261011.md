# ANKA Finans — Çoklu Varlık Kümülatif Getiri ve Hareketli Sharpe

Tarih: 2026-10-11 (Türkiye), aday dal: `feature/anka-multi-asset-performance-20261011`.
Referans: Kullanıcının sağladığı **Cumulative Returns (%) / Rolling Sharpe Ratio (90D Window)** ekranı.
Durum: **Gerçek Qt arayüzü + çalışan hesaplama ve yerel CSV girişi; üretim ve canlı veri kabulü DEĞİL.**

## Gerçek özellikler

- Windows ANKA Qt terminalinde **Çoklu Varlık · Getiri ve Sharpe** sekmesi eklendi; ana piyasa grafiği ve beş ayrılabilir panel korunur.
- Ortak takvimde kesişen tarihler; ilk ortak fiyatı %0 kabul ederek kümülatif yüzde getiri `(P_t / P_0 - 1) * 100`.
- Etkin yıllık risksiz getiri, `(1 + rf_annual) ** (1 / 252) - 1` ile dönemsel getiriye çevrilir.
- Hareketli Sharpe: son 90 **ortak getiri gözleminde** aritmetik fazla getirilerin ortalaması / **örnek** standart sapma × `sqrt(252)`; dönem 30, 60, 90, 120 olarak değiştirilebilir.
- Hiç günlük getiri yoksa veya oynaklık sıfırsa Sharpe `None`. 90 günlük Sharpe için en az **91 ortak kapanış** gerekir. Sonsuz değer veya sahte sıfır gösterilmez.
- Varlık seçimi, 1 yıl / 2 yıl / tüm tarih, risksiz faiz düzenleme ve anlık yeniden hesaplama.
- **Yerel CSV Yükle** gerçek çalışır: UTF-8 CSV sütunları **tam olarak** `symbol,date,close,currency`, tarihler ISO `YYYY-MM-DD`, her sembol içinde kesin artan tarihler ve pozitif sonlu fiyatlar. En az iki sembol ve ortak en az iki kapanış gerekir.
- Farklı para birimleri, FX dönüşüm katmanı olmadan **engellenir**. Eksik işlem günleri sessizce doldurulmaz; ortak tarihler dışındaki fiyatlar hesaplamaya dahil edilmez.
- CSV dosyasının değişiklik zamanıyla **son fiyat tarihi ayrı** gösterilir. CSV bağımsız doğrulanmamış kullanıcı kaynağıdır; gerçek zamanlı fiyat akışı gibi sunulmaz.

## Doğruluk ve sınırlamalar

- İlk açılışta 6 sentetik örnek sembolü vardır, 5 tanesi seçilidir; hepsi açıkça **SENTETİK / DEMO** etiketlidir. BIST, ABD, kıymetli maden fiyatları **gerçek piyasa fiyatları DEĞİLDİR**.
- Resimdeki amaçla uyumlu, ancak farklı gerçek para birimlerindeki BIST/USD/altın toplam getirileri için **yetkili FX/takvim/kurumsal aksiyon verisi** bağlamak gerekir; yapılmış değildir.
- Tarih eşlemesi ortak işlem günleri üzerinden yapılır; tatil takvimi ve 365/252 yıllıklandırma varsayımları sonuçları etkiler. Günlük frekans veya kur doğrulanmadığında sonuç üretim amaçlı kullanılmamalıdır.
- Temettü/sermaye hareketleri düzeltilmiş kapanış fiyatı gelmedikçe toplam getiri değil **fiyat getirisi** gösterilir. Bu ayrım kritik.
- Risk, gerçek emir, brokerage, Matriks veri hakları, tam otonomi, bağımsız inceleme hâlâ ayrı kabul kapılarıdır.

## Test ve geri alma

- `tests/test_multi_asset_comparison.py`: sayısal referans, Sharpe sample std, risksiz faiz, ortak tarih, eksik veri, 90 günlük minimum, veri doğrulama ve para birimi kapanları.
- `tests/test_multi_asset_csv.py`: yerel CSV girişi, kaynak bilgisi, hatalı tarihler/fiyatlar, farklı para birimleri.
- `tests/test_multi_asset_performance_ui.py`: gerçek Qt sekmesi, varlık filtresi, 90 günlük pencere, iki grafik, CSV içe aktarma, ana grafiğe geri dönme.
- `docs/previews/ANKA_MultiAsset_Returns_RollingSharpe_20261011.png`: gerçek Qt QWidget görüntüsü, yapay üretim değildir.
- Test başarısızlığı veya üretim yetkilendirme eksikse **main'e birleştirme yapılmaz**. Feature worktree dalı izole; ana `Documents/ANKA_Finans/Professional_20261009` içindeki 28 önceden var olan yerel değişiklik korunur.
- Geliştirme talebi veya kabul değişirse tek yeni feature commit'i `git revert` edilebilir veya çalışma dalı hiç birleştirilmeden bırakılabilir.

## Güvenlik ve sonraki teslim kapıları

1. Dış kaynaklı **gerçek tarihsel fiyatlar + düzeltilmiş kapanış + FX ve tatil takvimi** için kaynak/provenans sözleşmesi, veri tazelik uyarıları.
2. Bağımsız finans matematiği ve Qt etkileşimli kalite denetimi. Gerekirse lisanslı veri yükleyicisini ayrı izole alt modüle dönüştür.
3. 1366×768 ve 1920×1080 performans/okunabilirlik kontrolü; Windows V1 kurulum paketinde entegrasyon.
4. Tam planlayıcı → geliştirici → test → denetçi → rollback zinciri; kanıt yoksa BLOCKED.
