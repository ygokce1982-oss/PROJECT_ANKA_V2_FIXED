# Kurtarma notları

## Düzeltilenler

- Yarım kalmış ve bağlantısız Git yapısı temiz bir `main` dalıyla yeniden hazırlandı.
- `.gitignore` gerçek proje ihtiyaçlarına göre oluşturuldu.
- Boş README dosyası kurulum ve test talimatlarıyla dolduruldu.
- Yanlışlıkla dosya olarak oluşan `assets/icons`, `assets/images` ve
  `assets/sounds` gerçek klasörlere dönüştürüldü.
- Eski BTC veri adresi güncel, kimlik doğrulaması gerektirmeyen spot fiyat
  adresiyle değiştirildi.
- HTTP durum ve veri biçimi kontrolleri eklendi.
- Sessizce yutulan veri hataları loglanır ve arayüzde gösterilir hale getirildi.
- Ağ çağrıları arayüz iş parçacığından ayrıldı; açılışta donma riski azaltıldı.
- Tekrarlanan piyasa kartı kodu `InfoCard` bileşeninde birleştirildi.
- Piyasa veri katmanı için otomatik testler eklendi.

## Sonraki güvenli adımlar

1. Windows'ta sanal ortamı oluşturup `python app.py` ile uygulamayı açın.
2. GitHub Desktop ile bu klasörü yerel depo olarak ekleyin.
3. Hazırlanmış dosyaları `PROJECT ANKA V2 kurtarma başlangıcı` mesajıyla commit edin.
4. GitHub Desktop içinden `Publish repository` ile yeni ve tercihen özel bir depo oluşturun.
5. XU100 ve altın için veri kaynağı seçmeden önce kullanım şartlarını inceleyin.
