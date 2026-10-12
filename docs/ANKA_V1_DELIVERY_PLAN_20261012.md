# ANKA Professional V1 — 19 Ekim 2026 çalışma hedefi

12 Ekim güncellemesi. Mevcut ve sonradan eklenen özellikleri tek kullanılabilir Windows sürümünde toplama hedefi 19 Ekim 2026'dır. Bu tarih, henüz doğrulanmamış canlı veri veya üretim kabulü taahhüdü değildir.

## Güncel küçük geliştirme

Normal `app.py` akışından mevcut gelişmiş mum/EMA/Wilder RSI ve çoklu varlık/Sharpe penceresine erişim sağlanacak. Tek QApplication kullanılacak; altı mevcut sayfa korunacak; pencere tekrar kullanımı ve kapanışı doğrulanacak. DEMO/CSV kaynağı görünür, gerçek emir kapalı kalacak. Bu, bütün arayüzün tamamlandığı iddiası değil, özelliklerin normal giriş noktasından erişimi için ilk entegrasyondur.

Taban: `7bffbebf0ef607c4a334c7e5d249aeece88327d1`. Dal: `feature/anka-integrated-terminal-20261012`. Korunan ana çalışma alanındaki 28 kullanıcı değişikliği üzerine yazılmaz.

## Öncelik ve kabul sırası

1. 12–13 Ekim: ekranları tek uygulamadan erişilebilir hale getirme, pencere yaşam döngüsü ve açık veri etiketleri.
2. 14 Ekim: mevcut SQLite alarmlarına görünür geçmiş, bütün yerel semboller için kontrol, tekrarlanmayan uygulama içi bildirim. Kalıcı alarm deposu zaten vardır; yeniden yapılmaz.
3. 15 Ekim: haber/KAP/takvim, kaynak ve tazelik bilgisi, sağlayıcıdan analize ve kayda veri akışı. Canlı bağlantı ayrı doğrulanır.
4. 16 Ekim: gösterge eksikleri, sanal portföy/risk/backtest/performans akışlarının entegrasyonu. SMA/EMA/RSI tanımları, komisyon ve para birimi varsayımları açık tutulur. MACD/Bollinger/ATR adını taşıyan dal, bu göstergelerin tamamlandığı kanıtı değildir.
5. 17 Ekim: çoklu pencere, düzen kaydı, sembol eşleme, gerçek UI okunabilirliği. Fiziksel monitör ve telefon kabulü ayrıca kanıtlanır.
6. 18 Ekim: dağıtım paketi, temiz kurulum, yedek/geri yükleme ve geri dönüş; AI raporunun uçtan uca kabulü.
7. 19 Ekim: birleşik sürümde gerekli tam regresyon, bağımsız inceleme, açık kusurlar, sürüm manifesti ve uzak SHA ile teslim.

Lisanslı veri, sağlayıcı sözleşmesi, gerçek seans/tarih/düzeltilmiş fiyat kökeni ve cihaz erişimi dış bağımlılıklardır. Eksikleri genel hedeften çıkarılmaz; zamanında sağlanmazlarsa tam kapsam tesliminde gecikme riski olarak kaydedilir. Gerçek emir, satın alma, ödeme ve gizli anahtar işlemleri yapılmaz.

Her turda tek küçük değişiklik, gerekli test, bağımsız inceleme ve sınırlı geri alma kanıtı üretilir. Değişmeyen testler ve genel araç araştırmaları tekrarlanmaz. Başarılı sürüm ayrı dala gönderilir ve uzak SHA doğrulanır. Özel iletişim ve lisans içeriği herkese açık kayıtlara eklenmez.

`FULL_AUTONOMY=BLOCKED`, `PRODUCTION_ACCEPTANCE=BLOCKED`: bu iki durum ancak kendi açık kabul ölçütleri tamamlanırsa değişebilir.


### 12 Ekim gerçekleşen ilk entegrasyon

Normal uygulamadan gelişmiş terminale erişim kaynak, 352 tam test, 27 Qt testi, bağımsız inceleme ve gerçek geri alma provasıyla doğrulandı. Bu ilk küçük entegrasyondur; bütün 12–13 Ekim kapsamı tamamlandı sayılmaz. Sıradaki küçük iş mevcut SQLite üzerinden görünür alarm geçmişi ve bütün yerel sembollerin kontrolüdür.
