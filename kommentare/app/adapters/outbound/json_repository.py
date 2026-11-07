"""Ausgehende Adapter: speichern alles in JSON-Dateien (atomar, mit täglicher Sicherung).

Wichtig für die Daten: neue Felder immer mit .get(..., Standardwert) lesen, alte Felder nie umbenennen oder
löschen, ohne die Datei zu migrieren. So bleiben vorhandene Daten beim Erweitern des Dienstes erhalten."""
import json
import threading
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.application.ports import EintraegeRepository, QuellenRepository
from app.domain.models import KommentarEintrag, Quelle


def _quelle_to_dict(q: Quelle) -> dict:
    return {"id": q.id, "titel": q.titel, "autor": q.autor, "sprache": q.sprache, "lizenz": q.lizenz,
            "quell_url": q.quell_url, "namensnennung": q.namensnennung}


def _quelle_from_dict(d: dict) -> Quelle:
    return Quelle(id=d["id"], titel=d["titel"], autor=d.get("autor", ""), sprache=d.get("sprache", "de"),
                  lizenz=d.get("lizenz", ""), quell_url=d.get("quell_url", ""),
                  namensnennung=d.get("namensnennung", ""))


class JsonQuellenRepository(QuellenRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Quelle]:
        if not self.path.exists():
            return {}
        return {d["id"]: _quelle_from_dict(d) for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, quellen: dict[str, Quelle]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps([_quelle_to_dict(q) for q in quellen.values()],
                                                  ensure_ascii=False, indent=2))

    def list(self) -> list[Quelle]:
        with self._lock:
            return list(self._read().values())

    def get(self, quelle_id: str) -> Quelle | None:
        with self._lock:
            return self._read().get(quelle_id)

    def save(self, quelle: Quelle) -> None:
        with self._lock:
            quellen = self._read()
            quellen[quelle.id] = quelle
            self._write(quellen)

    def delete(self, quelle_id: str) -> None:
        with self._lock:
            quellen = self._read()
            quellen.pop(quelle_id, None)
            self._write(quellen)


def _eintrag_to_dict(e: KommentarEintrag) -> dict:
    return {"id": e.id, "quelle_id": e.quelle_id, "buch_index": e.buch_index, "kapitel": e.kapitel,
            "vers_von": e.vers_von, "vers_bis": e.vers_bis, "text": e.text, "verweis_id": e.verweis_id}


def _eintrag_from_dict(d: dict) -> KommentarEintrag:
    return KommentarEintrag(id=d["id"], quelle_id=d["quelle_id"], buch_index=d["buch_index"],
                            kapitel=d["kapitel"], vers_von=d["vers_von"], vers_bis=d["vers_bis"],
                            text=d["text"], verweis_id=d.get("verweis_id"))


class JsonEintraegeRepository(EintraegeRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, KommentarEintrag]:
        if not self.path.exists():
            return {}
        return {d["id"]: _eintrag_from_dict(d) for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, eintraege: dict[str, KommentarEintrag]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps([_eintrag_to_dict(e) for e in eintraege.values()],
                                                  ensure_ascii=False, indent=2))

    def zu_stelle(self, buch_index: int, kapitel: int, vers: int) -> list[KommentarEintrag]:
        with self._lock:
            return [e for e in self._read().values()
                    if e.buch_index == buch_index and e.kapitel == kapitel and e.deckt_ab(vers)]

    def zu_quelle(self, quelle_id: str) -> list[KommentarEintrag]:
        with self._lock:
            return [e for e in self._read().values() if e.quelle_id == quelle_id]

    def get(self, eintrag_id: str) -> KommentarEintrag | None:
        with self._lock:
            return self._read().get(eintrag_id)

    def save(self, eintrag: KommentarEintrag) -> None:
        with self._lock:
            eintraege = self._read()
            eintraege[eintrag.id] = eintrag
            self._write(eintraege)

    def save_alle(self, eintraege: list[KommentarEintrag]) -> None:
        with self._lock:
            vorhandene = self._read()
            for e in eintraege:
                vorhandene[e.id] = e
            self._write(vorhandene)

    def delete(self, eintrag_id: str) -> None:
        with self._lock:
            eintraege = self._read()
            eintraege.pop(eintrag_id, None)
            self._write(eintraege)

    def delete_zu_quelle(self, quelle_id: str) -> list[KommentarEintrag]:
        with self._lock:
            eintraege = self._read()
            betroffene = [e for e in eintraege.values() if e.quelle_id == quelle_id]
            for e in betroffene:
                eintraege.pop(e.id, None)
            self._write(eintraege)
            return betroffene
