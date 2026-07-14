"""Forex / döviz verisi sağlayıcısı için iskelet modül."""

from .base_provider import BaseProvider


class ForexProvider(BaseProvider):
    """Döviz kuru verilerini getiren sağlayıcı sınıfı."""

    def fetch(self):
        """Döviz verisi almak için kullanılacak yöntem."""
        raise NotImplementedError
