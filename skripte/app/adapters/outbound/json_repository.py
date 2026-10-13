"""Ausgehender Adapter: Angaben zu den Skripten in einer JSON-Datei (atomar, mit täglicher Sicherung).
Der Dateiinhalt selbst liegt in file_repository.py."""
from __future__ import annotations

import json
import threading
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.application.ports import SkriptRepository
from app.domain.models import Skript


class JsonSkriptRepository(SkriptRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Skript]:
        if not self.path.exists():
            return {}
        return {d["id"]: Skript(id=d["id"], subject_id=d["subject_id"], dateiname=d["dateiname"],
                                 content_type=d.get("content_type", "application/octet-stream"),
                                 groesse=d.get("groesse", 0), hochgeladen_am=d.get("hochgeladen_am", ""))
                for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, skripte: dict[str, Skript]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps(
            [{"id": s.id, "subject_id": s.subject_id, "dateiname": s.dateiname, "content_type": s.content_type,
              "groesse": s.groesse, "hochgeladen_am": s.hochgeladen_am} for s in skripte.values()],
            ensure_ascii=False, indent=2))

    def list(self, subject_id: str | None = None) -> list[Skript]:
        with self._lock:
            return [s for s in self._read().values() if subject_id is None or s.subject_id == subject_id]

    def get(self, skript_id: str) -> Skript | None:
        with self._lock:
            return self._read().get(skript_id)

    def save(self, skript: Skript) -> None:
        with self._lock:
            skripte = self._read()
            skripte[skript.id] = skript
            self._write(skripte)

    def delete(self, skript_id: str) -> None:
        with self._lock:
            skripte = self._read()
            skripte.pop(skript_id, None)
            self._write(skripte)

    def delete_subject(self, subject_id: str) -> list[Skript]:
        with self._lock:
            skripte = self._read()
            weg = [s for s in skripte.values() if s.subject_id == subject_id]
            self._write({k: s for k, s in skripte.items() if s.subject_id != subject_id})
            return weg
