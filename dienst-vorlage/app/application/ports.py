"""Ports: so sieht die Anwendung ihre Umwelt."""
from abc import ABC, abstractmethod

from app.domain.models import Item


class ItemRepository(ABC):
    """Ausgehender Port: Speicher."""
    @abstractmethod
    def list(self, subject_id: str | None = None) -> list[Item]: ...

    @abstractmethod
    def get(self, item_id: str) -> Item | None: ...

    @abstractmethod
    def save(self, item: Item) -> None: ...

    @abstractmethod
    def delete(self, item_id: str) -> None: ...

    @abstractmethod
    def delete_subject(self, subject_id: str) -> None: ...


class EventPublisher(ABC):
    """Ausgehender Port: meldet Ereignisse an einen übergeordneten/externen Service."""
    @abstractmethod
    def publish(self, event: str, payload: dict) -> None: ...
