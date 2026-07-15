# AI_CONTEXT

## Projenin amacı
PROJECT ANKA V2, masaüstü bir piyasa takip terminali olarak geliştirilmekte ve finansal veri göstergelerini hızlıca sunmayı hedeflemektedir.

## Kullanıcının hedefi
Kullanıcı, çalışan bir prototip üzerinden veri akışını ve UI entegrasyonunu doğrulamak, sonrasında test altyapısını düzeltmek ve yapay zekâ destekli analiz katmanına geçiş yapmaktır.

## Teknoloji yığını
- Python 3.11+
- PySide6
- requests
- unittest
- Ruff (kod kalitesi için)

## Mevcut mimari
- `app.py`: uygulama başlangıç noktası
- `core/market_data.py`: piyasa veri alımı ve formatlama
- `core/ai/local_team.py`: yerel Ollama iş akışı yönetimi
- `core/ai/workflow.py`: sıralı AI adımlarını yöneten iş akışı
- `core/ai/ollama_agent.py`: Ollama yerel model adaptörü
- `ui/main_window.py`: ana pencere ve düzen
- `ui/workspace.py`: sayfa yönetimi
- `ui/sidebar.py`: sol menü
- `ui/components/dashboard.py`: dashboard ve veri yenileme işi
- `ui/components/ai_panel.py`: AI paneli ve sonuç alanı
- `ui/ai_worker.py`: QThread tabanlı AI worker
- `ui/components/info_card.py`: gösterge kartları
- `tests/`: birim testler

## Tamamlanan işler
- Çalışan PySide6 tabanlı arayüz
- Piyasa paneli gösterimi
- USD/TRY ve EUR/TRY değerlerinin alınması ve formatlanması
- Arka plan veri yenileme mekanizması
- AI paneli PySide6 arayüzüne bağlandı
- AI işlemi QThread tabanlı worker ile UI thread'inden ayrıldı
- LocalAITeam kullanılarak yerel Ollama iş akışı entegre edildi
- AI paneli gemma3:1b ile manuel testten geçti
- Proje hafızası ve dokümantasyon dosyaları oluşturuldu
- Veri sağlayıcı altyapısı oluşturuldu
- ForexProvider geliştirildi ve MarketData sistemine bağlandı
- Testler sahte `LocalAITeam` ile çalıştırıldı

## Açık sorunlar
- BTC canlı kaynaklarında SSL/ağ sorunu
- XU100 gerçek veri kaynağı eksik
- Altın için onaylanmış canlı kaynak eksik
- qwen3 modelleri mevcut bilgisayarda yavaş çalışıyor
- `Grafik`, `Haberler`, `Portföy`, `Ayarlar` sayfaları gerçek işlevsellik taşımıyor

## Alınan kararlar
- GitHub projenin tek gerçek kaynağıdır.
- Hiçbir kritik bilgi yalnızca sohbet içinde bırakılmayacaktır.
- VS Code ana geliştirme ortamıdır.
- Codex uygulayıcı kodlama ajanıdır.
- ChatGPT mimari, görev planlama ve denetim rolündedir.
- LangGraph şu anda kurulmayacaktır.
- Önce çalışan temel sistem, sonra simülasyon, sonra Yapay Zekâ Meclisi geliştirilecektir.
- Finansal çıktılar kesin tahmin veya garanti olarak sunulmayacaktır.
- ANKA bir karar destek sistemi olarak tasarlanacaktır.
- USD/TRY ve EUR/TRY artık ForexProvider üzerinden alınıyor.

## Sonraki görev
- ANKA-019 — AI Paneli Hızlı/Takım Modları

## Yapılmaması gerekenler
- Sohbet geçmişine tek başına güvenmek
- Henüz tamamlanmamış yapay zekâ veya finansal tavsiye modüllerini erkenden ürünleştirmek
- Test sürecini atlamak veya internete bağımlı testlere izin vermek

## Çalışma yöntemi
- Her oturumda Markdown üzerinden kayıt tutulacak.
- Görevler numaralandırılacak ve kısa, açık hedeflerle takip edilecek.
- Kod değişiklikleri, önce mevcut durumu korumaya odaklanacak.
- Yeni yapay zekâ bileşenleri ayrı bir plan ile eklenecek.
