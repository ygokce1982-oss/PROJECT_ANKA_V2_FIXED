from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar
import unicodedata


def _normalize_text(raw_text: str) -> str:
    normalized = unicodedata.normalize("NFKC", raw_text.casefold())
    return normalized.replace("i̇", "i")


@dataclass(frozen=True)
class TaskRoute:
    role: str
    confidence: float
    reason: str


class AITaskRouter:
    """Görev metnini AI rolüne yönlendiren basit bir yönlendirici."""

    SUPPORTED_ROLES: ClassVar[tuple[str, ...]] = (
        "coder",
        "reviewer",
        "researcher",
        "analyst",
    )

    ROLE_KEYWORDS: ClassVar[dict[str, tuple[str, ...]]] = {
        "coder": (
            "kod",
            "yazma",
            "test",
            "hata",
            "düzelt",
            "debug",
            "implement",
            "uygulama",
        ),
        "reviewer": (
            "inceleme",
            "güvenlik",
            "kontrol",
            "doğrulama",
            "doğrula",
            "denet",
            "revizyon",
        ),
        "researcher": (
            "kaynak",
            "araştırma",
            "güncel",
            "bilgi",
            "incele",
            "özet",
            "soru",
        ),
        "analyst": (
            "finans",
            "risk",
            "değerlendirme",
            "özet",
            "analiz",
            "performans",
            "rapor",
        ),
    }

    def route(self, task: str, preferred_role: str | None = None) -> TaskRoute:
        if not task or not task.strip():
            raise ValueError("Görev metni boş olamaz")

        normalized = _normalize_text(task)
        preferred = _normalize_text(preferred_role) if preferred_role else None

        if preferred is not None and preferred in self.SUPPORTED_ROLES:
            return TaskRoute(
                role=preferred,
                confidence=0.9,
                reason=f"Tercih edilen geçerli rol kullanıldı: {preferred}",
            )

        for role, keywords in self.ROLE_KEYWORDS.items():
            if any(_normalize_text(keyword) in normalized for keyword in keywords):
                confidence = 0.85 if role != "analyst" else 0.8
                return TaskRoute(
                    role=role,
                    confidence=min(max(confidence, 0.0), 1.0),
                    reason=f"Görev metni '{role}' rolü için anahtar kelime eşleşmesi içeriyordu.",
                )

        return TaskRoute(
            role="analyst",
            confidence=0.6,
            reason="Özel bir eşleşme bulunamadı, güvenli varsayılan rol olarak 'analyst' seçildi.",
        )
