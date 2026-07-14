# Sonraki Görev

Görev: ANKA-007
Başlık: CryptoProvider geliştirme ve çevrimdışı birim testleri

Amaç:
- CoinGecko birincil kaynak olarak kullanılacak bir `CryptoProvider` tasarlamak
- Binance yedek kaynak mantığını tanımlamak
- Gerçek internete bağlanmayan birim testler oluşturmak
- Henüz `MarketData` entegrasyonu yapmamak

Kabul ölçütleri:
- CryptoProvider sınıfı mantıklı bir iskelete sahip
- Testler ağ bağlantısı olmadan çalışıyor
- CoinGecko ve Binance kaynakları için ayrı kaynak senaryoları belirlendi
- Üretim kodu ve UI değişiklikleri yapılmadı
