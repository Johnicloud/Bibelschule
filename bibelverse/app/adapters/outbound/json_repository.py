"""Ausgehender Adapter: speichert alles in einer JSON-Datei (atomar, mit täglicher Sicherung)."""
import json
import threading
from datetime import datetime
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.application.ports import VersRepository
from app.domain.models import Vers


class JsonVersRepository(VersRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Vers]:
        if not self.path.exists():
            return {}
        return {d["id"]: Vers(id=d["id"], referenz=d["referenz"], text=d["text"], subject_id=d.get("subject_id"),
                               box=d.get("box", 0), due=datetime.fromisoformat(d["due"]))
                for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, verse: dict[str, Vers]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps(
            [{"id": v.id, "referenz": v.referenz, "text": v.text, "subject_id": v.subject_id,
              "box": v.box, "due": v.due.isoformat()} for v in verse.values()],
            ensure_ascii=False, indent=2))

    def list(self) -> list[Vers]:
        with self._lock:
            return list(self._read().values())

    def get(self, vers_id: str) -> Vers | None:
        with self._lock:
            return self._read().get(vers_id)

    def save(self, vers: Vers) -> None:
        with self._lock:
            verse = self._read()
            verse[vers.id] = vers
            self._write(verse)

    def delete(self, vers_id: str) -> None:
        with self._lock:
            verse = self._read()
            verse.pop(vers_id, None)
            self._write(verse)

    def delete_subject(self, subject_id: str) -> None:
        with self._lock:
            self._write({k: v for k, v in self._read().items() if v.subject_id != subject_id})
