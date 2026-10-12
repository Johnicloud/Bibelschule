"""Ports: so sieht der Kern seine Umwelt."""
from abc import ABC, abstractmethod

from app.domain.models import Subject


class SubjectRepository(ABC):
    """Ausgehender Port: Speicher der Fächer."""
    @abstractmethod
    def list(self) -> list[Subject]: ...

    @abstractmethod
    def get(self, subject_id: str) -> Subject | None: ...

    @abstractmethod
    def save(self, subject: Subject) -> None: ...

    @abstractmethod
    def delete(self, subject_id: str) -> None: ...


class ServiceGateway(ABC):
    """Ausgehender Port: das Dienstverzeichnis und der Draht zu den Diensten.

    Jeder Dienst erfüllt denselben kleinen Vertrag:
      GET    /api/health                      lebt der Dienst?
      PUT    /api/subjects/{id}   {name}      Fach anlegen/umbenennen
      DELETE /api/subjects/{id}               Daten des Fachs löschen
      GET    /api/subjects/{id}/status        Kennzahlen des Fachs für die Übersicht
    """
    @abstractmethod
    def names(self) -> list[str]: ...

    @abstractmethod
    def online(self, service: str) -> bool: ...

    @abstractmethod
    def put_subject(self, service: str, subject_id: str, name: str) -> bool: ...

    @abstractmethod
    def delete_subject(self, service: str, subject_id: str) -> bool: ...

    @abstractmethod
    def status(self, service: str, subject_id: str) -> dict | None: ...

    @abstractmethod
    def forward(self, service: str, method: str, path: str, query: str, body: bytes,
                content_type: str | None) -> tuple[int, bytes, str]: ...
