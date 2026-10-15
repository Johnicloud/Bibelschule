"""Ports: so sieht die Anwendung ihre Umwelt."""
from abc import ABC, abstractmethod


class TextToSpeech(ABC):
    """Ausgehender Port: vertont einen Text lokal (kein Cloud-Dienst, siehe Projektnotizen)."""
    @abstractmethod
    def sprich(self, text: str) -> bytes:
        """Gibt den Text als WAV-Audio zurück."""


class PdfText(ABC):
    """Ausgehender Port: liest den reinen Text aus einer PDF-Datei (wie beim aufgabenleser-Dienst)."""
    @abstractmethod
    def text_auslesen(self, pdf: bytes) -> str: ...
