# ANKA Finans — Ajan Erişimi ve Yürütme Kapısı (11.10.2026)

**Kapsam:** İzole `repair/agent-gateway-20261011` dalı. Ana Windows çalışma ağacındaki 28 mevcut değişiklik korunur. Henüz üretim kabulü yok.

| Kapı | Sonuç | Kanıt |
| --- | --- | --- |
| Windows Desktop Commander bağlantısı | PASS | `DESKTOP-5C7PG1Q` çevrimiçi; salt-okunur envanter yapıldı |
| GitHub kanonik kayıtlar | PASS | `AGENTS.md`, `docs/ANKA_HANDOFF.md`, `docs/ANKA_OPERATIONS.jsonl`; main `7036096` |
| Codex CLI oturumu | PASS | `codex login status`: Logged in using ChatGPT |
| CodexAdapter (önceki) | FAIL | Sadece `Unavailable` dönüyordu; gerçek yürütme yoktu |
| CodexAdapter (izole onarım) | PASS: çağrı | `scripts/smoke_codex_live.py` → `LIVE_SUCCESS=True`, `LIVE_PROBE_EXIT=0`, finans alanıyla ilgili yanıt |
| Kod ve Agent Hub birim testleri | PASS: sınanmış aday | Onarım öncesi `test_codex_adapter`, `test_record_operation`, `test_agent_hub`: toplam **32/32** PASS; Windows `.cmd` yolu sonradan düzeltildi, tüm regresyonlar yeniden çalıştırılmalı |
| Claude Code | BLOCKED | Headless review: `Not logged in · Please run /login` |
| Gemini CLI | BLOCKED | `IneligibleTierError: UNSUPPORTED_CLIENT`, mevcut ücretsiz hesap türü desteklenmiyor |
| Ollama bağımsız kod incelemesi | BLOCKED | `qwen2.5-coder:3b` isteği `ReadTimeout`; `reports/agent_gateway_review.json` kanıtı |
| Figma | BLOCKED: araç sınırı | Figma dosyası oluşturuldu, Starter MCP limit nedeniyle düzenlenebilir tasarım ekranı tamamlanmadı |
| Matriks gerçek veri yetkisi | BLOCKED | Yetkili canlı olay alınmadı; test için sağlayıcı erişim/süre onayı gerekli |
| Dört aşamalı gerçek otonomi ve otomatik geri alma | BLOCKED | Kod değişikliği + deterministik test + bağımsız onay + rollback uçtan uca kanıtlanmadı |

## Kodun mevcut durumu

- `core/agent_hub/adapters/codex_adapter.py`: Güvenli `codex exec` çalıştırma; varsayılan `read-only`, sınırlı süre, ayrı çalışma ağacı; `workspace-write` ancak açık yapılandırma ile etkin.
- `tests/test_codex_adapter.py`: Sürüm, timeout, hata, eksik yürütücü, gizli ortam değişkenlerinin aktarılmaması ve yazma kapısı için deterministik testler.
- `scripts/smoke_codex_live.py`: Canlı fakat salt-okunur Codex çağrısı.
- `scripts/record_operation.py`: Ortak yapılandırılmış olay günlüğü aracı; diğer ajanların yürütücülerine zorunlu otomatik bağlanması tamamlanmadı.

## Sıradaki net işler

1. Bu dalda deterministik test ve dosya bütünlüğünü tekrar doğrula; başarısızsa PASS verme.
2. Bağımsız gözlemciyi uygun ve erişilebilir bir modelle çalıştır; Claude girişi ve Gemini istemci uygunluğu olmadan bu araçları çalışıyor sayma.
3. Geliştirici/planlayıcı/test/denetçi zincirinde gerçekten kaynak dosya değiştirme, test, denetim ve otomatik rollback'i kanıtla.
4. Ortak GitHub olay günlüğünü tüm gerçek yürütücülere bağla; gizli değerleri herkese açık depoya asla gönderme.
5. Figma Starter sınırı ve Matriks test lisansını ayrı engeller olarak tut; ANKA Finans uygulamasının geliştirilmesi bu harici sınırlar nedeniyle toptan durmaz.

**Durum:** `PARTIAL_AGENT_ACCESS`; `FULL_AUTONOMY=BLOCKED`. Dört rolün yanıt üretmesi, tam otonom yazılım geliştirme anlamına gelmez.
