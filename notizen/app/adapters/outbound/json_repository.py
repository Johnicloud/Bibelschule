"""Ausgehender Adapter: speichert alles in einer JSON-Datei (atomar, mit täglicher Sicherung).

Wichtig für die Daten: neue Felder immer mit .get(..., Standardwert) lesen, alte Felder nie umbenennen oder
löschen, ohne die Datei zu migrieren. So bleiben vorhandene Daten beim Erweitern des Dienstes erhalten."""
import json
import threading
from datetime import datetime
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.application.ports import KommentarRepository
from app.domain.models import Kommentar


def _aus_dict(d: dict) -> Kommentar:
    return Kommentar(id=d["id"], stelle=d["stelle"], text=d["text"],
                      erstellt=datetime.fromisoformat(d["erstellt"]), verweis_id=d.get("verweis_id"))


def _zu_dict(k: Kommentar) -> dict:
    return {"id": k.id, "stelle": k.stelle, "text": k.text, "erstellt": k.erstellt.isoformat(),
            "verweis_id": k.verweis_id}


class JsonKommentarRepository(KommentarRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Kommentar]:
        if not self.path.exists():
            return {}
        return {d["id"]: _aus_dict(d) for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, kommentare: dict[str, Kommentar]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps(
            [_zu_dict(k) for k in kommentare.values()], ensure_ascii=False, indent=2))

    def list_zu_stelle(self, stelle: str) -> list[Kommentar]:
        with self._lock:
            treffer = [k for k in self._read().values() if k.stelle == stelle]
            return sorted(treffer, key=lambda k: k.erstellt)

    def get(self, kommentar_id: str) -> Kommentar | None:
        with self._lock:
            return self._read().get(kommentar_id)

    def save(self, kommentar: Kommentar) -> None:
        with self._lock:
            kommentare = self._read()
            kommentare[kommentar.id] = kommentar
            self._write(kommentare)

    def delete(self, kommentar_id: str) -> None:
        with self._lock:
            kommentare = self._read()
            kommentare.pop(kommentar_id, None)
            self._write(kommentare)
