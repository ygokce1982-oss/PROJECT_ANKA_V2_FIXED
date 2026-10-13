## 2026-10-13 — Yerel alarm geçmişi ve tüm sembollerin kontrolü

- Dal `feature/anka-alert-history-20261013`, taban `d78485bdd064028ed6add5fcdbb92789df474de0`. Portföyde salt-okunur alarm geçmişi; manuel kontrol bütün kayıtlı yerel sembolleri işler. SQLite alarm/eşik kuralları korunur; tekrar/eski mum yeni olay üretmez.
- 12 yeni test; tam regresyon **364/364**, geri alma sonrası hedefli/Qt **39/39**; bağımsız inceleme **PASS_WITH_LIMITS**. Taban **19/19**, üç dosyanın birebir SHA256 ile geri yerleştirilmesi ve ana projenin **28/28** korunması doğrulandı.
- 1366×768 ve 1920×1080 gerçek Qt yakalamaları; iki örnek sembol alarmı ve tekrar kontrolde sıfır yeni olay. Çevrimdışı veriler kullanıldı.
- Tarihçenin gösterdiği kayıt sayısı sınırlıdır; sıralama tüm olay imlecini tarar. Otomatik arka plan/cihaz/telefon bildirimi ve canlı veri bu dilimin kabulü değildir. **FULL_AUTONOMY=BLOCKED; PRODUCTION_ACCEPTANCE=BLOCKED.**
- Uzak gönderim bu kayıt anında beklemede; sonrasında ayrı SHA makbuzu tutulur. [Kanıt](ANKA_ALERT_EVIDENCE_20261013.json), [inceleme](ANKA_ALERT_REVIEW_20261013.json).


### Uzak gönderim makbuzu

Kod commit `0bf85bf9260f3528dd76a37cb990abe31f3951e9`, `feature/anka-alert-history-20261013` uzak dalıyla tam SHA eşleşmesiyle doğrulandı (2026-10-13T13:06:30.655301+00:00). Genel otonomi ve üretim kabulü BLOCKED.
