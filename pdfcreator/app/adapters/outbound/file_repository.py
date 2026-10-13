"""Ausgehender Adapter: der Inhalt der PDF-Dateien, je eine Datei pro Vorlagen-ID."""
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_bytes
from app.application.ports import DateiSpeicher


class FileSystemDateiSpeicher(DateiSpeicher):
    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def _pfad(self, vorlage_id: str) -> Path:
        return self.folder / f"{vorlage_id}.pdf"

    def speichere(self, vorlage_id: str, inhalt: bytes) -> None:
        atomic_write_bytes(self._pfad(vorlage_id), inhalt)

    def lies(self, vorlage_id: str) -> bytes | None:
        pfad = self._pfad(vorlage_id)
        return pfad.read_bytes() if pfad.exists() else None

    def loesche(self, vorlage_id: str) -> None:
        self._pfad(vorlage_id).unlink(missing_ok=True)
