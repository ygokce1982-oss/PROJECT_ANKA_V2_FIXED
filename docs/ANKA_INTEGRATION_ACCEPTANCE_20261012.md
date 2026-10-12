## 2026-10-12 — Gelişmiş terminalin normal uygulamaya bağlanması

- Dal: `feature/anka-integrated-terminal-20261012`, taban `7bffbebf0ef607c4a334c7e5d249aeece88327d1`.
- Normal uygulamada **Araçlar → Gelişmiş grafikler (Demo / CSV)** menüsü mevcut mum/EMA/Wilder RSI ve çoklu varlık/Sharpe terminalini aynı QApplication içinde açar. Pencere yeniden kullanılır; kapanışta alt pencereler temizlenir. Altı mevcut sayfa ve veri-kaynağı etiketleri korunur.
- 8 yeni test; **352/352 tam regresyon**, geri alma sonrası **27/27 hedefli Qt offscreen** PASS. Bağımsız reviewer `PASS_WITH_LIMITS`, ek parent-destruction probe PASS. Geri alma tabanı **19/19**, üç kaynak dosyası aynı SHA256 ile geri yüklendi. Ana kullanıcı dosyaları **28/28 değişmedi**.
- İlk kırmızı test ve yanlış etiket bekleyen ilk yeşil deneme kaydı korundu; nihai kaynak hashleri tam regresyon, reviewer ve son Qt koşusunda aynı.
- Üç 1366×768 gerçek Qt görüntüsü incelendi. Mevcut başlık kırpılması/ikon eksikleri; fiziksel ekran, canlı sağlayıcı, paket/kurulum ve tam ürün kabulü açık kaldı.
- **FULL_AUTONOMY=BLOCKED; PRODUCTION_ACCEPTANCE=BLOCKED.** Bu kayıt anında uzak gönderim beklemededir; sonraki SHA makbuzu ayrı kayıttır.
- [Kabul kanıtı](ANKA_INTEGRATION_EVIDENCE_20261012.json), [bağımsız inceleme](ANKA_INTEGRATION_REVIEW_20261012.json), [19 Ekim çalışma hedefi](ANKA_V1_DELIVERY_PLAN_20261012.md).
