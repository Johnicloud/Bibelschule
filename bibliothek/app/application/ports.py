"""Ports: so sieht die Anwendung ihre Umwelt."""
from abc import ABC, abstractmethod

from app.domain.models import Buch


class BuchRepository(ABC):
    """Ausgehender Port: Speicher der Angaben zu den Büchern (Metadaten, nicht die Datei)."""
    @abstractmethod
    def list(self) -> list[Buch]: ...

    @abstractmethod
    def get(self, buch_id: str) -> Buch | None: ...

    @abstractmethod
    def save(self, buch: Buch) -> None: ...

    @abstractmethod
    def delete(self, buch_id: str) -> None: ...


class DateiSpeicher(ABC):
    """Ausgehender Port: der Inhalt der PDF-Dateien je Buch – das Original (meist ein Scan) und, falls schon
    erkannt, die durchsuchbare Text-PDF getrennt voneinander (das Original bleibt immer erhalten)."""
    @abstractmethod
    def speichere_original(self, buch_id: str, inhalt: bytes) -> None: ...

    @abstractmethod
    def original(self, buch_id: str) -> bytes | None: ...

    @abstractmethod
    def speichere_text(self, buch_id: str, inhalt: bytes) -> None: ...

    @abstractmethod
    def text_pdf(self, buch_id: str) -> bytes | None: ...

    @abstractmethod
    def loesche(self, buch_id: str) -> None: ...


class BildExtraktor(ABC):
    """Ausgehender Port: zerlegt eine PDF-Datei in ein Bild je Seite (ein gescanntes Buch ist meist genau
    das: eine Bild-Datei pro Seite in eine PDF gepackt)."""
    @abstractmethod
    def seiten_bilder(self, pdf: bytes) -> list[bytes]: ...


class OcrKI(ABC):
    """Ausgehender Port: ein lokales Sprachmodell mit Bildverständnis (Ollama, Vision-Modell), das den Text
    auf einer Seite liest. Nur ein Vorschlag, den man prüfen kann (siehe Entscheidungen: Ergebnisse der KI
    sind immer nur Vorschläge) – hier als durchsuchbare PDF statt als Text zum Nachlesen."""
    @abstractmethod
    def seite_lesen(self, bild: bytes) -> str: ...


class TextPdfBauer(ABC):
    """Ausgehender Port: legt den erkannten Text als unsichtbare Textebene über die ursprünglichen
    Seiten – das Bild bleibt sichtbar wie im Original, die PDF wird aber durchsuchbar/kopierbar."""
    @abstractmethod
    def baue(self, original_pdf: bytes, text_je_seite: list[str]) -> bytes: ...


class TextLeser(ABC):
    """Ausgehender Port: liest den Text aus einer PDF zurück (für die Volltextsuche über die Text-PDF,
    die `TextPdfBauer` gebaut hat)."""
    @abstractmethod
    def text(self, pdf: bytes) -> str: ...
