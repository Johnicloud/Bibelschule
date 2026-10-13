"""Ports: so sieht die Anwendung ihre Umwelt."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import Vers


class VersRepository(ABC):
    """Ausgehender Port: Speicher."""
    @abstractmethod
    def list(self) -> list[Vers]: ...

    @abstractmethod
    def get(self, vers_id: str) -> Vers | None: ...

    @abstractmethod
    def save(self, vers: Vers) -> None: ...

    @abstractmethod
    def delete(self, vers_id: str) -> None: ...

    @abstractmethod
    def delete_subject(self, subject_id: str) -> None: ...
