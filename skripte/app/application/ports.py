"""Ports: so sieht die Anwendung ihre Umwelt."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import Skript


class SkriptRepository(ABC):
    """Ausgehender Port: Speicher der Angaben (Metadaten)."""
    @abstractmethod
    def list(self, subject_id: str | None = None) -> list[Skript]: ...

    @abstractmethod
    def get(self, skript_id: str) -> Skript | None: ...

    @abstractmethod
    def save(self, skript: Skript) -> None: ...

    @abstractmethod
    def delete(self, skript_id: str) -> None: ...

    @abstractmethod
    def delete_subject(self, subject_id: str) -> list[Skript]:
        """Löscht alle Skripte eines Fachs aus den Angaben und gibt sie zurück (damit auch ihr Inhalt gelöscht werden kann)."""


class DateiSpeicher(ABC):
    """Ausgehender Port: der Inhalt der hochgeladenen Dateien."""
    @abstractmethod
    def speichere(self, skript_id: str, inhalt: bytes) -> None: ...

    @abstractmethod
    def lies(self, skript_id: str) -> bytes | None: ...

    @abstractmethod
    def loesche(self, skript_id: str) -> None: ...

    @abstractmethod
    def vorhanden(self, skript_id: str) -> bool: ...


class DateiLeser(ABC):
    """Ausgehender Port: liest Text aus einer Datei (PDF, Word .docx, Pages)."""
    @abstractmethod
    def zeilen(self, dateiname: str, inhalt: bytes) -> list[str]:
        """Der Text als Zeilen (PDF) bzw. Absätze (Word). Wirft InvalidInput, wenn das Format nicht lesbar ist."""

    @abstractmethod
    def pdf_vorschau(self, dateiname: str, inhalt: bytes) -> bytes | None:
        """Eine PDF-Ansicht der Datei, wenn der Browser sie nicht selbst anzeigen kann (Pages), sonst None."""


class Texterkennung(ABC):
    """Ausgehender Port: macht ein gescanntes PDF (nur Bilder) durchsuchbar und kopierbar."""
    @abstractmethod
    def erkennen(self, pdf: bytes) -> bytes:
        """Das PDF mit unsichtbarer Textebene über den Seitenbildern (Aussehen bleibt gleich). Wirft InvalidInput bei Fehlern."""
