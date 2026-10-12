"""Ports: so sieht die Anwendung ihre Umwelt."""
from abc import ABC, abstractmethod

from app.domain.models import ReadingTask


class ReadingRepository(ABC):
    """Ausgehender Port: Speicher."""
    @abstractmethod
    def list(self, subject_id: str | None = None) -> list[ReadingTask]: ...

    @abstractmethod
    def get(self, task_id: str) -> ReadingTask | None: ...

    @abstractmethod
    def save(self, task: ReadingTask) -> None: ...

    @abstractmethod
    def delete(self, task_id: str) -> None: ...

    @abstractmethod
    def delete_subject(self, subject_id: str) -> None: ...


class EventPublisher(ABC):
    """Ausgehender Port: meldet Ereignisse an einen übergeordneten/externen Service."""
    @abstractmethod
    def publish(self, event: str, payload: dict) -> None: ...
