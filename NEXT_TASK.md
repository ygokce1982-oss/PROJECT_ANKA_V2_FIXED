# Sonraki Görev

Görev: ANKA-012
Başlık: Ollama Yerel Yapay Zekâ Adaptörü

Amaç:
- `core/ai/ollama_agent.py` içinde bir yerel Ollama adaptörü tanımlamak
- Gerçek internete bağlanmadan, sadece API altyapısını hazırlamak
- Offline testler ile doğrulamak

Kabul ölçütleri:
- OllamaAgent `BaseAgent`'dan türetilmiş
- `run()` `AgentResult` sözleşmesine uygun dönüş sağlıyor
- `health_check()` Ollama erişimini kontrol ediyor
- `core/ai/__init__.py` OllamaAgent'i dışarı aktarıyor
- Testler ağ bağlantısı olmadan çalışıyor
- MarketData, UI ve sağlayıcı dosyaları değişmedi
