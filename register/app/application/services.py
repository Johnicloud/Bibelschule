"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from collections import Counter

from app.application.ports import EventPublisher, RegisterRepository
from app.domain.bible import BibleRef, parse_ref, split_refs
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Register, RegisterEntry

SORTS = ("name", "bibel")
LEGACY_REGISTERS = {"person": "Namen", "place": "Orte"}   # so hießen die zwei festen Register früher


def _clean(text: str, what: str) -> str:
    text = (text or "").strip()
    if not text:
        raise InvalidInput(f"{what} darf nicht leer sein.")
    return text


class RegisterService:
    def __init__(self, repo: RegisterRepository, events: EventPublisher | None = None):
        self.repo = repo
        self.events = events

    def _emit(self, event: str, payload: dict) -> None:
        if self.events:
            self.events.publish(event, payload)

    def _register(self, register_id: str) -> Register:
        register = self.repo.get_register(register_id)
        if register is None:
            raise NotFound("Register nicht gefunden.")
        return register

    def _check_unique(self, subject_id: str, name: str, own_id: str | None = None) -> None:
        if any(r.name.casefold() == name.casefold() and r.id != own_id for r in self.repo.list_registers(subject_id)):
            raise InvalidInput("Dieses Register gibt es in diesem Fach schon.")

    # Register
    def list_registers(self, subject_id: str) -> list[tuple[Register, int]]:
        """Alle Register eines Fachs in der Reihenfolge, in der sie angelegt wurden, mit Zahl der Einträge."""
        counts = Counter(e.register_id for e in self.repo.list(subject_id))
        return [(r, counts[r.id]) for r in self.repo.list_registers(subject_id)]

    def create_register(self, subject_id: str, name: str) -> Register:
        subject_id, name = _clean(subject_id, "Das Fach"), _clean(name, "Der Name des Registers")
        self._check_unique(subject_id, name)
        register = Register(subject_id=subject_id, name=name)
        self.repo.save_register(register)
        self._emit("register.created", {"subject_id": subject_id, "register_id": register.id, "name": name})
        return register

    def rename_register(self, register_id: str, name: str) -> Register:
        register = self._register(register_id)
        name = _clean(name, "Der Name des Registers")
        self._check_unique(register.subject_id, name, register.id)
        register.name = name
        self.repo.save_register(register)
        return register

    def delete_register(self, register_id: str) -> None:
        register = self._register(register_id)
        self.repo.delete_register(register.id)
        self._emit("register.deleted", {"subject_id": register.subject_id, "register_id": register.id})

    def register_names(self) -> dict[str, str]:
        return {r.id: r.name for r in self.repo.list_registers()}

    # Einträge
    def add_entry(self, register_id: str, name: str, refs: list[str]) -> RegisterEntry:
        """Legt einen Eintrag an. Gibt es ihn im Register schon, kommen die Stellen dazu."""
        register = self._register(register_id)
        name = _clean(name, "Der Name")
        parts = split_refs(refs)
        if not parts:
            raise InvalidInput("Gib mindestens eine Bibelstelle an.")
        parsed = [parse_ref(p) for p in parts]          # eine falsche Stelle bricht alles ab, nichts wird halb gespeichert

        probe = RegisterEntry(subject_id=register.subject_id, register_id=register.id, name=name)
        entry = next((e for e in self.repo.list(register.subject_id)
                      if e.register_id == register.id and e.name_key == probe.name_key), None)
        created = entry is None
        entry = entry or probe
        entry.add_refs(parsed)
        self.repo.save(entry)
        self._emit("register.entry_added" if created else "register.entry_updated",
                   {"subject_id": register.subject_id, "register_id": register.id,
                    "entry_id": entry.id, "name": entry.name})
        return entry

    def list_entries(self, subject_id: str | None = None, register_id: str | None = None,
                     sort: str = "name") -> list[RegisterEntry]:
        if sort not in SORTS:
            raise InvalidInput("Sortiert wird nach name oder bibel.")
        if register_id:
            register = self._register(register_id)
            entries = [e for e in self.repo.list(register.subject_id) if e.register_id == register.id]
        else:
            entries = self.repo.list(subject_id)
        if sort == "bibel":
            return sorted(entries, key=lambda e: (e.refs[0].sort_key if e.refs else (999,), e.name_key))
        return sorted(entries, key=lambda e: (e.name_key, e.name))

    def update_entry(self, entry_id: str, name: str, refs: list[str]) -> RegisterEntry:
        """Ändert Name und Bibelstellen eines Eintrags (ersetzt beides, anders als `add_entry`, das Stellen
        nur ergänzt). Name muss im Register weiterhin eindeutig sein (der Eintrag selbst zählt nicht mit)."""
        entry = self.repo.get(entry_id)
        if entry is None:
            raise NotFound("Eintrag nicht gefunden.")
        name = _clean(name, "Der Name")
        parts = split_refs(refs)
        if not parts:
            raise InvalidInput("Gib mindestens eine Bibelstelle an.")
        parsed = sorted({parse_ref(p) for p in parts}, key=lambda r: r.sort_key)

        name_key_neu = RegisterEntry(subject_id=entry.subject_id, register_id=entry.register_id,
                                      name=name).name_key
        doppelt = any(e.id != entry.id and e.register_id == entry.register_id and e.name_key == name_key_neu
                      for e in self.repo.list(entry.subject_id))
        if doppelt:
            raise InvalidInput(f"„{name}“ gibt es in diesem Register schon.")

        entry.name = name
        entry.refs = parsed
        self.repo.save(entry)
        self._emit("register.entry_updated", {"subject_id": entry.subject_id, "register_id": entry.register_id,
                                                "entry_id": entry.id, "name": entry.name})
        return entry

    def delete_entry(self, entry_id: str) -> None:
        entry = self.repo.get(entry_id)
        if entry is None:
            raise NotFound("Eintrag nicht gefunden.")
        self.repo.delete(entry_id)
        self._emit("register.entry_deleted", {"subject_id": entry.subject_id, "entry_id": entry.id})

    def by_passage(self, subject_id: str | None = None,
                   register_id: str | None = None) -> list[tuple[BibleRef, list[RegisterEntry]]]:
        """Bibelstellenregister: zu jeder Stelle (in Bibelreihenfolge) die Einträge, die dort vorkommen."""
        grouped: dict[BibleRef, list[RegisterEntry]] = {}
        for entry in self.list_entries(subject_id, register_id):
            for ref in entry.refs:
                grouped.setdefault(ref, []).append(entry)
        return sorted(grouped.items(), key=lambda kv: kv[0].sort_key)

    # Übernahme alter Daten
    def migrate_legacy(self) -> int:
        """Früher gab es nur Namen und Orte. Solche Einträge wandern in die Register „Namen“ und „Orte“
        ihres Fachs. Gefahrlos mehrfach aufrufbar. Gibt die Zahl der übernommenen Einträge zurück."""
        moved = 0
        for entry in [e for e in self.repo.list() if not e.register_id]:
            name = LEGACY_REGISTERS.get(entry.legacy_kind, "Namen")
            register = next((r for r in self.repo.list_registers(entry.subject_id)
                             if r.name.casefold() == name.casefold()), None)
            if register is None:
                register = Register(subject_id=entry.subject_id, name=name)
                self.repo.save_register(register)
            entry.register_id = register.id
            self.repo.save(entry)
            moved += 1
        return moved

    # Fach-Hooks
    def discard_subject(self, subject_id: str) -> None:
        self.repo.delete_subject(subject_id)

    def subject_status(self, subject_id: str) -> dict:
        entries = self.repo.list(subject_id)
        return {"registers": len(self.repo.list_registers(subject_id)), "entries": len(entries),
                "refs": sum(len(e.refs) for e in entries)}
