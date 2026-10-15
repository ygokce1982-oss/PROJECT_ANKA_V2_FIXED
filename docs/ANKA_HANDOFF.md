# ANKA Finans — Paylaşılan Devir ve Gerçek Durum

**Tarih:** 2026-10-11 (Europe/Istanbul)
**Kaynak:** Windows Desktop Commander salt-okunur kontrolleri, yerel kabul raporları, GitHub deposu ve Fintables okuma testi.
**Ana depo:** https://github.com/ygokce1982-oss/PROJECT_ANKA_V2_FIXED
**Güncel sonuç:** `BLOCKED_NOT_READY_FOR_AUTONOMY`. Bu bir tam otomasyon onayı değildir.

## Mevcut kanıtlar
- Proje: Windows `Documents/ANKA_Finans/Professional_20261009`, yerel dal `feature/anka-professional-20261009`, yerel HEAD `73ebf22` (2026-10-09).
- 2026-10-11 denetiminde ana yerel çalışma ağacında **28 mevcut değişiklik** vardı. Önceki yedek manifestinde 28 dosya için SHA256 doğrulaması raporlandı. **Temizleme/reset/üzerine yazma yasak.**
- GitHub `main` baz commit `b492f80` (2026-10-11 erişiminde). Yerel özellik dalı ile GitHub `main` aynı revizyonda değildir. Yerel geliştirmelerin tümü GitHub'da yayımlanmış kabul edilemez.
- İzole QA raporu `Documents/ANKA_Overnight/latest_agent_operational_gate.json`: dört düşük-bellek Ollama rolü HTTP yanıtı üretti, 241 test ve Ruff geçişi raporlandı. Ancak üç rolün içeriği finansal piyasalar yerine kredi kartına kaydı.
- Bağımsız rapor `Documents/ANKA_Overnight/latest_independent_acceptance.json` (2026-10-11 10:19 +03): `BLOCKED_NOT_READY_FOR_AUTONOMY`. İstenen planlayıcı/geliştirici/deterministik test/bağımsız denetçi zinciri, gerçek otomatik kod değişikliği ve konu uygunluğu kanıtlanmadı.
- 2026-10-11 önceki QA evrelerinde 214, 225, 237 ve 241 birim testinin geçişi raporlandı. Bunlar **farklı test anları ve adaylar**; ana projenin üretim onayı değildir.
- Desktop Commander bağlantısı yeniden sağlandı. Docker Engine 29.8.2, Ollama 0.40.3; Ollama'da 6 kurulu model. Önceki 4-ajansal görev kuyruğunda 3 zaman aşımı, 1 `running` kaydı görüldü; son durum yeniden denetlenmeli.
- Windows ANKA prototipi çevrimdışı ve emir gönderimi kapalı modda açıldı; kullanıcı bu arayüzü profesyonel terminal olarak **reddetti**. Figma tabanlı profesyonel tasarım hedefleniyor, tamamlandığı doğrulanmadı.
- ChatGPT Figma/GitHub/TinyFish eklentileri bağlı. Figma planında `View` koltuğu görüldü; düzenleme yetkisi ayrıca doğrulanmalı.
- ChatGPT üzerinden Fintables fiyat sorgusu `THYAO` için veri döndürdü; 11 finansal veri becerisi yüklendi. **Bu, Windows ANKA uygulamasında Fintables entegrasyonu yapıldığı anlamına gelmez.**
- Matriks deneme erişimi/sözleşme ve gerçek canlı BIST veri kapısı tamamlanmadı; gerçek emir gönderimi yasak.

## Sıradaki kanıt kapıları
1. Yerel `git status` ve rapor SHA'larını oku, hiç bir gizli değer göstermeden kontrol et.
2. Bellek kapasitesine göre **tek model / sıralı görev** ve finansal piyasa görevi doğruluğu testini gerçekleştir; zaman aşımı ve alakasız içerik `FAIL` olmalı.
3. Planlayıcı → geliştirici → deterministik test → bağımsız denetçi zincirini, izole dal üzerinde gerçek kod değişikliği, rollback ve izleme kanıtıyla doğrula.
4. Figma tasarımını doğrula; profesyonel arayüzü ayrı aday sürümde gerçek bileşenlerle inşa et; eski PySide6 prototipini nihai ürün gibi açma.
5. İzole aday kabul kapıları PASS ise kontrollü entegrasyon yap. Matriks canlı veri ve emir katmanı ayrı onay gerektirir.

## Sohbetler arası kullanım
Her yeni ajan veya sohbet GitHub'dan `AGENTS.md` → bu dosya → `docs/ANKA_OPERATION_LOG.md` ve `docs/ANKA_OPERATIONS.jsonl` → git geçmişi sırasını izlemelidir. ChatGPT sohbet metninin tamamı GitHub'a otomatik kopyalanmaz; **yalnızca gizli/veri içermeyen, GitHub'a push edilmiş kanıtlı kayıtlar** ortak görünür.

## 2026-10-11 Ajan Erişim V2 Güncellemesi

- Aday: epair/codex-timeout-20261011, commit 1fbd07. Codex CLI Windows alt süreç kapatma kontrolü ve Antigravity (Gemini planlayıcı, Claude denetçi) bağlı.
- 40/40 ilgili birim test PASS, Codex gerçek görev PASS, Gemini ve Claude gerçek model bağlantısı PASS. Bağlantı PASS = otonom geliştirme PASS değildir.
- Doğrudan Claude Code OAuth loggedIn:false; Figma Starter/View MCP kullanım kotası dolu. Matriks ayrı engel olarak tutulur.
- Kod main dalına birleştirilmedi. Bağımsız kod denetimi ve gerçek kod değişikliği→test→review→rollback uçtan uca kapısı henüz BLOCKED.


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


## 2026-10-14 — Yerel analiz sonrası uygulama içi alarm bildirimi

- Dal `feature/anka-local-alert-notice-20261014`, taban `76eef2d2fc8b924008d94170166e00e659846599`. Başarılı örnek/CSV analizi mevcut kalıcı yukarı eşik kuralıyla değerlendirilir; yeni olayda ana pencerede kapatılabilir bildirim ve geçmişe erişim gösterilir. Sayfa değiştirilmez. Tekrar/eski mum ve yeniden açılış bildirim üretmez.
- 13 yeni test; tam regresyon **377/377**, geri alma sonrası hedefli/Qt **52/52**; taban **39/39**. Dört kaynak dosyası birebir SHA256 ile geri yüklendi. Bağımsız inceleme **PASS_WITH_LIMITS**.
- 1366×768 ve 1920×1080 gerçek Qt yakalamaları; iki yerel sembol, bildirim kapatma, geçmişe erişim ve tekrar engeli doğrulandı.
- Ana proje başlangıçta tarihsel28 manifestinden farklıydı: 8 ek durum yolu ve 2 farklı eski dosya içeriği. Bu çalışma ana projeye yazmadı; 14 Ekim geri alma anında mevcut36 özeti aynıydı. Daha sonraki ana proje farkları aşağıdaki yayın notunda ayrıca kaydedildi. Tarihsel manifest saklandı ve başarısız karşılaştırma gizlenmedi.
- Bildirim yalnız yerel analiz akışındadır; cihaz/telefon, lisanslı canlı veri ve kalıcı bildirim teslim kuyruğu bu dilime dahil değildir. Ani kapanıştan önce teslim edilmeyen uyarı yeniden oynatılmaz; alarm geçmişi kalıcıdır. Büyük geçmişte sorgu taraması, fiziksel cihaz ve temiz kurulum kabulü açıktır.
- **FULL_AUTONOMY=BLOCKED; PRODUCTION_ACCEPTANCE=BLOCKED.** Uzak gönderim henüz beklemede. [Kanıt](ANKA_NOTICE_EVIDENCE_20261014.json), [inceleme](ANKA_NOTICE_REVIEW_20261014.json).


### 15 Ekim — Yayın aralığı koruması

14 Ekimde başarılı36 karşılaştırmasının ardından ana proje değişti: 15 Ekimde47, yayın öncesinde49 durum yolu gözlendi. Tarihsel28 ve36 karşılaştırmaları şu anda eşit değildir; başarısız kontroller ve eski manifestler saklandı. Değişikliklerin yapanı kesin doğrulanmadı. Bu dalın dört kaynak dosyası test, inceleme ve geri alma özetleriyle aynıdır.

Bağımsız ürün incelemesi 14 Ekimde tamamlandı. Sonraki ana proje farkının ek inceleme oturumu kullanım sınırında kesildi; yeni bağımsız inceleme yapılmış sayılmadı. Yayın işlemi yalnız ayrı aday dalına yazacaktır. Ana projeye dosya yazımı yapılmaz; 2026-10-15T13:05:13.459236+00:00 anındaki 49 dosyanın HEAD/dal/durum/içerik özeti yayın öncesi ve sonrası karşılaştırılır. Bu sınırlı kontrol tarihsel farkları kapatmaz veya genel üretim kabulü sağlamaz.


### Uzak SHA makbuzu

Kod commit `c574218064fa5f98fb4696a09b5ed5462afb0895` uzak `feature/anka-local-alert-notice-20261014` dalıyla tam eşleşti (2026-10-15T13:08:47.646969+00:00). Genel kabul BLOCKED.
