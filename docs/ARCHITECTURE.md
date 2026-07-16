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
- `core/ai/mock_agent.py`: gerçek API bağımlılığı olmadan çalışan test ajanı
- `core/ai/ollama_agent.py`: Ollama yerel model adaptörü
- `core/ai/orchestrator.py`: birden fazla ajanın koordine edildiği orkestratör
- `core/ai/task_router.py`: gelen görevin içeriğine göre uygun yapay zekâ rolünü seçen görev yönlendiricisi
- `core/ai/workflow.py`: sıralı iş akışı yönetimi
- `ui/components/ai_panel.py`: kullanıcı tarafından görev girilen, analiz başlatılan ve sonuçların gösterildiği AI sayfası
- `ui/ai_worker.py`: UI thread'ini kilitlemeden LocalAITeam işlemlerini yürüten QThread tabanlı işçi
- Ajanlar `name` ve `role` alanına sahip
- Görevler tüm ajanlara veya role göre gönderilebilir
- Yönlendirme katmanı görev tipine göre `coder`, `reviewer`, `researcher`, `analyst` rollerini seçer
- Hata veren ajan çalışmalarını durdurmaz, diğer sonuçlar dönmeye devam eder
- İş akışı `WorkflowStep` ve `WorkflowResult` ile adımları yönetir

## Agent Hub Katmanı
- `core/agent_hub/models.py`: kalıcı görev kaydı ve durum modelleri
- `core/agent_hub/task_store.py`: SQLite tabanlı kalıcı görev kuyruğu
- `core/agent_hub/agent_registry.py`: role göre ajan seçimi ve benzersiz kayıt
- `core/agent_hub/approval_policy.py`: onay gerektiren görevleri kontrollü olarak engelleme
- `core/agent_hub/scheduler.py`: önceliğe göre görev seçme ve çalıştırma kontrolü
- `core/agent_hub/hub.py`: başlatma, görev atama ve sonuç güncelleme
- `core/agent_hub/adapters`: yerel ve test adaptörleri
- Görev durumları `queued`, `running`, `review`, `blocked`, `completed`, `failed`, `cancelled`
- Görevler tekrar başlatıldıktan sonra kaybolmaz; SQLite ile kalıcı depolama sağlanır
