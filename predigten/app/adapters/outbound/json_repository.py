"""Ausgehender Adapter: speichert alles in einer JSON-Datei (atomar, mit täglicher Sicherung).

Wichtig für die Daten: neue Felder immer mit .get(..., Standardwert) lesen, alte Felder nie umbenennen oder
löschen, ohne die Datei zu migrieren. So bleiben vorhandene Daten beim Erweitern des Dienstes erhalten."""
import json
import threading
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.application.ports import PredigtRepository
from app.domain.models import Predigt


class JsonPredigtRepository(PredigtRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Predigt]:
        if not self.path.exists():
            return {}
        return {d["id"]: Predigt(id=d["id"], titel=d["titel"], datum=d.get("datum"),
                                 prediger=d.get("prediger"), notiz=d.get("notiz"),
                                 stellen=d.get("stellen", []), verweis_ids=d.get("verweis_ids", {}),
                                 hat_datei=d.get("hat_datei", False))
                for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, predigten: dict[str, Predigt]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps(
            [{"id": p.id, "titel": p.titel, "datum": p.datum, "prediger": p.prediger, "notiz": p.notiz,
              "stellen": p.stellen, "verweis_ids": p.verweis_ids, "hat_datei": p.hat_datei}
             for p in predigten.values()],
            ensure_ascii=False, indent=2))

    def list(self) -> list[Predigt]:
        with self._lock:
            return list(self._read().values())

    def get(self, predigt_id: str) -> Predigt | None:
        with self._lock:
            return self._read().get(predigt_id)

    def save(self, predigt: Predigt) -> None:
        with self._lock:
            predigten = self._read()
            predigten[predigt.id] = predigt
            self._write(predigten)

    def delete(self, predigt_id: str) -> None:
        with self._lock:
            predigten = self._read()
            predigten.pop(predigt_id, None)
            self._write(predigten)
