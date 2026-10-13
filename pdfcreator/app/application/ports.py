"""Ports: so sieht die Anwendung ihre Umwelt."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import Vorlage


class VorlageRepository(ABC):
    """Ausgehender Port: Speicher der Angaben zu den Vorlagen (Metadaten, nicht die Datei)."""
    @abstractmethod
    def list(self) -> list[Vorlage]: ...

    @abstractmethod
    def get(self, vorlage_id: str) -> Vorlage | None: ...

    @abstractmethod
    def save(self, vorlage: Vorlage) -> None: ...

    @abstractmethod
    def delete(self, vorlage_id: str) -> None: ...


class DateiSpeicher(ABC):
    """Ausgehender Port: der Inhalt der PDF-Dateien selbst."""
    @abstractmethod
    def speichere(self, vorlage_id: str, inhalt: bytes) -> None: ...

    @abstractmethod
    def lies(self, vorlage_id: str) -> bytes | None: ...

    @abstractmethod
    def loesche(self, vorlage_id: str) -> None: ...


class PdfRenderer(ABC):
    """Ausgehender Port: schreibt Text an feste Stellen einer PDF-Vorlage, liest auch Text aus ihr."""
    @abstractmethod
    def fuelle(self, vorlage_pdf: bytes, werte: dict[str, str], felder: list) -> bytes:
        """Gibt die ausgefüllte PDF-Datei zurück. `felder` = Vorlage.felder, `werte` = {schluessel: text}."""

    @abstractmethod
    def text_auslesen(self, pdf: bytes) -> str:
        """Roher Text einer PDF-Datei, für den KI-Vorschlag bei neu hochgeladenen Vorlagen."""


class TextKI(ABC):
    """Ausgehender Port: ein lokales Sprachmodell (Ollama), das nur Vorschläge liefert, nie automatisch handelt."""
    @abstractmethod
    def frage(self, prompt: str) -> str: ...
