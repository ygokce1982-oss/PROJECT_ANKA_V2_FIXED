"""Altın verisi sağlayıcısı için iskelet modül."""

from .base_provider import BaseProvider


class GoldProvider(BaseProvider):
    """Altın ve değerli metal verilerini getiren sağlayıcı sınıfı."""

    def fetch(self):
        """Altın verisini almak için kullanılacak yöntem."""
        raise NotImplementedError
