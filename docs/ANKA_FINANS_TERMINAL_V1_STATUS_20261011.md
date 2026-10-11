# ANKA Finans — Profesyonel Terminal Önizleme V1

**Tarih:** 11 Ekim 2026
**Durum:** `OFFLINE_PREVIEW_CANDIDATE` — üretim veya tam otonomi kabulü DEĞİL.

## Çalıştırma

Windows'ta masaüstündeki **ANKA Finans - Cevrimdisi Onizleme** kısayoluna çift tıklayın. Alternatif: bu depodaki `ANKA_Finans_Baslat.cmd` dosyasını çalıştırın. Başlatıcı Python 3.14, PySide6 ve requests yüklü Windows ortamını kullanır.

Uygulama `ANKA_OFFLINE=1` ve `ANKA_DISABLE_LIVE=1` ile açılır. Gerçek piyasa emirleri gönderilmez; doğrulanmamış canlı fiyat gösterilmez.

## Uygulamada gerçekten bulunan ekranlar

1. **Piyasa Komuta Merkezi:** beş pazar göstergesi için boş/koşullu değer kartları, açık veri modu uyarısı, gerçek sayfalara giden kısayollar.
2. **Grafik ve Analiz:** örnek veya CSV verisi üzerinden grafik ve teknik değerlendirme.
3. **ANKA Yapay Zekâ:** mevcut ajan paneli; burada tam otonom üretim doğrulanmış değildir.
4. **Haber ve Araştırma:** yerel araştırma notları.
5. **Sanal Portföy:** gerçek emir vermeyen kâğıt işlemler.
6. **Ayarlar:** uygulama ve yerel veri seçenekleri.

## Doğrulama

- Çevrimdışı Python unittest paketi, GitHub tabanlı izole sürüm dalında **252/252 PASS**, exit 0 (ilk kopyalama ve test).
- Yeni kontrol paneli gezintisi, çevrimdışı fiyat dürüstlüğü, Qt kabuğu, uygulama kimliği, veri kalitesi ve risk testleri kapsandı.
- Qt ekranı gerçek `QWidget.grab()` ile oluşturulup `docs/previews/ANKA_Finans_Terminal_20261011.png` olarak kaydedildi.
- Son menü glifleri platform uyumluluğu için düz metne değiştirildi; hedeflenmiş yeniden doğrulama gerekir.
- Başlangıç klasörü `Documents/ANKA_Overnight/ANKA_FINANS_RELEASE_CANDIDATE_20261011`; kullanıcının `Documents/ANKA_Finans/Professional_20261009` içindeki 28 mevcut dosya değişikliği değiştirilmedi.

## Bilerek açık bırakılan kapılar

- Canlı BIST, lisanslı Matriks veri akışı, sağlayıcı hakları: bağlanmış/güncel olarak sunulmaz.
- Planlayıcı→geliştirici→deterministik test→bağımsız denetçi→geri alma tam otonom uçtan uca kapısı PASS değildir; Codex geliştirici görevinde önceki zaman aşımı kaydı bulunmaktadır.
- Figma tam düzenlenebilir tasarımında Starter/View kota sorunu bulunmaktadır.
- Bu adaydan ana GitHub `main` dalına otomatik birleştirme yapılmamalı; bağımsız inceleme ve gerçek kullanıcı kabulü gerekir.

## Kabul politikası

`PASS` yalnızca dosya, test ve gözlenmiş çalışma kanıtına uygulanır. Gerçek emir, bakiye değiştirme, ödeme, API anahtarı güncelleme ve gizli verileri açık GitHub deposuna gönderme yasaktır.

## Ajan bağlantısı ve arayüz güncellemesi (11 Ekim 2026)

- `core/agent_hub/adapters/codex_adapter.py` ve `antigravity_adapter.py` izole onarım dalından kontrollü aktarıldı.
- Antigravity Gemini planlayıcı ve Claude inceleyici ANKA'nın Yapay Zekâ sayfasında **açık kullanıcı seçimiyle** kullanılabilir. Varsayılan seçenek yerel Ollama'dır. Bu değişiklik bağımsız kod geliştirme otonomisi sağlamaz.
- `core/ai/remote_read_only_team.py` üzerinden yalnızca analiz/inceleme yetkisi kullanılır. Gizli bilgiler ve gerçek finansal emirler paylaşılmamalıdır.
- Yeni `tests/test_remote_read_only_team.py` ve `tests/test_ai_provider_selection.py` testleri eklendi.
- İlgili tüm çevrimdışı/regresyon birim testlerinin son çalışması **276/276 PASS**, exit 0.
- İki Qt görüntüsü: `docs/previews/ANKA_Finans_Terminal_20261011.png` ve `docs/previews/ANKA_Finans_Yapay_Zeka_20261011.png`. Bu görseller canlı fiyat veya gerçek hesap içermez.
- `FULL_AUTONOMY=BLOCKED`: gerçek kod yazan geliştirici + bağımsız denetim + otomatik geri alma uçtan uca doğrulanmadı; GitHub `main` birleştirilmedi.
