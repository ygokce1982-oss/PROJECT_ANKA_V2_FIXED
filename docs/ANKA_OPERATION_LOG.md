# ANKA Finans — Ortak İşlem Günlüğü

Bu belge insan tarafından okunabilen kalıcı özet içindir. Makine kayıtları `ANKA_OPERATIONS.jsonl` dosyasında tutulur. **GitHub push olmadan uzak kayıt tamamlandı sayılmaz.** Depo herkese açıktır; gizli bilgiler kaydedilmez.

| Tarih (TR) | Aktör | İşlem ve kanıt | Sonuç | Sonraki iş |
| --- | --- | --- | --- | --- |
| 2026-10-09 | Yerel geliştirme | `Professional_20261009` özellik dalında Matrikse hazırlık ve yerel ajan teslim planı commitleri (`73ebf22`, `b1e9e08`). Ana ağaçta sonradan 28 değişiklik görüldü. | KISMİ | Kodu ana dala otomatik birleştirme; farkları doğrula. |
| 2026-10-11 09:19 | İzole aday / Ollama | 4 rol gerçek model yanıtı, 241 birim test PASS ve Ruff PASS raporlandı; üç rolde konu kayması tespit edildi. | BLOCKED | Finans alanı uygunluğu, gerçek kod üretimi ve review kapısı. |
| 2026-10-11 10:19 | Bağımsız salt-okunur denetim | `latest_independent_acceptance.json` sonuç: `BLOCKED_NOT_READY_FOR_AUTONOMY`. | BLOCKED | Tam zincir, doğru içerik, otomatik rollback, piyasa canlı veri. |
| 2026-10-11 | ChatGPT / araç denetimi | Desktop Commander, GitHub, Ollama, Docker, Figma/TinyFish bağlantıları ve Fintables salt-okunur THYAO fiyat sorgusu doğrulandı. Fintables yerel Windows uygulamasına bağlanmadı. | KISMİ | Entegrasyon testlerini ayrı yap. |
| 2026-10-11 | GitHub kayıt kurtarma | Asıl depo `ygokce1982-oss/PROJECT_ANKA_V2_FIXED` bulundu. Alternatif `1982-gokce/yasinin-deposu` boş. Windows `git push --dry-run` başarılı, hiçbir uzak veri yazılmadı. | PASS | Ortak ajan sözleşmesi ve bu kayıtları git üzerinden yayımla. |

| 2026-10-11 | GitHub yayın ve erişim | Ortak ajan sözleşmesi, devir kaydı, günlük ve kayıt aracı 80f11e9 commit'iyle main dalına gönderildi; uzaktan commit eşleşti, GitHub bağlantısıyla dosyalar okundu. GitHub eklentisinin özel izin ayarı kullanıcı isteği üzerine Allow all actions olarak değiştirildi. | PASS | Gelecek her görevde günlük tutma ve kanıtlı test kapılarını uygula. |

| 2026-10-11 | Codex erişim onarımı | Kod ve 32 PASS test `repair/codex-adapter-20261011` dalına `40f6b72` ile kaydedildi; gerçek CLI salt-okunur görev çalıştı. Claude girişsiz, Gemini istemcisi uyumsuz, Figma kullanım sınırında, Ollama reviewer zaman aşımında. | KISMİ | Bağımsız inceleme, gerçek kod değişikliği zinciri, otomatik geri alma ve güvenli entegrasyon. |

| 2026-10-11 | Ajan erişim V2 | Codex Windows süreç ağacı temizliği ve Antigravity Gemini/Claude geçidi aday dalda f1fbd07 olarak yayımlandı; 40 birim test, Codex canlı görev ve iki model bağlantısı PASS. Doğrudan Claude Code girişi ve Figma kotası BLOCKED. | KISMİ | Bağımsız denetim, gerçek süreç stres testi ve otomatik kod değişikliği/rollback kapısı. |

**Kural:** Her gerçek geliştirme, test, denetim, hata veya geri alma sonrası yukarıdaki tabloya özet ekle; ayrıntıyı `scripts/record_operation.py` ile JSONL dosyasına kaydet. Başarısız doğrulamayı gizleme veya geçmiş kaydı silme.

## 2026-10-12 — Sharpe veri güvenliği için izole düzeltme

- Ayrı dal: `fix/anka-sharpe-guards-20261012`. Bilinen ortak işlem seansı boşluğu tek bir günlük getiriyi oluşturmaz; ilgili hareketli Sharpe değeri `None` olarak kalır, kümülatif fiyat getirisi korunur. Geleceğe tarihli kaynak damgası reddedilir.
- Hedefli testler **26/26**, tüm çevrimdışı regresyon ve Qt smoke testleri **326/326 PASS**, `git diff --check` ve AST kontrolü **PASS**.
- Bağımsız Antigravity Gemini denetimi: **PASS_WITH_LIMITS**, kaynak takvimi ve düzeltilmiş kapanış fiyatlarının doğrulanmadığı açık. Claude inceleme istemine yalnız plan yanıtı verdi, bağımsız karar değil. Ollama iki model ile **0xc0000005** yerel llama-server çöküşü yaşadı; tekrar aynı yöntemi deneme.
- **Üretim kullanımı, Matriks canlı verisi, otomatik emir ve tam otonomi BLOCKED.** Korunan ana yerel 28 dosyaya dokunulmadı. Bu kayıt `main` dalının kabulü değildir.


## 2026-10-11 — Çoklu varlık performansı ve Sharpe ekranı

- **Dal:** `feature/anka-multi-asset-performance-20261011` (bağımsız Windows worktree).
- **İşlem:** Kümülatif getiri grafiği + ortak günlük kapanışlardan yıllıklandırılmış hareketli 90 günlük Sharpe, 30/60/90/120 pencere seçenekleri; 2 grafik aynı gerçek Qt sekmesinde.
- **Kaynak kontrolü:** Sıralı ISO tarihler, sonlu/pozitif kapanışlar, zorunlu veri-kaynağı ve dosya zamanı; farklı dövizler engellenir; eksik tarihler sessizce doldurulmaz. Sentetik örnek ve kullanıcı yerel CSV kaynağı ayrı etiketlenir.
- **Test kanıtı:** Tam çevrimdışı regresyon `python -B -m unittest discover -s tests -p test_*.py -q`, `Ran 322 tests`, `OK`, exit 0. Özel hesap/CSV/Qt testleri PASS. Gerçek `QWidget.grab()` ekran görüntüsü ayrıca kaydedildi.
- **Bağımsız inceleme:** **BLOCKED/PENDING**, henüz PASS kanıtı yok; ana dala birleştirme ve üretim kullanımı onaylanmış değildir. Yetkili gerçek Matriks/BIST veri akışı ve gerçek emir kapısı da BLOCKED.
- **Geri alma:** Ayrı feature commit'i geri alınabilir, feature worktree kaldırılabilir; korunan 28 kullanıcı düzenlemesi bulunan ana yerel çalışma projesine dokunulmadı.
- **Sabah programı:** ANKA Finans Tamamlama saatlik koşullu görev etkin, 2026-10-12 08:00 Türkiye saati için bağımsız sabah durum raporu oluşturuldu; aynı dosyalara paralel yazma yapılmaması şart.


## 2026-10-12 — Gelecek fiyat tarihini reddetme ve güvenli kurtarma

- Yeni izole dal: `fix/anka-price-date-recovery-20261012`, taban `0d8318d`. Önceki adayın iki dosyası yedeklendi ve eski dal temiz tabana döndürüldü. Ana kullanıcı projesi 28/28 SHA256 ile korundu.
- 18 yeni sabit-saat testi; hedefli37/37, tam344/344, Qt19/19 PASS. Ayrı kaynak reviewer `PASS_WITH_LIMITS`; geri alma provasında taban19/19 PASS, aday dosya hashleri geri yüklendi.
- Gelecek UTC fiyat günleri ve temel/hafta ISO biçimleri reddedilir. CSV çevre boşluklarını kırpma ve dosya mtime anlamı korunur. Gerçek emir kapalıdır.
- İlk CRLF temizlik hatası, font eksikliği ve kesilen reviewer oturumları günlükte korunur. Özgün eski izin reddinin kesin nedeni kayıt eksikliği nedeniyle doğrulanamadı; politika değiştirilmedi.
- **FULL_AUTONOMY=BLOCKED; PRODUCTION_ACCEPTANCE=BLOCKED.** Uzak gönderim bu belgenin commit anında beklemededir; dal HEAD doğrulaması gerekir. [Ayrıntılı kabul kaydı](ANKA_DATE_RECOVERY_ACCEPTANCE_20261012.md).


### 12 Ekim 2026 — Uzak gönderim kanıtı

Yerel kod commit `5d24fb729ce70019bc719574768d826d2e2f8ccd`, `origin/fix/anka-price-date-recovery-20261012` ile tam SHA eşleşmesiyle doğrulandı (2026-10-12T12:26:52.705922+00:00). Gönderim başarılı; ana kullanıcı projesi 28/28 dosya özetiyle korundu. Bu ek kayıt yalnız belgelendirmedir. `FULL_AUTONOMY=BLOCKED`, `PRODUCTION_ACCEPTANCE=BLOCKED`.


## 2026-10-12 — Gelişmiş terminalin normal uygulamaya bağlanması

- Dal: `feature/anka-integrated-terminal-20261012`, taban `7bffbebf0ef607c4a334c7e5d249aeece88327d1`.
- Normal uygulamada **Araçlar → Gelişmiş grafikler (Demo / CSV)** menüsü mevcut mum/EMA/Wilder RSI ve çoklu varlık/Sharpe terminalini aynı QApplication içinde açar. Pencere yeniden kullanılır; kapanışta alt pencereler temizlenir. Altı mevcut sayfa ve veri-kaynağı etiketleri korunur.
- 8 yeni test; **352/352 tam regresyon**, geri alma sonrası **27/27 hedefli Qt offscreen** PASS. Bağımsız reviewer `PASS_WITH_LIMITS`, ek parent-destruction probe PASS. Geri alma tabanı **19/19**, üç kaynak dosyası aynı SHA256 ile geri yüklendi. Ana kullanıcı dosyaları **28/28 değişmedi**.
- İlk kırmızı test ve yanlış etiket bekleyen ilk yeşil deneme kaydı korundu; nihai kaynak hashleri tam regresyon, reviewer ve son Qt koşusunda aynı.
- Üç 1366×768 gerçek Qt görüntüsü incelendi. Mevcut başlık kırpılması/ikon eksikleri; fiziksel ekran, canlı sağlayıcı, paket/kurulum ve tam ürün kabulü açık kaldı.
- **FULL_AUTONOMY=BLOCKED; PRODUCTION_ACCEPTANCE=BLOCKED.** Bu kayıt anında uzak gönderim beklemededir; sonraki SHA makbuzu ayrı kayıttır.
- [Kabul kanıtı](ANKA_INTEGRATION_EVIDENCE_20261012.json), [bağımsız inceleme](ANKA_INTEGRATION_REVIEW_20261012.json), [19 Ekim çalışma hedefi](ANKA_V1_DELIVERY_PLAN_20261012.md).


### 12 Ekim — Terminal entegrasyonu uzak gönderim kanıtı

Kod commit `98866f12d52fa100610b6804b4de46f1cbaba9ed`, uzak `feature/anka-integrated-terminal-20261012` ile tam SHA eşleşmesiyle doğrulandı (2026-10-12T16:51:53.362496+00:00). Ana kullanıcı projesinin 28 dosyası değişmedi. Bu ek yalnız gönderim makbuzudur. `FULL_AUTONOMY=BLOCKED`, `PRODUCTION_ACCEPTANCE=BLOCKED`.


## 2026-10-13 — Yerel alarm geçmişi ve tüm sembollerin kontrolü

- Dal `feature/anka-alert-history-20261013`, taban `d78485bdd064028ed6add5fcdbb92789df474de0`. Portföyde salt-okunur alarm geçmişi; manuel kontrol bütün kayıtlı yerel sembolleri işler. SQLite alarm/eşik kuralları korunur; tekrar/eski mum yeni olay üretmez.
- 12 yeni test; tam regresyon **364/364**, geri alma sonrası hedefli/Qt **39/39**; bağımsız inceleme **PASS_WITH_LIMITS**. Taban **19/19**, üç dosyanın birebir SHA256 ile geri yerleştirilmesi ve ana projenin **28/28** korunması doğrulandı.
- 1366×768 ve 1920×1080 gerçek Qt yakalamaları; iki örnek sembol alarmı ve tekrar kontrolde sıfır yeni olay. Çevrimdışı veriler kullanıldı.
- Tarihçenin gösterdiği kayıt sayısı sınırlıdır; sıralama tüm olay imlecini tarar. Otomatik arka plan/cihaz/telefon bildirimi ve canlı veri bu dilimin kabulü değildir. **FULL_AUTONOMY=BLOCKED; PRODUCTION_ACCEPTANCE=BLOCKED.**
- Uzak gönderim bu kayıt anında beklemede; sonrasında ayrı SHA makbuzu tutulur. [Kanıt](ANKA_ALERT_EVIDENCE_20261013.json), [inceleme](ANKA_ALERT_REVIEW_20261013.json).


### Uzak gönderim makbuzu

Kod commit `0bf85bf9260f3528dd76a37cb990abe31f3951e9`, `feature/anka-alert-history-20261013` uzak dalıyla tam SHA eşleşmesiyle doğrulandı (2026-10-13T13:06:30.655301+00:00). Genel otonomi ve üretim kabulü BLOCKED.
