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
      GET    /api/manifest                    Steckbrief: name, label, panel, status-Felder
      GET    /api/subjects                    (optional) vorhandene Fächer, die der Kern übernehmen darf
    """
    @abstractmethod
    def names(self) -> list[str]: ...

    @abstractmethod
    def register(self, name: str, url: str) -> None:
        """Nimmt einen Dienst ins Verzeichnis auf (merkt sich ihn dauerhaft)."""

    @abstractmethod
    def manifest(self, service: str, live: bool = True) -> dict:
        """Steckbrief des Dienstes (label, panel, status). live=False nimmt nur den gemerkten."""

    @abstractmethod
    def list_subjects(self, service: str) -> list[dict] | None:
        """Fächer, die der Dienst schon hat ([{id, name}]); None, wenn er das nicht anbietet oder nicht erreichbar ist."""

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
