"""Sicheres Speichern für JSON-Dateien: atomar schreiben und täglich eine Sicherung behalten."""
import os
import shutil
import tempfile
from datetime import date
from pathlib import Path

KEEP_BACKUPS = 14


def atomic_write_text(path: Path, text: str) -> None:
    """Schreibt erst in eine Nebendatei und ersetzt dann die Datei in einem Schritt.
    So bleibt die alte Datei heil, falls das Schreiben mittendrin abbricht."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Wie atomic_write_text, nur für binäre Dateien (PDF-Vorlagen)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def daily_backup(path: Path, today: date | None = None, keep: int = KEEP_BACKUPS) -> None:
    """Kopiert die Datei vor dem ersten Schreiben des Tages nach backups/ (Stand vom Vortag) und
    behält die letzten `keep` Tage."""
    path = Path(path)
    if not path.exists():
        return
    folder = path.parent / "backups"
    target = folder / f"{path.stem}-{(today or date.today()).isoformat()}{path.suffix}"
    if target.exists():
        return
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    old = sorted(folder.glob(f"{path.stem}-*{path.suffix}"))
    for f in old[:-keep]:
        f.unlink(missing_ok=True)
