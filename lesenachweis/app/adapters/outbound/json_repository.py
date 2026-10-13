"""Ausgehender Adapter: speichert alle Lesepensen in einer JSON-Datei."""
import json
import threading
from datetime import date
from pathlib import Path

from app.application.ports import ReadingRepository
from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.domain.models import Buch, ReadingEntry, ReadingTask


def _to_dict(t: ReadingTask) -> dict:
    return {"id": t.id, "subject_id": t.subject_id, "title": t.title, "unit": t.unit,
            "total": t.total, "passes": t.passes,
            "buecher": [{"id": b.id, "title": b.title, "total": b.total} for b in t.buecher],
            "start": t.start.isoformat() if t.start else None,
            "deadline": t.deadline.isoformat() if t.deadline else None,
            "entries": [{"id": e.id, "day": e.day.isoformat(), "amount": e.amount, "note": e.note}
                        for e in t.entries]}


def _from_dict(d: dict) -> ReadingTask:
    return ReadingTask(
        id=d["id"], subject_id=d["subject_id"], title=d["title"], unit=d["unit"],
        total=d["total"], passes=d.get("passes", 1),
        buecher=[Buch(id=b["id"], title=b["title"], total=b["total"]) for b in d.get("buecher", [])],
        start=date.fromisoformat(d["start"]) if d.get("start") else None,
        deadline=date.fromisoformat(d["deadline"]) if d.get("deadline") else None,
        entries=[ReadingEntry(id=e["id"], day=date.fromisoformat(e["day"]), amount=e["amount"],
                              note=e.get("note", "")) for e in d.get("entries", [])])


class JsonReadingRepository(ReadingRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, ReadingTask]:
        if not self.path.exists():
            return {}
        return {d["id"]: _from_dict(d) for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, tasks: dict[str, ReadingTask]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps([_to_dict(t) for t in tasks.values()], ensure_ascii=False, indent=2))

    def list(self, subject_id: str | None = None) -> list[ReadingTask]:
        with self._lock:
            return [t for t in self._read().values() if subject_id is None or t.subject_id == subject_id]

    def get(self, task_id: str) -> ReadingTask | None:
        with self._lock:
            return self._read().get(task_id)

    def save(self, task: ReadingTask) -> None:
        with self._lock:
            tasks = self._read()
            tasks[task.id] = task
            self._write(tasks)

    def delete(self, task_id: str) -> None:
        with self._lock:
            tasks = self._read()
            tasks.pop(task_id, None)
            self._write(tasks)

    def delete_subject(self, subject_id: str) -> None:
        with self._lock:
            tasks = {i: t for i, t in self._read().items() if t.subject_id != subject_id}
            self._write(tasks)
