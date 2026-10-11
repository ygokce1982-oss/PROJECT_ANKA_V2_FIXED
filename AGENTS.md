# ANKA Finans — Ortak Ajan Sözleşmesi

Bu depo, ANKA Finans projesinin paylaşılan GitHub kayıt noktasıdır. Her yeni ChatGPT, Codex, Claude, Gemini ve diğer ajan oturumu **önce** bu dosyayı okumalıdır.

## Zorunlu başlangıç sırası
1. `AGENTS.md` ve `docs/ANKA_HANDOFF.md` dosyalarını oku.
2. `docs/ANKA_OPERATION_LOG.md` ve `docs/ANKA_OPERATIONS.jsonl` kayıtlarını kontrol et.
3. `docs/AI_CONTEXT.md`, `PROJECT_STATUS.md`, `NEXT_TASK.md`, `CHANGELOG.md` ve git geçmişini oku. Eski belgelerin tarihini dikkate al; bunları güncel kanıt kabul etme.
4. `git status --short`, mevcut dal, uzak depo ve son test kanıtlarını **salt-okunur** denetle.
5. Var olan işi/başarılı testi tekrarlama. Kaydı eksik işi ancak kanıtı doğrulayarak kapat.
6. İşe başlamadan önce kayıt aç; her önemli eylem, test, hata, onarım, geri alma ve sonucu izlenebilir biçimde kaydet.

## Değişiklik ve kalite kapıları
- Her görev için ayrı dal/izole çalışma ağacı; mevcut yerel değişikliklere ve API anahtarlarına dokunma.
- Ajan zinciri: planlayıcı → geliştirici → deterministik test → bağımsız denetçi → kabul. Bir kapı başarısızsa sonraki kapıya geçme.
- `PASS` yalnızca açık kabul ölçütü, çalışan test ve bağımsız kanıtla verilir. Model yanıtı üretmek ≠ görev tamamlamak.
- Başarısız değişikliği sınırlı onar; olmazsa geri al, `BLOCKED` kaydet. Otomatik canlı emir, alım-satım veya bakiye işlemi yapma.
- Haricî veri sağlayıcı haklarını/aboneliklerini doğrula; Fintables ChatGPT bağlantısını yerel programa entegre edilmiş gibi gösterme.
- Üretim/gerçek piyasa özelliğini test ortamından bağımsız doğrulamadan `PASS` sayma.

## GitHub ve günlük disiplini
- Kanonik depo: `ygokce1982-oss/PROJECT_ANKA_V2_FIXED`. `1982-gokce/yasinin-deposu` bu projenin kanonik deposu değildir.
- Depo herkese açıktır. Parola, token, `.env`, anahtar, özel e-posta içeriği, müşteri/veri lisansı içeriği veya ham hassas günlük **asla** yayımlama.
- `python scripts/record_operation.py --actor <rol> --action <kısa-işlem> --status <PASS|FAIL|BLOCKED|IN_PROGRESS> --evidence <kanıt> --next <adım>` ile makine günlüğüne kayıt aç. Gizli değer içeren argüman kullanma.
- Her değişiklikte insan-okunur `docs/ANKA_OPERATION_LOG.md` özeti ile JSONL günlüğünü git commit ve uygun GitHub dalına push et. Push başarısızsa yerel kayıt korunur; uzak sisteme kaydedildiği iddia edilmez.
- Bu dosyanın her oturumda yüklenmesi GitHub bağlantısı olan ajanlar için görev kuralıdır; bağlantı veya çalışma zamanı olmadan otomatik yürütme garantisi değildir.

## İlk açık işler
Ayrıntılar: [ANKA_HANDOFF](docs/ANKA_HANDOFF.md). Dört rol model çağrıları yapılmış; **tam otonomi BLOCKED**. En son bağımsız kabul raporu yerel Windows bilgisayarda, `Documents/ANKA_Overnight/latest_independent_acceptance.json` dosyasındadır.
