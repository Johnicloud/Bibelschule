"""Ausgehender Adapter: speichert die Fächer in einer JSON-Datei."""
import json
import threading
from pathlib import Path

from app.application.ports import SubjectRepository
from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.domain.models import Aufgabe, Subject


def _aufgabe_in(d: dict) -> Aufgabe:
    return Aufgabe(id=d["id"], titel=d["titel"], frist=d.get("frist"),
                   gewichtung=d.get("gewichtung"), erledigt=d.get("erledigt", False))


def _aufgabe_out(a: Aufgabe) -> dict:
    return {"id": a.id, "titel": a.titel, "frist": a.frist, "gewichtung": a.gewichtung, "erledigt": a.erledigt}


class JsonSubjectRepository(SubjectRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Subject]:
        if not self.path.exists():
            return {}
        return {d["id"]: Subject(id=d["id"], name=d["name"], aufgaben=[_aufgabe_in(a) for a in d.get("aufgaben", [])],
                                  se=d.get("se"))
                for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, subjects: dict[str, Subject]) -> None:
        daily_backup(self.path)
        data = [{"id": s.id, "name": s.name, "aufgaben": [_aufgabe_out(a) for a in s.aufgaben], "se": s.se}
                for s in subjects.values()]
        atomic_write_text(self.path, json.dumps(data, ensure_ascii=False, indent=2))

    def list(self) -> list[Subject]:
        with self._lock:
            return list(self._read().values())

    def get(self, subject_id: str) -> Subject | None:
        with self._lock:
            return self._read().get(subject_id)

    def save(self, subject: Subject) -> None:
        with self._lock:
            subjects = self._read()
            subjects[subject.id] = subject
            self._write(subjects)

    def delete(self, subject_id: str) -> None:
        with self._lock:
            subjects = self._read()
            subjects.pop(subject_id, None)
            self._write(subjects)
