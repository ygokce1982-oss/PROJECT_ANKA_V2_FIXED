# Sonraki Görev

Görev: ANKA-013
Başlık: Çoklu Yapay Zekâ İş Akışı

Amaç:
- `core/ai/workflow.py` içinde bir iş akışı yönetimi eklemek
- Coder, reviewer, researcher ve analyst adımlarını sıralı çalıştırmak
- Önceki adım çıktısını sonraki adıma aktarmak
- Offline testler ile doğrulamak

Kabul ölçütleri:
- `WorkflowStep` ve `WorkflowResult` veri modelleri tanımlandı
- `MultiAIWorkflow` adım ekleme, kaldırma ve sıralı çalıştırma sağlıyor
- Role uygun ajan bulunamazsa hata veriyor
- Zorunlu adım başarısızsa duruyor, isteğe bağlı adım başarısızsa devam ediyor
- Testler ağ bağlantısı olmadan çalışıyor
- MarketData, UI ve sağlayıcı dosyaları değişmedi
