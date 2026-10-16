## 16 Ekim 2026 — Sağlayıcı yedekleme çekirdeği kabulü

Kayıtlı sağlayıcılar öncelik sırasıyla denenir; boş veri, sağlayıcı reddi ve tüketici reddi/istisnası sonraki kaynağa geçirir. Başarılı kaynak ve denemeler döner; hepsi başarısızsa açık hata oluşur. Hata metinleri ham sağlayıcı istisnasını içermez; sonuç repr çıktısında veri gizlidir. Registry işlemleri ve fetch aynı kilidi paylaşır.

- Dal `feature/anka-provider-failover-core-20261016`, taban `2e64385232e7e4370723ff370c5ae8e347a97042`. 17 yeni test; **405/405 tam** (16 Ekim 05:19 UTC tamamlandı), geri yükleme sonrası **34/34 hedefli/Qt**, tabanda **17/17**. Tam koşu aynı kaynak hashleriyle tekrar edilmeden kullanıldı; ayrı koşular toplanmaz.
- Bağımsız inceleme **PASS_WITH_LIMITS**; ilk çağrının hizmet sınırı kaydı korunur. İki dosyalık arşiv inceleme tamamlanana kadar tabanda tutuldu; kabul edilen dosyalar aynı SHA256 ile geri yüklendi.
- Ana projeye yazılmadı; bu yayın aralığının 54 değişik dosyası, HEAD/dal/durum/hashleri korunuyor. Tarihsel28 manifesti farklıdır ve saklanır.
- Güvenlik taramasında yalnız iki mock-session testindeki açık sentetik değer için dar istisna vardır. Gerçek kimlik bilgisi veya özel e-posta/lisans içeriği eklenmedi.
- Bu çekirdek canlı fiyat, tazelik/köken doğrulaması veya UI entegrasyonu sağlamaz. Sağlayıcı kendi I/O süresini sınırlamalı; iptal/kapanış işi ayrı. Önceki Qt pending-worker bulgusu açık kalır.
- **FULL_AUTONOMY=BLOCKED; PRODUCTION_ACCEPTANCE=BLOCKED.** Uzak gönderim bu kayıt anında bekliyor.

Kanıt: [test/geri alma](ANKA_PROVIDER_FAILOVER_EVIDENCE_20261016.json), [bağımsız inceleme](ANKA_PROVIDER_FAILOVER_REVIEW_20261016.json).
