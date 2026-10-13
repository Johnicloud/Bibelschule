"""Ports: so sieht die Anwendung ihre Umwelt."""
from __future__ import annotations  # Methoden heißen `list`; ohne das wäre `list[...]` danach verdeckt
from abc import ABC, abstractmethod

from app.domain.models import Register, RegisterEntry


class RegisterRepository(ABC):
    """Ausgehender Port: Speicher für Register und ihre Einträge."""
    # Einträge
    @abstractmethod
    def list(self, subject_id: str | None = None) -> list[RegisterEntry]: ...

    @abstractmethod
    def get(self, entry_id: str) -> RegisterEntry | None: ...

    @abstractmethod
    def save(self, entry: RegisterEntry) -> None: ...

    @abstractmethod
    def delete(self, entry_id: str) -> None: ...

    # Register
    @abstractmethod
    def list_registers(self, subject_id: str | None = None) -> list[Register]: ...

    @abstractmethod
    def get_register(self, register_id: str) -> Register | None: ...

    @abstractmethod
    def save_register(self, register: Register) -> None: ...

    @abstractmethod
    def delete_register(self, register_id: str) -> None:
        """Löscht das Register samt seinen Einträgen."""

    @abstractmethod
    def delete_subject(self, subject_id: str) -> None: ...


class EventPublisher(ABC):
    """Ausgehender Port: meldet Ereignisse an einen übergeordneten/externen Service."""
    @abstractmethod
    def publish(self, event: str, payload: dict) -> None: ...
