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

### 2026-10-11 — Windows GUI gerçek başlatma kanıtı

- Çift tıklanabilir `ANKA_Finans_Baslat.cmd` ile Windows masaüstünden uygulama başlatıldı; ayrı `python.exe` süreci çalışır görüldü.
- Gerçek Windows pencere başlığı `ANKA Finans | Profesyonel Piyasa Terminali` olarak `MainWindowTitle` üzerinden doğrulandı. Bu yalnız **GUI_START=PASS** kanıtıdır; canlı veri, tam otonomi veya nihai üretim kabulü anlamına gelmez.

## 2026-10-11 — Figma referansına göre profesyonel terminal yeniden yapıldı

**Yeni kod dalı:** `feature/anka-professional-terminal-20261011` / commit `4c33c96e89d533c0aebc2b58b02d2ed96e26bbf0` (Windows GitHub push + uzak SHA eşleşmesi PASS).
**Referans:** Kullanıcının 9 Ekim 2026 tarihli ANKA Finans ekran görüntüsündeki gerçek terminal düzeni; eski büyük piyasa kartlı taslak kullanıcı beklentisini karşılamıyordu, **kullanım için yeni dal tercih edilmeli**.
**Somut arayüz:** 72 px sol gezinme, üst piyasa bandı, seçili hisse fiyat/bilgi özeti, filtrelenebilir izleme listesi, hacim/momentum/gerileyenler taraması, sektör göreli hacim paneli, teknik görünüm, kaydırılabilir haber akışı ve ayarlanabilir QSplitter panelleri. Sembol seçimi ve filtreler gerçekten çalışır; rakamlar ÖRNEK/DEMO olarak etiketli, gerçek emir kapalı.
**Doğrulama:** Windows izole dalda tüm `281/281` çevrimdışı `unittest` PASS, exit 0; 1366 × 768 ve 1480 × 890 Qt QWidget ekran görüntüleri başarıyla alınıp incelendi. Uygulama bilgisayarda açık; `python.exe` süreç kimliği ve pencere başlığı doğrulandı. Windows masaüstünde `ANKA Finans - PROFESYONEL ONIZLEME.lnk` kısayolu oluşturuldu.
**Figma:** Yeni dosya oluşturuldu: https://www.figma.com/design/ijVC43Q32AeaHDjrwSjCgP. Figma `whoami` hesabı Starter plan, View seat. `use_figma` düzenleme çağrısı **Starter MCP kullanım kotası** nedeniyle reddedildi. **Figma dosyası boş**, düzenlenebilir katmanlar yapılmış gibi gösterme. Hedef tasarım ile Qt kodunu bağlamak için özellik dalında `docs/FIGMA_SYNC_DESIGN_SPEC_20261011.json` ve `docs/ANKA_REFERENCE_DESIGN_ACCEPTANCE_20261011.md` var. Kotu yenilendiğinde/izinli editör erişimi sağlandığında bunlardan düzenlenebilir Figma sistemini kurup tasarım bağlamıyla Qt'yi çapraz doğrula.
**Önemli sınırlar:** `FULL_AUTONOMY=BLOCKED` ve nihai ürün kabulü henüz sağlanmadı; aday kod GitHub main'e birleştirilmedi. Kullanıcıya ait Windows ana projesindeki 28 yerel değişiklik korundu. Matriks ve canlı alım-satım yetkisi ayrı engel olarak durur.

[Profesyonel sürüm](https://github.com/ygokce1982-oss/PROJECT_ANKA_V2_FIXED/tree/feature/anka-professional-terminal-20261011) · [1366×768 ekran](https://github.com/ygokce1982-oss/PROJECT_ANKA_V2_FIXED/blob/feature/anka-professional-terminal-20261011/docs/previews/ANKA_Finans_Terminal_1366x768.png).

## 2026-10-11 — ANKA Finans görsel arşivi ve gerçek çalışma alanı kalıcılığı

- **Doğrulanmış güncel deney dalı:** `experiment/anka-toolchain-workstation-20261011`, commit `88de29d8aa90dc69583cb57b48be1a8adc30309a`. Windows git push sonrası uzak SHA eşleşmesi PASS; kaynak GitHub main'e kör birleştirilmedi.
- **Görseller:** Bilgisayarda erişilebilir ANKA görsel dizinlerinde 10 PNG dosyası bulundu, SHA-256 ile 7 farklı PNG olarak korunup arşivlendi. Arşiv: [GitHub ZIP](https://github.com/ygokce1982-oss/PROJECT_ANKA_V2_FIXED/blob/experiment/anka-toolchain-workstation-20261011/docs/ANKA_Finans_Gorsel_Arsivi_20261011.zip). [Kaynaklar ve hash belgesi](https://github.com/ygokce1982-oss/PROJECT_ANKA_V2_FIXED/blob/experiment/anka-toolchain-workstation-20261011/docs/visual_archive/MANIFEST.json). Windows'da ayrıca `Documents/ANKA_Finans_Gorsel_Arsivi_20261011.zip` mevcut. Chat içinde üretilmiş fakat dosya bytes'ı artık erişilemeyen önceki görseller bu arşivin kapsamında değildir.
- **Özellik:** `scripts/anka_professional_toolchain_demo.py` içinde gerçek QSettings INI çalışma alanı kaydı; beş QDockWidget için yerleşim ve ayrılabilir pencere durumu, pencere geometrisi, hisse sembolü ve grafik yakınlaştırması kalıcıdır. Yeniden açınca geri yüklenir; `Düzeni Geri Al` kayıtlı düzeni sıfırlar. Yerel ayarlar `AppData/Roaming/ANKA Finans/workstation-layout.ini` içinde tutulur. `ANKA_LAYOUT_FILE` testte izole edilir.
- **Kanıt:** Tüm çevrimdışı regresyonlar `292/292 PASS` (11.10.2026); beş yeni çalışma alanı kalıcılık testi dahil. Ana kullanıcı kaynağı `Documents/ANKA_Finans/Professional_20261009` üzerindeki önceki 28 değişiklik korunmuştur.
- **Durum:** Çalışan Qt Widgets Designer + QDockWidget + QPainter demosu, sentetik mum/derinlik/risk/haber içerir; gerçek borsa verisi ve emir akışı yok. `FULL_AUTONOMY=BLOCKED`; `PRODUCTION_ACCEPTANCE=BLOCKED`. Ajanlar gerçek test ve bağımsız denetim geçmeden PASS gösteremez.
- **Devam:** Yeni özellikleri bu doğrulanmış dalı kaynak alarak ayrı, korumalı geliştirme dallarında gerçekleştir; otomatik test, bağımsız denetim ve rollback; kullanıcıya ait ana dosyaları değiştirme. [Yeni özellik ve kapsam belgesi](https://github.com/ygokce1982-oss/PROJECT_ANKA_V2_FIXED/blob/experiment/anka-toolchain-workstation-20261011/docs/ANKA_TOOLCHAIN_REAL_EXAMPLE_20261011.md).

## 2026-10-11 — ANKA Finans gerçek EMA ve Wilder RSI grafikleri

- **Yeni geliştirilen izole dal:** `feature/anka-verified-chart-indicators-20261011` / commit `cd7ef21b42cb0fac0702cf87c2c997b9608bbe07`. Windows Git `push` başarı ve uzak SHA eşleşmesi doğrulandı. [Kaynak](https://github.com/ygokce1982-oss/PROJECT_ANKA_V2_FIXED/tree/feature/anka-verified-chart-indicators-20261011).
- **Somut değişiklik:** `core/chart_indicators.py` OHLCV tutarlılık ve NaN/Inf doğrulaması, EMA'nın SMA ile başlatılarak tüm mum geçmişinden hesaplanması, Wilder RSI'nın gerçek kapanış dizilerinden hesaplanması. Qt grafik kodundaki önceki sinüs amaçlı RSI kaldırıldı; yakınlaştırma EMA başlangıcını yeniden belirlemiyor. Rakamların kaynağı yine **DEMO/simülasyon**, lisanslı canlı veri değil.
- **Kanıt:** tam çevrimdışı regresyon `300/300 PASS`, çıkış kodu 0; yeni sekiz sayısal test ve mevcut bütün GUI testleri geçti. Qt Designer + 5 dock grafik ekranı tekrar görüntülendi. [Test ve kabul notu](https://github.com/ygokce1982-oss/PROJECT_ANKA_V2_FIXED/blob/feature/anka-verified-chart-indicators-20261011/docs/ANKA_CHART_INDICATORS_ACCEPTANCE_20261011.md).
- **Koruma:** ana Windows `Documents/ANKA_Finans/Professional_20261009` klasöründeki 28 önceki kullanıcı değişikliğine dokunulmadı; kod `main`e birleştirilmedi.
- **Sıradaki kapı:** bağımsız kaynak incelemesi ve gerçek piyasa verilerinin kaynak/tarih/sağlayıcı doğrulaması. `FULL_AUTONOMY=BLOCKED`, `PRODUCTION_ACCEPTANCE=BLOCKED`, Matriks canlı veri yetkilendirmesi ayrı. Gerçek emir iletimi kapalıdır.
