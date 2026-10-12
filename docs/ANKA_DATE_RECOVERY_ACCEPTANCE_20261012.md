# ANKA Finans — 12 Ekim 2026 tarih doğrulaması kurtarma kabulü

Kayıt zamanı: 2026-10-12T15:24:39+03:00. Dal: `fix/anka-price-date-recovery-20261012`; taban `0d8318d4171254ad8d25b3f791076b16a63ce9c5`.

## Sonuç ve kapsam

Dar çevrimdışı tarih düzeltmesi bağımsız kaynak incelemesi ve geri alma provasıyla kabul edildi. Genel `FULL_AUTONOMY=BLOCKED`, `PRODUCTION_ACCEPTANCE=BLOCKED`. Bu dalın gönderimi veya yerel testleri üretim/gerçek piyasa onayı değildir; `main` birleştirmesi yapılmadı.

Fiyat karşılaştırması artık tek UTC saat örneği kullanır. UTC bugünden sonraki **her fiyat satırını**, ortak tarih kesişimine girmese bile `FUTURE_PRICE_DATE` ile reddeder. Çekirdek girdisinde yalnız `YYYY-MM-DD` kabul edilir; Python'un temel ISO ve hafta-tarih alternatifleri reddedilir. Geçmiş/bugünkü fiyatlar kabul edilir. Kaynak zamanında tam +5 dakika kabul edilir; +5 dakika +1 mikrosaniye reddedilir, saat dilimi dönüşümü korunur.

Kaynak kod değişikliği 6 ekleme / 1 silmedir; yalnız `core/multi_asset_comparison.py` ve yeni 18 test içeren `tests/test_multi_asset_future_date_guards.py` etkilenir. CSV içe aktarıcısının mevcut çevre boşluklarını kırpması sürer. Dosya mtime bilgisi piyasa-asof zamanı değildir; satır tarihi <=mtime şartı eklenmedi.

## Güncel kanıt

| Kapı | Sonuç |
|---|---|
| Yeni deterministik testler | Tabanda 18 test / beklenen 11 assertion hatası, exit 1; düzeltmede 18/18, exit 0 |
| Hedefli testler | 37/37, exit 0; geri alma sonrasında tekrar doğrulandı |
| Tam regresyon | 344/344, sıfır hata/atlama; 99.636 s test, 132.499 s import dahil toplam |
| Ayrı Qt offscreen smoke | 19/19, exit 0 |
| Gerçek Qt görüntüsü | 1366×768 ve 1920×1080; okunabilir etiketler, gelecek CSV reddi, gerçek emir kapalı |
| Önceki bağımsız denetçi test kanıtı | 42/42 (37 hedefli +5 ayrı sınır durumu), exit 0; nihai karar öncesi oturumu kota hatasıyla kesildi |
| Tamamlanan bağımsız kaynak incelemesi | `PASS_WITH_LIMITS`; ayrı bağlamlı inceleyici, kaynak hashleri eşleşti |
| Geri alma güvenliği incelemesi | `PASS_WITH_LIMITS`; ayrıntı ayrı JSON raporunda |
| Yeni aday geri alma provası | İki dosya yedeklendi, tabana dönüşte 19/19, aday byte hashleri birebir geri yüklendi |
| Korunan kullanıcı projesi | 28/28 SHA256, dal, HEAD ve Git durum kaydı aynı |

Testler, proje/sağlayıcı importlarından önce Python audit ağ çağrıları ve gerçek alt süreç başlatmalarını engelleyen yerel sarmalayıcıyla çalıştırıldı. Gerçek dış çağrı denemesi görülmedi. Bu, OS güvenlik duvarı veya tüm native kodu kapsayan sandbox iddiası değildir. Qt ayar dosyaları test alanında izole edildi.

## Önceki başarısız adayın çözümü

`fix/anka-future-ohlcv-date-20261012` dalındaki iki ajan dosyasının özgün byte kopyası, patch ve SHA256 manifesti görev kanıt alanında korundu. Kaynak, `0d8318d` tabanına döndürüldü; izlenmeyen test tek dosya olarak kanıt alanına taşındı. Eski çalışma ağacı temizdir. Ana `Documents/ANKA_Finans/Professional_20261009` dosyalarına yazılmadı.

Özgün izin reddi mesajı erişilebilir kayıtlarda yoktur. Desktop Commander geçmişinde testler görülür; reviewer/rollback reddi sunucuya ulaşmış olarak görünmez. Üst onay katmanı olası açıklamadır, kesin kök neden değildir. Bu turda politika/hesap ayarı gevşetilmedi; ayrı inceleyici ve açık dosya listeli, hash kontrollü geri alma kullanıldı.

## Korunan başarısız denemeler

- İlk geri alma temizlik kontrolü, Git taban byte'ları LF iken Windows çalışma ağacı CRLF beklediğinden başarısız oldu. Erken PASS günlüğü sonraki FAIL kaydıyla açıkça düzeltildi; doğrulanan depo biçimi uygulanınca Git blob ve temiz durum eşleşti.
- İlk Qt yakalama yardımcı aracı font kaydını atladığı için yazılar kareydi. Bu görüntüler kabul edilmedi ve yerel kanıt alanında saklandı. Uygulamanın mevcut `main()` font başlatması kullanıldı; kaynak uygulama değişmedi.
- Önceki kaynak ve güvenlik alt inceleme oturumları model kotasıyla kesildi. Ara test kanıtı nihai kabul sayılmadı; etkin oturum modeliyle yeni bağımsız inceleme tamamlandı.

## Sınırlar ve devam

Sistem UTC saati referanstır. Resmî borsa takvimleri, tüm varlıkların birlikte eksik günleri, fiyat eskiliği, düzeltilmiş kapanış/temettü/bölünme kökeni ve FX dönüşümü bu düzeltmenin kapsamında doğrulanmadı. Veri sentetik veya kullanıcı CSV'sidir. 1366×768 görüntüsü yalnız bu akışın çizildiğini kanıtlar; tam ürün yerleşimi/fiziksel çoklu monitör kabulü değildir. Gerçek emir, lisans, ödeme ve gizli anahtar işlemi yapılmadı.

Bu kayıt commit öncesi hazırlanmıştır; uzak gönderim ancak uzak dal SHA'sı yerel commit ile eşleştiğinde tamamlanır. Kaynak hashleri ve ayrıntılı ölçümler [kanıt JSON](ANKA_DATE_RECOVERY_EVIDENCE_20261012.json), [bağımsız inceleme](ANKA_DATE_RECOVERY_REVIEW_20261012.json) ve [güvenlik incelemesi](ANKA_DATE_RECOVERY_SAFETY_20261012.json) içindedir.


### 12 Ekim 2026 — Uzak gönderim kanıtı

Yerel kod commit `5d24fb729ce70019bc719574768d826d2e2f8ccd`, `origin/fix/anka-price-date-recovery-20261012` ile tam SHA eşleşmesiyle doğrulandı (2026-10-12T12:26:52.705922+00:00). Gönderim başarılı; ana kullanıcı projesi 28/28 dosya özetiyle korundu. Bu ek kayıt yalnız belgelendirmedir. `FULL_AUTONOMY=BLOCKED`, `PRODUCTION_ACCEPTANCE=BLOCKED`.
