"""Ausgehender Adapter: speichert die Fächer in einer JSON-Datei."""
import json
import threading
from pathlib import Path

from app.application.ports import SubjectRepository
from app.domain.models import Subject


class JsonSubjectRepository(SubjectRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Subject]:
        if not self.path.exists():
            return {}
        return {d["id"]: Subject(id=d["id"], name=d["name"]) for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, subjects: dict[str, Subject]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([{"id": s.id, "name": s.name} for s in subjects.values()],
                                        ensure_ascii=False, indent=2), "utf-8")

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
