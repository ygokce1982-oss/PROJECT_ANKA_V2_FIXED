"""Temel veri sağlayıcı arayüzü ve ortak davranışlar."""

class BaseProvider:
    """Bütün veri sağlayıcılarının temel sınıfıdır.

    Bu sınıf, sağlayıcıların ortak yöntem ve özelliklerini tanımlar.
    """

    def connect(self):
        """Sağlayıcı ile bağlantı kurar."""
        raise NotImplementedError

    def fetch(self):
        """Veri sağlayıcıdan ham veri çeker."""
        raise NotImplementedError

    def parse(self, raw_data: object):
        """Ham veriyi uygulamanın kullanabileceği biçime dönüştürür."""
        raise NotImplementedError

    def validate(self, parsed_data: object) -> bool:
        """Ayrıştırılmış verinin geçerliliğini denetler."""
        raise NotImplementedError
