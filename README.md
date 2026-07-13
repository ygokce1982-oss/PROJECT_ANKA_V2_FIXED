# PROJECT ANKA V2

PROJECT ANKA V2, PySide6 ile geliştirilen masaüstü piyasa takip terminalinin
kurtarılmış ve sağlamlaştırılmış sürümüdür.

## Mevcut özellikler

- Koyu temalı masaüstü arayüzü
- Piyasalar, grafik, yapay zekâ, haberler, portföy ve ayarlar bölümleri
- USD/TRY ve EUR/TRY döviz verileri
- BTC/USD spot fiyatı
- Arayüzü dondurmayan arka plan veri yenilemesi
- Veri kaynağı sorunlarını kullanıcıya gösteren durum mesajları

XU100 ve altın kartları sonraki geliştirme aşaması için yer tutucu olarak
bırakılmıştır.

## Gereksinimler

- Python 3.11 veya daha yeni bir sürüm
- İnternet bağlantısı

## Windows'ta kurulum

PowerShell'i proje klasöründe açın:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

PowerShell sanal ortamı etkinleştirmeye izin vermiyorsa:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

## Testler

```powershell
python -m unittest discover -s tests -v
```

İsteğe bağlı kod kontrolü:

```powershell
python -m pip install -r requirements-dev.txt
ruff check .
ruff format --check .
```

## Proje yapısı

```text
PROJECT_ANKA_V2_FIXED/
├── app.py
├── core/
├── ui/
│   └── components/
├── tests/
├── assets/
├── data/
├── docs/
└── logs/
```

## Veri kaynakları

- Döviz kurları: ExchangeRate-API açık uç noktası
- BTC/USD: Coinbase açık spot fiyat uç noktası

Uygulamadaki değerler yalnızca bilgilendirme amaçlıdır; yatırım tavsiyesi
değildir.
