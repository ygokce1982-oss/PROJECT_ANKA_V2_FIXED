"""BIST ve yerel piyasa verisi sağlayıcısı için iskelet modül."""

from .base_provider import BaseProvider


class BistProvider(BaseProvider):
    """BIST hisse ve endeks verilerini getiren sağlayıcı sınıfı."""

    def fetch(self):
        """BIST verisini almak için kullanılacak yöntem."""
        raise NotImplementedError
