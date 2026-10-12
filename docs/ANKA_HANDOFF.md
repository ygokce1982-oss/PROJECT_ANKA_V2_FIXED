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
