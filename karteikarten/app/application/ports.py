"""Ports: so sieht die Anwendung ihre Umwelt."""
from abc import ABC, abstractmethod
from app.domain.models import Card, Deck


class DeckRepository(ABC):
    """Ausgehender Port: Speicher."""
    @abstractmethod
    def list(self) -> list[Deck]: ...

    @abstractmethod
    def get(self, deck_id: str) -> Deck | None: ...

    @abstractmethod
    def save(self, deck: Deck) -> None: ...

    @abstractmethod
    def delete(self, deck_id: str) -> None: ...


class EventPublisher(ABC):
    """Ausgehender Port: meldet Ereignisse an einen übergeordneten/externen Service."""
    @abstractmethod
    def publish(self, event: str, payload: dict) -> None: ...


class PrintRenderer(ABC):
    """Ausgehender Port: baut einen druckbaren Bogen aus Karten (Vorder-/Rückseiten im Wechsel, für doppelseitigen
    Druck). `format` wählt die Kartengröße, z. B. "a7" oder "a8"."""
    @abstractmethod
    def druckbogen(self, cards: list[Card], format: str = "a7") -> bytes: ...
