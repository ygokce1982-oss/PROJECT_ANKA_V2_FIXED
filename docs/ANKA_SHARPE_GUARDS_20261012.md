# ANKA Finans — 12 Ekim 2026: Sharpe ve kaynak tarihi korumaları

## Problem
11 Ekim gece bağımsızlığı bekleyen salt-okunur QA'da iki potansiyel hata kaydedildi:
1. `asof_utc` yalnızca zaman dilimi bilgisi açısından doğrulanıyordu; ileri tarihli veri kaynağı damgası kabul edilebiliyordu.
2. Ortak tarihler arasındaki bir veya birkaç kayıp işlem seansı, 90 günlük hareketli Sharpe hesabında tek bir günlük getiriye indirgenebiliyordu. Bu, risk-ayarlı getiriyi bozabilir.

## İzole düzeltme
- Kaynak zaman damgası UTC'de şu andan **5 dakikadan fazla ilerideyse** `FUTURE_SOURCE_TIMESTAMP` hatasıyla reddedilir. 5 dakika yalnızca sistem saatleri arasındaki küçük farkı tolere eder; piyasa verisinin güvenilirliğini ispatlamaz.
- Kesişen tarihler arasındaki dönemde herhangi bir varlığın başka bir seans gözlemi varsa, ilgili getiri hareketli Sharpe penceresinde **geçersiz** sayılır. Pencerenin tamamı kesintisiz geçerli günlük getirilerden oluşana kadar sonuç `None` kalır. Tarihler doldurulmaz.
- Fiyat-kapanışları üzerinden **kümülatif getiriyi korur**: kesinti olsa bile gözlemlenmiş uç noktalar arasındaki toplam fiyat değişimi hesaplanabilir. Bunun günlük Sharpe getiri olduğu iddia edilmez.
- Açık uyarı: gerçek borsa takvimi, kur dönüşümleri, düzeltilmiş kapanış ve temettü/bölünme kaynak kökeni halen bağımsız doğrulanmadı. Varsayılan sentetik veri canlı veri DEĞİLDİR.

## Sınırlar
- Bu koruma yalnızca veri girişindeki **gözlenebilen** takvim boşluklarını tespit eder. İki varlığın da verisi olmayan tatil ya da kesinti gerçek işlem takvimi olmadan tespit edilemez. Bu nedenle üretim kabulü değildir.
- Her varlığın işlem takvimi farklı olabilir. Çok piyasalı analizin gerçek kullanımı için yetkili resmi seans takvimi, ortak baz para birimi, kaynağı ispatlı toplam-getiri serisi gerekir.
- Varsayılan fiyatlar SENTETİK/DEMO ve kullanıcı CSV verisi doğrulanmamış kaynaktır. Bunları gerçek emir ya da yatırım tavsiyesi için kullanma.

## Kabul ve geri alma
- `tests/test_multi_asset_provenance_guards.py`: 4 regresyon testi: ileri tarih/zaman dilimi, bilinen kayıp seans, hafta sonu, açık veri kökeni uyarısı.
- Yeni izole Git çalışma dalı: `fix/anka-sharpe-guards-20261012`.
- Hedefli testler: **26/26 PASS**, 9,47 s.
- Tam çevrimdışı regresyon: **326/326 PASS**, 58,048 s, çıkış kodu 0. Windows Qt offscreen testi de dahil.
- Bağımsız kod denetimi (Antigravity Gemini 3.8 Flash Low, 2026-10-12): **PASS_WITH_LIMITS**; gerçek patch okundu. Bilinen eksik seansları `union_days` ile tespit edip Sharpe penceresini geçersiz kılması doğru bulundu. Denetim kaydı: yerel `Documents/ANKA_Overnight/ANKA_Gemini_Sharpe_Review_20261012.json`. Riskler: tüm varlıklarda ortak eksik günler, sistem saati kayması, resmî borsa takvimi yokluğu ve Python < 3.10 uyumsuzluğu.
- Ollama qwen2.5-coder:1.5b ve gemma3:1b incelemeleri **FAIL**: llama-server 0xc0000005. Antigravity Claude yanıtı yalnız inceleme niyetini bildirdi, gerekçeli karar sunmadı; PASS sayılmadı.
- Bağımsız denetimin bu dar düzeltme için sonucu PASS_WITH_LIMITS'tir; üretim veri/kaynak ve genel otonomi kabulü **BLOCKED** kalır.
- Ek kalite: `git diff --check` exit 0; Windows varsayılan Python ortamında Ruff kurulu olmadığından Ruff PASS denmedi.
- Başarısız inceleme veya yeni sınır durumunda ana dala birleştirme yok. Özellik dalındaki değişiklik `git revert` ile geri alınabilir; korunan kullanıcı Windows projesine hiç yazılmadı.
