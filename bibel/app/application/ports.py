"""Ports: so sieht die Anwendung ihre Umwelt."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import Bibelindex, Vers


class IndexRepository(ABC):
    """Ausgehender Port: die Buch-Seiten-Zuordnung (nicht die PDF-Datei selbst)."""
    @abstractmethod
    def get(self) -> Bibelindex | None: ...

    @abstractmethod
    def save(self, index: Bibelindex) -> None: ...


class VersRepository(ABC):
    """Ausgehender Port: die herausgelesenen Bibelverse."""
    @abstractmethod
    def ersetze_alle(self, verse: list[Vers]) -> None: ...

    @abstractmethod
    def kapitel(self, buch_index: int, kapitel: int) -> list[Vers]: ...

    @abstractmethod
    def hat_verse(self) -> bool: ...


class DateiSpeicher(ABC):
    """Ausgehender Port: der Inhalt der einen hinterlegten Bibel-PDF-Datei."""
    @abstractmethod
    def speichere(self, inhalt: bytes) -> None: ...

    @abstractmethod
    def lies(self) -> bytes | None: ...


class PdfText(ABC):
    """Ausgehender Port: liest eine PDF-Datei und versucht, die Startseite jedes Bibelbuchs zu erkennen."""
    @abstractmethod
    def buchseiten_erkennen(self, pdf: bytes) -> dict[int, int]:
        """{buch_index: pdf_seite (1-basiert)} für die Bücher, die erkannt wurden. Fehlende Bücher trägt
        man von Hand nach (siehe Entscheidungen: automatische Erkennung ist ein Vorschlag, kein Zwang)."""


class VerseExtractor(ABC):
    """Ausgehender Port: liest den eigentlichen Verstext eines Buches aus der PDF (siehe verse_extractor.py)."""
    @abstractmethod
    def buch_verse(self, pdf: bytes, von_seite: int, bis_seite: int | None) -> list[tuple[int, int, str]]:
        """[(kapitel, vers, text), ...] für ein Buch, zwischen `von_seite` und `bis_seite` (1-basiert, inklusive,
        None = bis zum Ende der Datei)."""
