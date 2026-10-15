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
