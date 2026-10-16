"""Registered providers and explicit, traceable read-only fallback.

No sources, sessions or credentials are configured automatically. Freshness and
provenance policies belong to the consumer's acceptance callback. This manager
does not impose request timeouts or cancellation; each provider must bound I/O.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sized
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from .base_provider import BaseProvider


@dataclass(frozen=True)
class ProviderAttempt:
    provider: str
    status: str
    reason: str = ""


@dataclass(frozen=True)
class ProviderFetchResult:
    provider: str
    data: Any = field(repr=False)
    attempts: tuple[ProviderAttempt, ...]


class ProviderFailoverError(RuntimeError):
    """All attempts failed; no raw exception messages or payloads are included."""

    def __init__(self, attempts: tuple[ProviderAttempt, ...]) -> None:
        self.attempts = attempts
        details = " | ".join(f"{item.provider}: {item.reason}" for item in attempts)
        super().__init__(f"No valid market data provider: {details}")


class ProviderManager:
    """Register providers and fetch in priority order.

    Fetches and registry methods share a lock. Direct concurrent mutation of the
    compatibility ``providers`` dictionary is unsupported. Names are trusted
    configuration labels, not credentials. Accepted data remains a raw payload;
    callers must not log it indiscriminately.
    """

    def __init__(self) -> None:
        self.providers: dict[str, BaseProvider] = {}
        self._fetch_lock = RLock()

    def register_provider(self, name: str, provider: BaseProvider) -> None:
        """Yeni bir sağlayıcı kaydeder."""
        with self._fetch_lock:
            self.providers[name] = provider

    def remove_provider(self, name: str) -> None:
        """Kayıtlı sağlayıcıyı kaldırır."""
        with self._fetch_lock:
            self.providers.pop(name, None)

    def get_provider(self, name: str) -> BaseProvider | None:
        """Kayıtlı sağlayıcıyı adıyla döndürür."""
        with self._fetch_lock:
            return self.providers.get(name)

    def list_providers(self) -> list[str]:
        """Kayıtlı sağlayıcı isimlerini döndürür."""
        with self._fetch_lock:
            return list(self.providers)

    def fetch_with_failover(
        self, priority: Iterable[str], *, acceptance: Callable[[Any], bool] | None = None
    ) -> ProviderFetchResult:
        """Return the first nonempty payload accepted by both validation layers.

        This is synchronous and serializes shared-provider use through this
        manager. Provider exceptions expose only their class names in attempts.
        An absent/failed consumer freshness check is not a live-data guarantee.
        """
        if isinstance(priority, (str, bytes)):
            raise ValueError("Provider priority must be a collection of names")
        try:
            names = tuple(priority)
        except TypeError as error:
            raise ValueError("Provider priority must be iterable") from error
        if not names or not all(isinstance(name, str) and name.strip() for name in names):
            raise ValueError("At least one nonempty provider name is required")
        if len(names) != len(set(names)):
            raise ValueError("Repeated provider in fallback chain")
        if acceptance is not None and not callable(acceptance):
            raise ValueError("Consumer acceptance must be callable")

        with self._fetch_lock:
            attempts: list[ProviderAttempt] = []
            for name in names:
                provider = self.providers.get(name)
                if provider is None:
                    attempts.append(ProviderAttempt(name, "failed", "NOT_REGISTERED"))
                    continue
                try:
                    data = provider.fetch()
                    if data is None or (isinstance(data, Sized) and len(data) == 0):
                        raise ValueError("Empty provider data")
                    if provider.validate(data) is not True:
                        raise ValueError("Provider validation rejected data")
                    if acceptance is not None and acceptance(data) is not True:
                        raise ValueError("Consumer validation rejected data")
                except Exception as error:
                    attempts.append(ProviderAttempt(name, "failed", type(error).__name__))
                    continue
                attempts.append(ProviderAttempt(name, "success"))
                return ProviderFetchResult(name, data, tuple(attempts))
            raise ProviderFailoverError(tuple(attempts))
