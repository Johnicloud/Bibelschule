"""Ausgehender Adapter: der Inhalt der hochgeladenen Dateien, je eine Datei pro Skript-ID (ohne Endung,
der Dateiname steht in den Angaben)."""
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_bytes
from app.application.ports import DateiSpeicher


class FileSystemDateiSpeicher(DateiSpeicher):
    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def _pfad(self, skript_id: str) -> Path:
        return self.folder / skript_id

    def speichere(self, skript_id: str, inhalt: bytes) -> None:
        atomic_write_bytes(self._pfad(skript_id), inhalt)

    def lies(self, skript_id: str) -> bytes | None:
        pfad = self._pfad(skript_id)
        return pfad.read_bytes() if pfad.exists() else None

    def loesche(self, skript_id: str) -> None:
        self._pfad(skript_id).unlink(missing_ok=True)

    def vorhanden(self, skript_id: str) -> bool:
        return self._pfad(skript_id).exists()

    def groesse(self, skript_id: str) -> int | None:
        pfad = self._pfad(skript_id)
        return pfad.stat().st_size if pfad.exists() else None

    def lies_bereich(self, skript_id: str, start: int, ende: int) -> bytes:
        with self._pfad(skript_id).open("rb") as f:
            f.seek(start)
            return f.read(ende - start + 1)
