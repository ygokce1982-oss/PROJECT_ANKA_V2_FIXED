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

## 2026-10-11 — ANKA Finans çalışır terminal adayı (en yeni doğrulanmış teslim)

- **Kod dalı:** `feature/anka-finans-terminal-20261011`, commit `61e32e0e3d1ccf1a719016f8796d860ca3a70ebd`. Windows Git üzerinden gönderim yapıldı, uzak SHA eşleşmesi doğrulandı. [GitHub'da aç](https://github.com/ygokce1982-oss/PROJECT_ANKA_V2_FIXED/tree/feature/anka-finans-terminal-20261011).
- **Test kanıtı:** Windows izole Git çalışma ağacında `276/276` çevrimdışı bütünleşik Python unittest PASS. Qt pencere, kontrol paneli yönlendirmeleri, piyasa durumunun dürüst gösterimi ve bulut modeli seçimi testleri kapsandı.
- **Somut uygulama:** Altı ekranlı koyu profesyonel PySide6 terminali; örnek/CSV grafik ve analiz, araştırma kayıtları, sanal portföy, kontrollü piyasa merkezi ve Yapay Zekâ. Gemini planlayıcı ve Claude inceleyici seçildiğinde Antigravity kullanılır; varsayılan yerel Ollama'dır.
- **Ekran kanıtları:** `docs/previews/ANKA_Finans_Terminal_20261011.png` ve `docs/previews/ANKA_Finans_Yapay_Zeka_20261011.png` aday dalda; Qt QWidget görüntüsünden oluşturuldu.
- **Windows kullanımı:** `Documents/ANKA_Overnight/ANKA_FINANS_RELEASE_CANDIDATE_20261011/ANKA_Finans_Baslat.cmd` veya masaüstündeki `ANKA Finans - Cevrimdisi Onizleme` kısayolu. Gerçek emir gönderimi kapalı, canlı BIST lisansı ve fiyat doğrulanmamış.
- **Koruma:** Kullanıcının `Documents/ANKA_Finans/Professional_20261009` çalışma ağacındaki 28 mevcut değişiklik korunmuştur; `main` koduna bu aday birleştirilmemiştir.
- **Açık blokajlar:** `FULL_AUTONOMY=BLOCKED` ve `PRODUCTION_ACCEPTANCE=BLOCKED`; gerçek otomatik geliştirme→deterministik test→bağımsız kaynak denetimi→rollback uçtan uca tamamlanmadı. Doğrudan Claude Code oturumu ve Figma Starter kullanım kotası ayrı engellerdir.
- **Sonraki görev:** Yeni aday dalındaki gerçekten çalışan terminal üzerinden bağımsız QA ve otomatik onarım güvenlik kapılarını kur; önce Git diff, test kanıtı ve son kayıtları oku. Başarısız ajan görevi/model yanıtını PASS gösterme.
