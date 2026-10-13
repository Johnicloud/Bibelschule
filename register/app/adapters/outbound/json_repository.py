"""Ausgehender Adapter: speichert das Register in einer JSON-Datei."""
import json
import threading
from pathlib import Path

from app.application.ports import RegisterRepository
from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.domain.bible import BibleRef
from app.domain.models import RegisterEntry


def _to_dict(e: RegisterEntry) -> dict:
    return {"id": e.id, "subject_id": e.subject_id, "kind": e.kind, "name": e.name,
            "refs": [{"book": r.book, "chapter": r.chapter, "verse": r.verse,
                      "chapter_end": r.chapter_end, "verse_end": r.verse_end} for r in e.refs]}


def _from_dict(d: dict) -> RegisterEntry:
    return RegisterEntry(
        id=d["id"], subject_id=d["subject_id"], kind=d["kind"], name=d["name"],
        refs=[BibleRef(r["book"], r["chapter"], r["verse"], r["chapter_end"], r["verse_end"])
              for r in d.get("refs", [])])


class JsonRegisterRepository(RegisterRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, RegisterEntry]:
        if not self.path.exists():
            return {}
        return {d["id"]: _from_dict(d) for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, entries: dict[str, RegisterEntry]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps([_to_dict(e) for e in entries.values()], ensure_ascii=False, indent=2))

    def list(self, subject_id: str | None = None) -> list[RegisterEntry]:
        with self._lock:
            return [e for e in self._read().values() if subject_id is None or e.subject_id == subject_id]

    def get(self, entry_id: str) -> RegisterEntry | None:
        with self._lock:
            return self._read().get(entry_id)

    def save(self, entry: RegisterEntry) -> None:
        with self._lock:
            entries = self._read()
            entries[entry.id] = entry
            self._write(entries)

    def delete(self, entry_id: str) -> None:
        with self._lock:
            entries = self._read()
            entries.pop(entry_id, None)
            self._write(entries)

    def delete_subject(self, subject_id: str) -> None:
        with self._lock:
            self._write({i: e for i, e in self._read().items() if e.subject_id != subject_id})
