"""Ausgehender Adapter: der Inhalt der hochgeladenen Datei je Predigt. Bewusst ohne tägliche Sicherung
(wie beim Skripte-/Bibliothek-Dienst) – der Inhalt kann groß werden, ein erneuter Upload ersetzt ihn ohnehin."""
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_bytes
from app.application.ports import DateiSpeicher


class FileSystemDateiSpeicher(DateiSpeicher):
    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def _pfad(self, predigt_id: str) -> Path:
        return self.folder / f"{predigt_id}.pdf"

    def speichere(self, predigt_id: str, inhalt: bytes) -> None:
        atomic_write_bytes(self._pfad(predigt_id), inhalt)

    def lies(self, predigt_id: str) -> bytes | None:
        pfad = self._pfad(predigt_id)
        return pfad.read_bytes() if pfad.exists() else None

    def loesche(self, predigt_id: str) -> None:
        self._pfad(predigt_id).unlink(missing_ok=True)
