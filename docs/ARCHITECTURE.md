# ARCHITECTURE

## Mevcut mimari
- `app.py`: uygulama başlangıç noktası
- `core/market_data.py`: piyasa veri katmanı
- `ui/main_window.py`: ana pencere
- `ui/workspace.py`: sayfa yönetimi
- `ui/sidebar.py`: sol menü
- `ui/components/dashboard.py`: piyasa paneli
- `ui/components/info_card.py`: bilgi kartı
- `tests/`: birim testleri

## Gelecekte önerilen katmanlar
- `domain/`
- `services/`
- `providers/`
- `simulation/`
- `analytics/`
- `ai/`
- `storage/`
- `ui/pages/`

## AI Orkestrasyon Katmanı
- `core/ai/base_agent.py`: ortak AI ajan arayüzü
- `core/ai/models.py`: `AgentResult` veri modeli
- `core/ai/mock_agent.py`: gerçek API bağımlılığı olmadan çalışan test ajanı- `core/ai/ollama_agent.py`: Ollama yerel model adaptörü- `core/ai/orchestrator.py`: birden fazla ajanın koordine edildiği orkestratör
- Ajanlar `name` ve `role` alanına sahip
- Görevler tüm ajanlara veya role göre gönderilebilir
- Hata veren ajan çalışmalarını durdurmaz, diğer sonuçlar dönmeye devam eder
