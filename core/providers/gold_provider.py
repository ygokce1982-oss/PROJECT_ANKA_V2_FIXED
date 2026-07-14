"""Altın verisi sağlayıcısı için sağlayıcı modülü."""

from typing import Any, Dict

from .base_provider import BaseProvider


class GoldProvider(BaseProvider):
    """Gram altın/TL fiyatını işlemek için sağlayıcı sınıfı."""

    def connect(self) -> None:
        """Şimdilik hiçbir canlı bağlantı açmaz."""
        return None

    def fetch(self) -> Dict[str, str]:
        """Canlı veri kaynağı yapılandırılmadığında hata fırlatır."""
        raise NotImplementedError(
            "Onaylanmış altın veri kaynağı henüz yapılandırılmadı"
        )

    def parse(self, raw_data: Any) -> Dict[str, float]:
        """Ham gram altın/TL verisini sayısal bir sözlüğe çevirir."""
        if not isinstance(raw_data, dict):
            raise TypeError("Beklenmeyen payload tipi")

        if "gold_try" not in raw_data:
            raise ValueError("Altın verisi eksik")

        return {"gold_try": float(raw_data["gold_try"])}

    def validate(self, parsed_data: Any) -> bool:
        """Altın fiyatının sayısal ve pozitif olduğunu doğrular."""
        try:
            value = float(parsed_data["gold_try"])
            return value > 0
        except Exception:
            return False

    def format(self, parsed_data: Any) -> Dict[str, str]:
        """Geçerli parsed_data değerini kullanıcıya gösterilecek biçime çevirir."""
        value = float(parsed_data["gold_try"])
        return {"gold": f"₺{value:,.2f}"}
