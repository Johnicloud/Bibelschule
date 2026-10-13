"""Ports: so sieht die Anwendung ihre Umwelt."""
from __future__ import annotations

from abc import ABC, abstractmethod


class PdfText(ABC):
    """Ausgehender Port: roher Text einer PDF-Datei (z. B. ein Aufgabenblatt)."""
    @abstractmethod
    def text_auslesen(self, pdf: bytes) -> str: ...


class TextKI(ABC):
    """Ausgehender Port: ein lokales Sprachmodell (Ollama), das nur Vorschläge liefert, nie automatisch handelt."""
    @abstractmethod
    def frage(self, prompt: str) -> str: ...
