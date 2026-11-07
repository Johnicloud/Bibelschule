"""Ausgehender Adapter: speichert Einträge (register.json) und Register (registers.json) in JSON-Dateien."""
from __future__ import annotations  # Methoden heißen `list`; ohne das wäre `list[...]` danach verdeckt
import json
import threading
from pathlib import Path

from app.application.ports import RegisterRepository
from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.domain.bible import BibleRef
from app.domain.models import Register, RegisterEntry


def _to_dict(e: RegisterEntry) -> dict:
    return {"id": e.id, "subject_id": e.subject_id, "register_id": e.register_id, "kind": e.legacy_kind,
            "name": e.name, "lat": e.lat, "lon": e.lon,
            "refs": [{"book": r.book, "chapter": r.chapter, "verse": r.verse,
                      "chapter_end": r.chapter_end, "verse_end": r.verse_end} for r in e.refs]}


def _from_dict(d: dict) -> RegisterEntry:
    return RegisterEntry(
        id=d["id"], subject_id=d["subject_id"], register_id=d.get("register_id", ""),
        legacy_kind=d.get("kind", ""), name=d["name"], lat=d.get("lat", None), lon=d.get("lon", None),
        refs=[BibleRef(r["book"], r["chapter"], r["verse"], r["chapter_end"], r["verse_end"])
              for r in d.get("refs", [])])


class JsonRegisterRepository(RegisterRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self.registers_path = self.path.with_name("registers.json")
        self._lock = threading.Lock()

    # Einträge
    def _read(self) -> dict[str, RegisterEntry]:
        if not self.path.exists():
            return {}
        return {d["id"]: _from_dict(d) for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, entries: dict[str, RegisterEntry]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps([_to_dict(e) for e in entries.values()], ensure_ascii=False, indent=2))

    # Register
    def _read_registers(self) -> dict[str, Register]:
        if not self.registers_path.exists():
            return {}
        return {d["id"]: Register(id=d["id"], subject_id=d["subject_id"], name=d["name"])
                for d in json.loads(self.registers_path.read_text("utf-8"))}

    def _write_registers(self, registers: dict[str, Register]) -> None:
        daily_backup(self.registers_path)
        data = [{"id": r.id, "subject_id": r.subject_id, "name": r.name} for r in registers.values()]
        atomic_write_text(self.registers_path, json.dumps(data, ensure_ascii=False, indent=2))

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

    def list_registers(self, subject_id: str | None = None) -> list[Register]:
        with self._lock:
            return [r for r in self._read_registers().values() if subject_id is None or r.subject_id == subject_id]

    def get_register(self, register_id: str) -> Register | None:
        with self._lock:
            return self._read_registers().get(register_id)

    def save_register(self, register: Register) -> None:
        with self._lock:
            registers = self._read_registers()
            registers[register.id] = register
            self._write_registers(registers)

    def delete_register(self, register_id: str) -> None:
        with self._lock:
            # erst die Einträge, dann das Register: bricht es dazwischen ab, bleibt nur ein leeres Register
            self._write({i: e for i, e in self._read().items() if e.register_id != register_id})
            registers = self._read_registers()
            registers.pop(register_id, None)
            self._write_registers(registers)

    def delete_subject(self, subject_id: str) -> None:
        with self._lock:
            self._write({i: e for i, e in self._read().items() if e.subject_id != subject_id})
            self._write_registers({i: r for i, r in self._read_registers().items() if r.subject_id != subject_id})
