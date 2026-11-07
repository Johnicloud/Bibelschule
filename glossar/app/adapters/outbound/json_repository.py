"""Ausgehender Adapter: speichert alles in einer JSON-Datei (atomar, mit täglicher Sicherung).

Wichtig für die Daten: neue Felder immer mit .get(..., Standardwert) lesen, alte Felder nie umbenennen oder
löschen, ohne die Datei zu migrieren. So bleiben vorhandene Daten beim Erweitern des Dienstes erhalten."""
import json
import threading
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.application.ports import GlossarRepository
from app.domain.models import GlossarEintrag, Stellenverweis


def _to_dict(e: GlossarEintrag) -> dict:
    return {"id": e.id, "wort": e.wort, "transliteration": e.transliteration, "erklaerung": e.erklaerung,
            "stellen": [{"stelle": s.stelle, "verweis_id": s.verweis_id} for s in e.stellen]}


def _from_dict(d: dict) -> GlossarEintrag:
    return GlossarEintrag(
        id=d["id"], wort=d["wort"], transliteration=d.get("transliteration", ""), erklaerung=d.get("erklaerung", ""),
        stellen=[Stellenverweis(s["stelle"], s.get("verweis_id")) for s in d.get("stellen", [])])


class JsonGlossarRepository(GlossarRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, GlossarEintrag]:
        if not self.path.exists():
            return {}
        return {d["id"]: _from_dict(d) for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, eintraege: dict[str, GlossarEintrag]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps([_to_dict(e) for e in eintraege.values()], ensure_ascii=False, indent=2))

    def list(self) -> list[GlossarEintrag]:
        with self._lock:
            return list(self._read().values())

    def get(self, eintrag_id: str) -> GlossarEintrag | None:
        with self._lock:
            return self._read().get(eintrag_id)

    def save(self, eintrag: GlossarEintrag) -> None:
        with self._lock:
            eintraege = self._read()
            eintraege[eintrag.id] = eintrag
            self._write(eintraege)

    def delete(self, eintrag_id: str) -> None:
        with self._lock:
            eintraege = self._read()
            eintraege.pop(eintrag_id, None)
            self._write(eintraege)
