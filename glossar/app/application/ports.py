"""Ports: so sieht die Anwendung ihre Umwelt."""
from abc import ABC, abstractmethod

from app.domain.models import GlossarEintrag


class GlossarRepository(ABC):
    """Ausgehender Port: Speicher."""
    @abstractmethod
    def list(self) -> list[GlossarEintrag]: ...

    @abstractmethod
    def get(self, eintrag_id: str) -> GlossarEintrag | None: ...

    @abstractmethod
    def save(self, eintrag: GlossarEintrag) -> None: ...

    @abstractmethod
    def delete(self, eintrag_id: str) -> None: ...


class BibelVerweise(ABC):
    """Ausgehender Port: legt beim Bibel-Dienst Verweise auf Bibelstellen an/ab (siehe Entscheidungen
    „Bibel als Grundlage“, generischer Verweis-Mechanismus des Bibel-Diensts)."""
    @abstractmethod
    def anlegen(self, stelle: str, referenz: str, titel: str | None) -> str:
        """Legt einen Verweis an (art="glossar") und gibt dessen ID beim Bibel-Dienst zurück."""
        ...

    @abstractmethod
    def loeschen(self, verweis_id: str) -> None: ...
