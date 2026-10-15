"""Ausgehender Adapter: speichert alles in einer JSON-Datei (atomar, mit täglicher Sicherung).

Wichtig für die Daten: neue Felder immer mit .get(..., Standardwert) lesen, alte Felder nie umbenennen oder
löschen, ohne die Datei zu migrieren. So bleiben vorhandene Daten beim Erweitern des Dienstes erhalten."""
import json
import threading
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.application.ports import BuchRepository
from app.domain.models import Buch


class JsonBuchRepository(BuchRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Buch]:
        if not self.path.exists():
            return {}
        return {d["id"]: Buch(id=d["id"], titel=d["titel"], autor=d.get("autor"), verlag=d.get("verlag"),
                              jahr=d.get("jahr"), isbn=d.get("isbn"), standort=d.get("standort"),
                              notiz=d.get("notiz"), ausgeliehen_an=d.get("ausgeliehen_an"),
                              hat_datei=d.get("hat_datei", False), text_erkannt=d.get("text_erkannt", False),
                              faecher=d.get("faecher", []))
                for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, buecher: dict[str, Buch]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps(
            [{"id": b.id, "titel": b.titel, "autor": b.autor, "verlag": b.verlag, "jahr": b.jahr,
              "isbn": b.isbn, "standort": b.standort, "notiz": b.notiz, "ausgeliehen_an": b.ausgeliehen_an,
              "hat_datei": b.hat_datei, "text_erkannt": b.text_erkannt, "faecher": b.faecher}
             for b in buecher.values()],
            ensure_ascii=False, indent=2))

    def list(self) -> list[Buch]:
        with self._lock:
            return list(self._read().values())

    def get(self, buch_id: str) -> Buch | None:
        with self._lock:
            return self._read().get(buch_id)

    def save(self, buch: Buch) -> None:
        with self._lock:
            buecher = self._read()
            buecher[buch.id] = buch
            self._write(buecher)

    def delete(self, buch_id: str) -> None:
        with self._lock:
            buecher = self._read()
            buecher.pop(buch_id, None)
            self._write(buecher)
