"""Ports: so sieht die Anwendung ihre Umwelt."""
from abc import ABC, abstractmethod

from app.domain.models import Kommentar


class KommentarRepository(ABC):
    """Ausgehender Port: Speicher der Kommentare."""
    @abstractmethod
    def list_zu_stelle(self, stelle: str) -> list[Kommentar]:
        """Älteste zuerst."""

    @abstractmethod
    def get(self, kommentar_id: str) -> Kommentar | None: ...

    @abstractmethod
    def save(self, kommentar: Kommentar) -> None: ...

    @abstractmethod
    def delete(self, kommentar_id: str) -> None: ...


class BibelVerweise(ABC):
    """Ausgehender Port: meldet einen Kommentar als Verweis beim Bibel-Dienst an (bzw. löst die Anmeldung
    wieder auf) – „was verweist hierher?“ bleibt dort an einer Stelle über alle Dienste hinweg beantwortbar
    (siehe Projektnotizen, „Bibel als Grundlage“)."""
    @abstractmethod
    def anlegen(self, stelle: str, referenz: str, titel: str | None) -> str | None:
        """Liefert die Verweis-ID, oder None, wenn der Bibel-Dienst gerade nicht erreichbar ist."""

    @abstractmethod
    def loeschen(self, verweis_id: str) -> None:
        """Fehler (z. B. Bibel-Dienst nicht erreichbar) blockieren das Löschen des Kommentars nicht."""
