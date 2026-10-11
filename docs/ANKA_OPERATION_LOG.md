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

**Kural:** Her gerçek geliştirme, test, denetim, hata veya geri alma sonrası yukarıdaki tabloya özet ekle; ayrıntıyı `scripts/record_operation.py` ile JSONL dosyasına kaydet. Başarısız doğrulamayı gizleme veya geçmiş kaydı silme.
