"""Ports: so sieht die Anwendung ihre Umwelt."""
from abc import ABC, abstractmethod

from app.domain.models import Einheit


class EinheitRepository(ABC):
    """Ausgehender Port: Speicher der Trainingseinheiten."""
    @abstractmethod
    def list(self) -> list[Einheit]:
        """Neueste zuerst."""

    @abstractmethod
    def get(self, einheit_id: str) -> Einheit | None: ...

    @abstractmethod
    def save(self, einheit: Einheit) -> None: ...

    @abstractmethod
    def delete(self, einheit_id: str) -> None: ...


class BibelQuelle(ABC):
    """Ausgehender Port: der Verstext eines Kapitels, vom Bibel-Dienst geholt."""
    @abstractmethod
    def kapitel(self, buch_kurz: str, kapitel: int) -> str:
        """Der laufende Text des Kapitels, oder ein leerer String, wenn dafür noch kein Verstext eingelesen ist."""
