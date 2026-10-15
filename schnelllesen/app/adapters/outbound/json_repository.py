"""Ausgehender Adapter: speichert alles in einer JSON-Datei (atomar, mit täglicher Sicherung).

Wichtig für die Daten: neue Felder immer mit .get(..., Standardwert) lesen, alte Felder nie umbenennen oder
löschen, ohne die Datei zu migrieren. So bleiben vorhandene Daten beim Erweitern des Dienstes erhalten."""
import json
import threading
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.application.ports import EinheitRepository
from app.domain.models import Durchgang, Einheit


def _durchgang_aus_dict(d: dict) -> Durchgang:
    return Durchgang(runde=d["runde"], sekunden=d["sekunden"], ziel_sekunden=d["ziel_sekunden"])


def _einheit_aus_dict(d: dict) -> Einheit:
    return Einheit(id=d["id"], buch=d["buch"], buch_name=d["buch_name"], kapitel=d["kapitel"],
                   text=d["text"], wortanzahl=d["wortanzahl"], erstellt=d["erstellt"],
                   durchgaenge=[_durchgang_aus_dict(x) for x in d.get("durchgaenge", [])])


def _einheit_zu_dict(e: Einheit) -> dict:
    return {"id": e.id, "buch": e.buch, "buch_name": e.buch_name, "kapitel": e.kapitel, "text": e.text,
            "wortanzahl": e.wortanzahl, "erstellt": e.erstellt,
            "durchgaenge": [{"runde": d.runde, "sekunden": d.sekunden, "ziel_sekunden": d.ziel_sekunden}
                            for d in e.durchgaenge]}


class JsonEinheitRepository(EinheitRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Einheit]:
        if not self.path.exists():
            return {}
        return {d["id"]: _einheit_aus_dict(d) for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, einheiten: dict[str, Einheit]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps(
            [_einheit_zu_dict(e) for e in einheiten.values()], ensure_ascii=False, indent=2))

    def list(self) -> list[Einheit]:
        with self._lock:
            return sorted(self._read().values(), key=lambda e: e.erstellt, reverse=True)

    def get(self, einheit_id: str) -> Einheit | None:
        with self._lock:
            return self._read().get(einheit_id)

    def save(self, einheit: Einheit) -> None:
        with self._lock:
            einheiten = self._read()
            einheiten[einheit.id] = einheit
            self._write(einheiten)

    def delete(self, einheit_id: str) -> None:
        with self._lock:
            einheiten = self._read()
            einheiten.pop(einheit_id, None)
            self._write(einheiten)
