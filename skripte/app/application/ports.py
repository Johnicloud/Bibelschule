"""Ports: so sieht die Anwendung ihre Umwelt."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.druckbogen import Textstueck
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

    @abstractmethod
    def groesse(self, skript_id: str) -> int | None: ...

    @abstractmethod
    def lies_bereich(self, skript_id: str, start: int, ende: int) -> bytes:
        """Die Bytes von `start` bis `ende` (beide einschließlich) – für Audio/Video, damit nicht alles geladen wird."""


class DateiLeser(ABC):
    """Ausgehender Port: liest Text aus einer Datei (PDF, Word .docx, Pages)."""
    @abstractmethod
    def zeilen(self, dateiname: str, inhalt: bytes) -> list[str]:
        """Der Text als Zeilen (PDF) bzw. Absätze (Word). Wirft InvalidInput, wenn das Format nicht lesbar ist."""

    @abstractmethod
    def hat_text(self, dateiname: str, inhalt: bytes) -> bool:
        """Hat das PDF schon eine Textebene (nicht gescannt)? Geprüft an den ersten Seiten."""

    @abstractmethod
    def textstuecke(self, dateiname: str, inhalt: bytes) -> list[Textstueck]:
        """Die Textstücke eines PDFs mit Lage und Schriftgröße (für Druckbögen); leer, wenn es nichts Passendes gibt."""

    @abstractmethod
    def seiten(self, dateiname: str, inhalt: bytes) -> list[str]:
        """Der Text je Seite (PDF, Pages), je Folie (PowerPoint) oder als eine „Seite“ (Word, Text); leer für alles ohne Text."""

    @abstractmethod
    def ansichtstext(self, dateiname: str, inhalt: bytes) -> str:
        """Der Text einer Datei als reiner Text zum Anzeigen (PowerPoint mit „Folie n“, OpenDocument)."""

    @abstractmethod
    def pdf_vorschau(self, dateiname: str, inhalt: bytes) -> bytes | None:
        """Eine PDF-Ansicht der Datei, wenn der Browser sie nicht selbst anzeigen kann (Pages), sonst None."""


class Texterkennung(ABC):
    """Ausgehender Port: macht ein gescanntes PDF (nur Bilder) durchsuchbar und kopierbar."""
    @abstractmethod
    def erkennen(self, pdf: bytes) -> bytes:
        """Das PDF mit unsichtbarer Textebene über den Seitenbildern (Aussehen bleibt gleich). Wirft InvalidInput bei Fehlern."""


class BildWandler(ABC):
    """Ausgehender Port: wandelt Bilder, die nicht jeder Browser anzeigt (iPhone-Fotos: HEIC), in JPEG um."""
    @abstractmethod
    def zu_jpeg(self, inhalt: bytes) -> bytes: ...
