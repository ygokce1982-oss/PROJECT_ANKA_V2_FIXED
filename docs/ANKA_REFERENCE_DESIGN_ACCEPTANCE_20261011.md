# ANKA Finans — Referans Tasarıma Göre Profesyonel Terminal

**Referans:** Kullanıcının 9 Ekim 2026 tarihli 1366 × 768 ANKA Finans piyasa izleme ekranı.
**Uygulama:** Windows / PySide6, izole Git çalışma dalı.
**Durum:** Profesyonel terminal *aday önizlemesi*; Figma katman kabulü ve nihai üretim onayı yok.

## Hedef görsel sözleşme

| Referans bölümü | Qt uygulamasındaki gerçek karşılığı |
| --- | --- |
| Üst ANKA FINANS çalışma alanı | 66 px markalı üst bant, DEMO durum göstergesi |
| BIST 100 / BIST 30 / kur / altın bandı | 36 px üst piyasa şeridi; tamamı örnek veri |
| Dar sol simge çubuğu | 72 px gezinme alanı ve altı gerçek uygulama sayfası |
| THYAO fiyat ve yüksek/düşük/hacim özeti | Seçili hisseye göre değişen 74 px enstrüman bandı |
| İzleme listesi | Şirket/sembol araması, satır seçimi ve farklı renkte artış/azalış |
| Piyasa taraması | Hacim artışı, Momentum, Gerileyenler filtreleri; tablo gerçekte değişir |
| İkinci tarama | Sektör / göreli hacim tablosu; satır seçimi üst özeti değiştirir |
| Teknik görünüm | MA/ATR/RSI ve aralık gösterimi; sabit örnek olduğu etiketlenir |
| Haber akışı | Örnek haber kayıtları; gerçek haber servisi olmadığı belirtilir |
| Çalışma alanını ayarlama | Yatay ve dikey QSplitter; kullanıcı panel genişliğini değiştirebilir |

## Tasarım iş akışı ve Figma

- Figma tasarım dosyası **oluşturuldu**: https://www.figma.com/design/ijVC43Q32AeaHDjrwSjCgP
- Figma Starter/View seat üzerindeki **MCP tool call limit** tasarım katmanları oluşturma çağrısını engelledi. Dosya şu anda boş; düzenlenebilir Figma sayfası tamamlanmadı.
- `docs/FIGMA_SYNC_DESIGN_SPEC_20261011.json` renk belirteçleri, panel yerleşimi, etkileşimler ve görsel kabul koşullarıyla gerçek kodu ilişkilendirir. Kota açıldığında Figma katmanları bu sözleşmeyle oluşturulacak, ardından gerçek Figma tasarım bağlamı tekrar alınarak Qt ekranı fark denetiminden geçirilecek.
- Fotoğrafı veya ekran görüntüsünü düzenlenebilir Figma katmanı diye sunmak yasaktır.

## Testler

- Ekran `scripts/render_terminal_preview.py` ile Qt uygulamasında gerçek `QWidget.grab` kullanılarak alınır.
- `tests/test_reference_workstation.py`: üç yeniden boyutlandırılabilir sütun, iki çoklu panel, hisse seçimi, şirket araması, tarama filtresi, çevrimdışı veri doğruluğu.
- **281/281** izole çevrimdışı `unittest` testleri PASS, çıkış kodu 0 (11 Ekim 2026).
- Ajanların genel anlamda tam otonom gerçek kod değişikliği / bağımsız gözlemci / otomatik rollback zinciri henüz kanıtlanmadı; `FULL_AUTONOMY=BLOCKED`.

## Güvenlik

Tüm piyasa rakamları **ÖRNEK/DEMO**; gerçek fiyat veya yatırım önerisi değildir. Gerçek emir ve hesap işlemleri kapalıdır. Windows kullanıcısının ana çalışma dizinindeki 28 önceki değişiklik ayrı tutulmuştur; main'e otomatik birleştirme yapılmaz.
