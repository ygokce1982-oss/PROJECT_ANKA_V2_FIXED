"""Sağlayıcı örneklerini yönetmek için iskelet modül."""

from .base_provider import BaseProvider


class ProviderManager:
    """Farklı veri sağlayıcılarını kaydeden ve yöneten sınıf."""

    def __init__(self) -> None:
        self.providers: dict[str, BaseProvider] = {}

    def register_provider(self, name: str, provider: BaseProvider) -> None:
        """Yeni bir sağlayıcı kaydeder."""
        self.providers[name] = provider

    def remove_provider(self, name: str) -> None:
        """Kayıtlı sağlayıcıyı kaldırır."""
        self.providers.pop(name, None)

    def get_provider(self, name: str) -> BaseProvider | None:
        """Kayıtlı sağlayıcıyı adıyla döndürür."""
        return self.providers.get(name)

    def list_providers(self) -> list[str]:
        """Kayıtlı sağlayıcı isimlerini döndürür."""
        return list(self.providers)
