"""Ports: so sieht die Anwendung ihre Umwelt."""
from abc import ABC, abstractmethod

from app.domain.models import RegisterEntry


class RegisterRepository(ABC):
    """Ausgehender Port: Speicher."""
    @abstractmethod
    def list(self, subject_id: str | None = None) -> list[RegisterEntry]: ...

    @abstractmethod
    def get(self, entry_id: str) -> RegisterEntry | None: ...

    @abstractmethod
    def save(self, entry: RegisterEntry) -> None: ...

    @abstractmethod
    def delete(self, entry_id: str) -> None: ...

    @abstractmethod
    def delete_subject(self, subject_id: str) -> None: ...


class EventPublisher(ABC):
    """Ausgehender Port: meldet Ereignisse an einen übergeordneten/externen Service."""
    @abstractmethod
    def publish(self, event: str, payload: dict) -> None: ...
