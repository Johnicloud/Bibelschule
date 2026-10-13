"""Ports: so sieht die Anwendung ihre Umwelt."""
from abc import ABC, abstractmethod

from app.domain.models import Dozent


class DozentRepository(ABC):
    """Ausgehender Port: Speicher."""
    @abstractmethod
    def list(self) -> list[Dozent]: ...

    @abstractmethod
    def get(self, dozent_id: str) -> Dozent | None: ...

    @abstractmethod
    def save(self, dozent: Dozent) -> None: ...

    @abstractmethod
    def delete(self, dozent_id: str) -> None: ...
