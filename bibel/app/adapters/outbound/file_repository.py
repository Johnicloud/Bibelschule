"""Ausgehender Adapter: der Inhalt der einen hinterlegten Bibel-PDF-Datei. Der Inhalt selbst läuft bewusst
ohne tägliche Sicherung (groß, austauschbar durch erneutes Hochladen) – wie bei den Dateien des Skripte-Diensts."""
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_bytes
from app.application.ports import DateiSpeicher


class FileSystemDateiSpeicher(DateiSpeicher):
    def __init__(self, pfad: Path):
        self.pfad = Path(pfad)

    def speichere(self, inhalt: bytes) -> None:
        atomic_write_bytes(self.pfad, inhalt)

    def lies(self) -> bytes | None:
        return self.pfad.read_bytes() if self.pfad.exists() else None
