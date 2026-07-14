# Sonraki Görev

Görev: ANKA-011
Başlık: Çoklu Yapay Zekâ Orkestrasyon Altyapısı

Amaç:
- `core/ai/` içinde çoklu ajan orkestrasyon altyapısı kurmak
- API anahtarı veya canlı model bağlantısı olmadan tasarlamak
- Offline testler ile doğrulamak

Kabul ölçütleri:
- `BaseAgent`, `AgentResult`, `MockAgent` ve `MultiAIOrchestrator` sınıfları tanımlanmış
- Ajan ekleme, kaldırma, listeleme, görev dağıtımı ve role bazlı hedefleme destekleniyor
- Hata veren ajan diğerlerini etkilemiyor
- Testler ağ bağlantısı olmadan çalışıyor
- MarketData, UI ve sağlayıcı dosyaları değişmedi
