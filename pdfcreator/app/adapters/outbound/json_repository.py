"""Ausgehender Adapter: Angaben zu den Vorlagen in einer JSON-Datei (atomar, mit täglicher Sicherung).
Der Dateiinhalt selbst liegt in file_repository.py."""
from __future__ import annotations

import json
import threading
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.application.ports import VorlageRepository
from app.domain.models import Feld, Vorlage


def _feld_in(d: dict) -> Feld:
    return Feld(schluessel=d["schluessel"], seite=d.get("seite", 0), x=d["x"], y=d["y"], groesse=d.get("groesse", 10.5))


def _feld_out(f: Feld) -> dict:
    return {"schluessel": f.schluessel, "seite": f.seite, "x": f.x, "y": f.y, "groesse": f.groesse}


class JsonVorlageRepository(VorlageRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Vorlage]:
        if not self.path.exists():
            return {}
        return {d["id"]: Vorlage(id=d["id"], name=d["name"], dateiname=d["dateiname"],
                                  felder=[_feld_in(f) for f in d.get("felder", [])],
                                  ki_vorschlag=d.get("ki_vorschlag"))
                for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, vorlagen: dict[str, Vorlage]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps(
            [{"id": v.id, "name": v.name, "dateiname": v.dateiname, "felder": [_feld_out(f) for f in v.felder],
              "ki_vorschlag": v.ki_vorschlag} for v in vorlagen.values()],
            ensure_ascii=False, indent=2))

    def list(self) -> list[Vorlage]:
        with self._lock:
            return list(self._read().values())

    def get(self, vorlage_id: str) -> Vorlage | None:
        with self._lock:
            return self._read().get(vorlage_id)

    def save(self, vorlage: Vorlage) -> None:
        with self._lock:
            vorlagen = self._read()
            vorlagen[vorlage.id] = vorlage
            self._write(vorlagen)

    def delete(self, vorlage_id: str) -> None:
        with self._lock:
            vorlagen = self._read()
            vorlagen.pop(vorlage_id, None)
            self._write(vorlagen)
