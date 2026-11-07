"""Ports: so sieht die Anwendung ihre Umwelt."""
from abc import ABC, abstractmethod

from app.domain.models import Predigt


class PredigtRepository(ABC):
    """Ausgehender Port: Speicher der Angaben zu den Predigten (Metadaten, nicht die Datei)."""
    @abstractmethod
    def list(self) -> list[Predigt]: ...

    @abstractmethod
    def get(self, predigt_id: str) -> Predigt | None: ...

    @abstractmethod
    def save(self, predigt: Predigt) -> None: ...

    @abstractmethod
    def delete(self, predigt_id: str) -> None: ...


class DateiSpeicher(ABC):
    """Ausgehender Port: der Inhalt der hochgeladenen Datei je Predigt (meist eine PDF). Anders als bei
    bibliothek keine Texterkennung in diesem ersten Durchgang (siehe Projektnotizen) – darum nur eine Datei
    je Predigt, kein Original/Text-Paar."""
    @abstractmethod
    def speichere(self, predigt_id: str, inhalt: bytes) -> None: ...

    @abstractmethod
    def lies(self, predigt_id: str) -> bytes | None: ...

    @abstractmethod
    def loesche(self, predigt_id: str) -> None: ...


class BibelVerweise(ABC):
    """Ausgehender Port: meldet einen Verweis auf eine Bibelstelle direkt beim Bibel-Dienst an bzw. entfernt
    ihn wieder (siehe dessen generischer Verweis-Mechanismus, Entscheidungen: Bibel als Grundlage). Gibt beim
    Anlegen die Verweis-ID zurück (oder None, wenn der Bibel-Dienst gerade nicht erreichbar ist – eine Predigt
    muss sich auch ohne ihn anlegen/bearbeiten/löschen lassen, siehe ollama bei pdfcreator als Vorbild für
    diese Haltung: ein Nebenaufruf darf das Hauptgeschäft nie zum Scheitern bringen)."""
    @abstractmethod
    def anlegen(self, stelle: str, referenz: str) -> str | None: ...

    @abstractmethod
    def loeschen(self, verweis_id: str) -> None: ...
