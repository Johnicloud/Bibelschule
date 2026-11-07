"""Ports: so sieht die Anwendung ihre Umwelt."""
from abc import ABC, abstractmethod

from app.domain.models import KommentarEintrag, Quelle


class QuellenRepository(ABC):
    """Ausgehender Port: die Kommentarwerke selbst (Titel, Autor, Lizenz, …)."""
    @abstractmethod
    def list(self) -> list[Quelle]: ...

    @abstractmethod
    def get(self, quelle_id: str) -> Quelle | None: ...

    @abstractmethod
    def save(self, quelle: Quelle) -> None: ...

    @abstractmethod
    def delete(self, quelle_id: str) -> None: ...


class EintraegeRepository(ABC):
    """Ausgehender Port: die einzelnen Kommentar-Einträge."""
    @abstractmethod
    def zu_stelle(self, buch_index: int, kapitel: int, vers: int) -> list[KommentarEintrag]:
        """Alle Einträge (gleich welcher Quelle), deren Bereich diesen Vers einschließt."""

    @abstractmethod
    def zu_quelle(self, quelle_id: str) -> list[KommentarEintrag]: ...

    @abstractmethod
    def get(self, eintrag_id: str) -> KommentarEintrag | None: ...

    @abstractmethod
    def save(self, eintrag: KommentarEintrag) -> None: ...

    @abstractmethod
    def save_alle(self, eintraege: list[KommentarEintrag]) -> None:
        """Mehrere Einträge auf einmal speichern (Import einer ganzen Quelle)."""

    @abstractmethod
    def delete(self, eintrag_id: str) -> None: ...

    @abstractmethod
    def delete_zu_quelle(self, quelle_id: str) -> list[KommentarEintrag]:
        """Löscht alle Einträge einer Quelle (z. B. vor einem erneuten Import) und gibt sie zurück, damit ihre
        Verweise beim Bibel-Dienst mit aufgeräumt werden können."""


class BibelVerweise(ABC):
    """Ausgehender Port: legt beim Bibel-Dienst Verweise auf Bibelstellen an/ab (siehe Entscheidungen
    „Bibel als Grundlage“, generischer Verweis-Mechanismus des Bibel-Diensts)."""
    @abstractmethod
    def anlegen(self, stelle: str, referenz: str, titel: str | None) -> str: ...

    @abstractmethod
    def loeschen(self, verweis_id: str) -> None: ...
