## 2026-10-16 — Yerel haber/KAP/takvim yayın yaşı

NEWS/KAP/CALENDAR kayıtları içe aktarılan yayın tarihine göre “Son 24 saat”, “24 saatten eski”, “Gelecek tarih” veya “Tarih geçersiz” gösterir. Ekran UTC hesaplama zamanını ve kaynağın güncelliğinin doğrulanmadığını açıkça belirtir. Yerel yenileme düğmesi kayıtları yeniden okur. Okuma hatasında eski satırlar temizlenir; başarılı içe aktarmayı izleyen okuma hatası gizlenmez.

- Dal `feature/anka-research-age-20261016`; taban `146b5192720b7ce33b90a51bf3c2cc57c74e3d16`. 11 yeni test, **388/388 tam**, geri alma sonrası **18/18 hedefli/Qt**, tabana dönüşte **7/7**. Ayrı koşuların test sayıları toplanmaz.
- Bağımsız inceleme **PASS_WITH_LIMITS**; üç kaynak dosyasının SHA256 değerleri test/inceleme/geri alma sonrası aynıdır. Kanıt: [rapor](ANKA_RESEARCH_AGE_EVIDENCE_20261016.json), [inceleme](ANKA_RESEARCH_AGE_REVIEW_20261016.json).
- İlk inceleme, hatalı içe aktarmanın mevcut satırların hesaplama zamanını gizlediğini buldu. Görünüm durumu korundu; dolu tabloda iki ardışık hata ve ardından yenileme testi eklendi. İlk inceleme ve inceleyicinin geçici klasör temizliğinde başarısız olan ek deneyi saklandı; bağımsız test başarısı iddia edilmez.
- 1366×768 ve 1920×1080 gerçek Qt offscreen yakalamaları incelendi. İlk yakalamada eksik yazı karakterleri görüldü; yalnız yakalama ortamına mevcut Windows fontları yüklendi. İlk kanıt korundu. Uzun alanlar araç ipucuyla tam okunur; tablo yerleşiminin iyileştirilmesi sonraki UI işidir.
- Ana projeye yazılmadı. Bu dilimin başlangıcındaki 54 değişik yol, içerik/HEAD/dal/durum özeti sonunda aynıydı. Tarihsel28 manifesti artık eşit değildir; eski kayıtlar korunur ve günler boyunca değişmediği iddia edilmez.
- 24 saat bir gösterim eşiğidir; canlı sağlayıcı tazeliği veya takvim etkinliği zamanı değildir. Lisanslı canlı akış, kaynağa gitme, otomatik yenileme ve fiziksel cihaz kabulü açık kalır.
- **FULL_AUTONOMY=BLOCKED; PRODUCTION_ACCEPTANCE=BLOCKED.** Uzak gönderim bekleniyor.
