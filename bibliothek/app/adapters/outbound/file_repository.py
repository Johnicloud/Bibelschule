"""Ausgehender Adapter: der Inhalt der PDF-Dateien, je Buch zwei mögliche Dateien (Original-Scan, Text-PDF).
Bewusst ohne tägliche Sicherung (wie beim Skripte-Dienst) – der Inhalt kann groß werden, ein erneuter Upload
ersetzt ihn ohnehin."""
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_bytes
from app.application.ports import DateiSpeicher


class FileSystemDateiSpeicher(DateiSpeicher):
    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def _pfad(self, buch_id: str, art: str) -> Path:
        return self.folder / f"{buch_id}-{art}.pdf"

    def speichere_original(self, buch_id: str, inhalt: bytes) -> None:
        atomic_write_bytes(self._pfad(buch_id, "original"), inhalt)

    def original(self, buch_id: str) -> bytes | None:
        pfad = self._pfad(buch_id, "original")
        return pfad.read_bytes() if pfad.exists() else None

    def speichere_text(self, buch_id: str, inhalt: bytes) -> None:
        atomic_write_bytes(self._pfad(buch_id, "text"), inhalt)

    def text_pdf(self, buch_id: str) -> bytes | None:
        pfad = self._pfad(buch_id, "text")
        return pfad.read_bytes() if pfad.exists() else None

    def loesche(self, buch_id: str) -> None:
        self._pfad(buch_id, "original").unlink(missing_ok=True)
        self._pfad(buch_id, "text").unlink(missing_ok=True)
