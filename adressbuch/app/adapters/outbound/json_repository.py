"""Ausgehender Adapter: speichert alles in einer JSON-Datei (atomar, mit täglicher Sicherung).

Wichtig für die Daten: neue Felder immer mit .get(..., Standardwert) lesen, alte Felder nie umbenennen oder
löschen, ohne die Datei zu migrieren. So bleiben vorhandene Daten beim Erweitern des Dienstes erhalten."""
import json
import threading
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.application.ports import DozentRepository
from app.domain.models import Dozent


class JsonDozentRepository(DozentRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Dozent]:
        if not self.path.exists():
            return {}
        return {d["id"]: Dozent(id=d["id"], name=d["name"], email=d.get("email"), telefon=d.get("telefon"),
                                 adresse=d.get("adresse"), notiz=d.get("notiz"), faecher=d.get("faecher", []))
                for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, dozenten: dict[str, Dozent]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps(
            [{"id": d.id, "name": d.name, "email": d.email, "telefon": d.telefon, "adresse": d.adresse,
              "notiz": d.notiz, "faecher": d.faecher} for d in dozenten.values()],
            ensure_ascii=False, indent=2))

    def list(self) -> list[Dozent]:
        with self._lock:
            return list(self._read().values())

    def get(self, dozent_id: str) -> Dozent | None:
        with self._lock:
            return self._read().get(dozent_id)

    def save(self, dozent: Dozent) -> None:
        with self._lock:
            dozenten = self._read()
            dozenten[dozent.id] = dozent
            self._write(dozenten)

    def delete(self, dozent_id: str) -> None:
        with self._lock:
            dozenten = self._read()
            dozenten.pop(dozent_id, None)
            self._write(dozenten)
