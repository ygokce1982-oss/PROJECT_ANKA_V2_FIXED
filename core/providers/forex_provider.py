"""Forex / döviz verisi sağlayıcısı için iskelet modül.

Bu modül, `BaseProvider` sınıfından türeyen ve USD/TRY ile EUR/TRY
değerlerini sağlayacak bir sağlayıcı iskeleti sunar. Metot gövdeleri
şimdilik `NotImplementedError` yerine basit iskelet davranışlarıyla
tanımlanmıştır; gerçek API çağrıları ve hata yönetimi daha sonra eklenecektir.
"""

from typing import Any, Dict

import requests

from .base_provider import BaseProvider


class ForexProvider(BaseProvider):
    """Döviz kuru verilerini getiren sağlayıcı sınıfı.

    Bu sınıf USD temelinde döviz kurları sağlayan bir servisden
    `usdtry` ve `eurtry` oranlarını alacak şekilde tasarlanmıştır.
    """

    EXCHANGE_RATES_URL = "https://open.er-api.com/v6/latest/USD"
    REQUEST_TIMEOUT = 8

    def __init__(self) -> None:
        self.session: requests.Session | None = None

    def connect(self) -> None:
        """İsteğe bağlı: kalıcı bir `requests.Session` oluşturur."""
        if self.session is None:
            self.session = requests.Session()

    def fetch(self) -> Dict[str, float]:
        """Ham JSON veriyi alır, ayrıştırır ve doğrulanmış sözlük döndürür.

        Döndürülen sözlük anahtarları: `usdtry`, `eurtry` (her ikisi de float).
        """
        self.connect()
        assert self.session is not None

        response = self.session.get(
            self.EXCHANGE_RATES_URL,
            timeout=self.REQUEST_TIMEOUT,
            headers={
                "User-Agent": "PROJECT-ANKA-V2/2.0",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()

        payload = response.json()
        parsed = self.parse(payload)
        if not self.validate(parsed):
            raise ValueError("Forex verisi doğrulamada başarısız oldu")

        return parsed

    def parse(self, raw_data: Any) -> Dict[str, float]:
        """Ham API yanıtından `usdtry` ve `eurtry` değerlerini çıkarır.

        Beklenen kaynak biçimi: ExchangeRate-API benzeri bir sözlük
        içinde `rates` alanı ve `TRY`, `EUR` anahtarları.
        """
        if not isinstance(raw_data, dict):
            raise TypeError("Beklenmeyen payload tipi")

        if raw_data.get("result") != "success":
            raise ValueError("Döviz servisi başarısız sonuç döndürdü")

        rates = raw_data.get("rates", {})
        usdtry = float(rates["TRY"])
        usdeur = float(rates["EUR"])

        if usdeur == 0:
            raise ValueError("Geçersiz EUR kuru")

        eurtry = usdtry / usdeur

        return {"usdtry": usdtry, "eurtry": eurtry}

    def validate(self, parsed_data: Any) -> bool:
        """Basit doğrulama: anahtarların varlığı ve pozitif değerler."""
        try:
            usd = float(parsed_data["usdtry"])
            eur = float(parsed_data["eurtry"])
            return usd > 0 and eur > 0
        except Exception:
            return False
