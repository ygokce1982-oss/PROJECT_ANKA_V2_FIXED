"""Temel veri sağlayıcı arayüzü ve ortak davranışlar."""

class BaseProvider:
    """Bütün veri sağlayıcılarının temel sınıfıdır.

    Bu sınıf, sağlayıcıların ortak yöntem ve özelliklerini tanımlar.
    """

    def fetch(self):
        """Veri sağlayıcıdan veri çeker.

        Alt sınıflar bu yöntemi uygulamalıdır.
        """
        raise NotImplementedError
