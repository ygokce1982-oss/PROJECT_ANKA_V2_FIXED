# Sonraki Görev

Görev: ANKA-020
Başlık: Otonom Agent Hub MVP

Amaç:
- Kalıcı SQLite tabanlı görev kuyruğu oluşturmak
- AgentRegistry ile role göre ajan seçimi sağlamak
- Scheduler ile önceliğe göre görev atamak
- Onay gerektiren görevleri bloke etmek
- OllamaAdapter ile mevcut Ollama altyapısını kullanmak

Kabul ölçütleri:
- Görevler `queued`, `running`, `review`, `blocked`, `completed`, `failed`, `cancelled` durumlarını desteklemeli
- Aynı görev iki kez çalışmamalı
- Başarısız görevler `max_attempts` sınırına kadar yeniden denenmeli
- Görevler program yeniden başladıktan sonra kaybolmamalı
- Testler tamamen çevrimdışı çalışmalı
- `logs/agent_hub.log` dosyasında günlük tutulmalı
