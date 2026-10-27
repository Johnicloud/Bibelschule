"""Ports: so sieht die Anwendung ihre Umwelt."""
from abc import ABC, abstractmethod


class BibelQuelle(ABC):
    """Ausgehender Port: der Verstext eines Kapitels, vom Bibel-Dienst geholt."""
    @abstractmethod
    def kapitel(self, buch_kurz: str, kapitel: int) -> str:
        """Der laufende Text des Kapitels, oder ein leerer String, wenn dafür noch kein Verstext eingelesen ist."""


class TextKI(ABC):
    """Ausgehender Port: ein lokales Sprachmodell (Ollama), das nur Vorschläge liefert, nie automatisch handelt."""
    @abstractmethod
    def frage(self, prompt: str) -> str: ...
