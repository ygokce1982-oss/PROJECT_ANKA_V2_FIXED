"""Kripto para verisi sağlayıcısı için iskelet modül."""

from .base_provider import BaseProvider


class CryptoProvider(BaseProvider):
    """Kripto para fiyatlarını ve piyasa bilgisini getiren sağlayıcı sınıfı."""

    def fetch(self):
        """Kripto para verisini almak için kullanılacak yöntem."""
        raise NotImplementedError
