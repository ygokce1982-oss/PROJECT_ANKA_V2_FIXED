# Sonraki Görev

Görev: ANKA-017
Başlık: Yerel Yapay Zekâ Paneli Entegrasyonu

Amaç:
- `ui/components/ai_panel.py` ile mevcut PySide6 arayüzüne yapay zekâ görev paneli eklemek
- `ui/ai_worker.py` ile arka plan işleyişini UI thread'den ayırmak
- `core/ai/local_team.py` kullanarak yerel Ollama modelini çalıştırmak
- Sonuçları, hata durumlarını ve model bilgisini kullanıcıya göstermek

Kabul ölçütleri:
- Kullanıcı çok satırlı görev metni girebilmeli
- "Analiz Et" düğmesi ile işlem başlatılmalı
- Analiz sürecinde düğme devre dışı kalmalı ve durum gösterilmeli
- Sonuçlar salt okunur alanda ve yalnızca nihai Türkçe içerik olarak gösterilmeli
- Boş görevde Türkçe uyarı verilmeli
- Ollama erişim hatası açıklayıcı biçimde gösterilmeli
- UI kapanırken çalışan thread güvenli şekilde sonlandırılmalı
- Testler sahte `LocalAITeam` ile çalıştırılmalı
