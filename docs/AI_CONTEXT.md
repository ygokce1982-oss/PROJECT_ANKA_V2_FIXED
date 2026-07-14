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
- `ui/main_window.py`: ana pencere ve düzen
- `ui/workspace.py`: sayfa yönetimi
- `ui/sidebar.py`: sol menü
- `ui/components/dashboard.py`: dashboard ve veri yenileme işi
- `ui/components/info_card.py`: gösterge kartları
- `tests/`: birim testler

## Tamamlanan işler
- Çalışan PySide6 tabanlı arayüz
- Piyasa paneli gösterimi
- USD/TRY ve EUR/TRY değerlerinin alınması ve formatlanması
- Arka plan veri yenileme mekanizması
- Proje hata/bağlantı sorunlarına dair ön inceleme
- Proje hafızası ve dokümantasyon dosyaları oluşturuldu

## Açık sorunlar
- BTC servisleri ile ağ/SSL bağlantısı problemi var
- XU100 ve altın verisi hâlen yer tutucu
- `Grafik`, `Yapay Zekâ`, `Haberler`, `Portföy`, `Ayarlar` sayfaları gerçek işlevsellik taşımıyor
- Testte BTC JSON biçimi gerçek kodla tutarsız olabilir
- `toolbar.py` ve bazı klasörler boş veya eksik kullanılmakta

## Alınan kararlar
- GitHub projenin tek gerçek kaynağıdır.
- Hiçbir kritik bilgi yalnızca sohbet içinde bırakılmayacaktır.
- VS Code ana geliştirme ortamıdır.
- Codex uygulayıcı kodlama ajanıdır.
- ChatGPT mimari, görev planlama ve denetim rolündedir.
- LangGraph şu anda kurulmayacaktır.
- Önce çalışan temel sistem, sonra simülasyon, daha sonra Yapay Zekâ Meclisi geliştirilecektir.
- Finansal çıktılar kesin tahmin veya garanti olarak sunulmayacaktır.
- ANKA bir karar destek sistemi olarak tasarlanacaktır.

## Yapılmaması gerekenler
- Sohbet geçmişine tek başına güvenmek
- Henüz tamamlanmamış yapay zekâ veya finansal tavsiye modüllerini erkenden ürünleştirmek
- Test sürecini atlamak veya internete bağımlı testlere izin vermek

## Sonraki görev
- ANKA-002 — Test altyapısını doğrulama ve BTC test uyumsuzluğunu düzeltme

## Çalışma yöntemi
- Her oturumda Markdown üzerinden kayıt tutulacak.
- Görevler numaralandırılacak ve kısa, açık hedeflerle takip edilecek.
- Kod değişiklikleri, önce mevcut durumu korumaya odaklanacak.
- Yeni yapay zekâ bileşenleri ayrı bir plan ile eklenecek.
