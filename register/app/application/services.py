"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from app.application.ports import EventPublisher, RegisterRepository
from app.domain.bible import BibleRef, parse_ref, split_refs
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import KINDS, RegisterEntry

SORTS = ("name", "bibel")


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

    def add_entry(self, subject_id: str, kind: str, name: str, refs: list[str]) -> RegisterEntry:
        """Legt einen Namen/Ort an. Gibt es ihn im Fach schon, kommen die Stellen dazu."""
        if kind not in KINDS:
            raise InvalidInput("Die Art ist Name (person) oder Ort (place).")
        subject_id, name = _clean(subject_id, "Das Fach"), _clean(name, "Der Name")
        parts = split_refs(refs)
        if not parts:
            raise InvalidInput("Gib mindestens eine Bibelstelle an.")
        parsed = [parse_ref(p) for p in parts]          # eine falsche Stelle bricht alles ab, nichts wird halb gespeichert

        probe = RegisterEntry(subject_id=subject_id, kind=kind, name=name)
        entry = next((e for e in self.repo.list(subject_id) if e.kind == kind and e.name_key == probe.name_key), None)
        created = entry is None
        entry = entry or probe
        entry.add_refs(parsed)
        self.repo.save(entry)
        self._emit("register.entry_added" if created else "register.entry_updated",
                   {"subject_id": subject_id, "entry_id": entry.id, "kind": kind, "name": entry.name})
        return entry

    def list_entries(self, subject_id: str | None = None, kind: str | None = None,
                     sort: str = "name") -> list[RegisterEntry]:
        if sort not in SORTS:
            raise InvalidInput("Sortiert wird nach name oder bibel.")
        entries = [e for e in self.repo.list(subject_id) if kind in (None, e.kind)]
        if sort == "bibel":
            return sorted(entries, key=lambda e: (e.refs[0].sort_key if e.refs else (999,), e.name_key))
        return sorted(entries, key=lambda e: (e.name_key, e.kind))

    def delete_entry(self, entry_id: str) -> None:
        entry = self.repo.get(entry_id)
        if entry is None:
            raise NotFound("Eintrag nicht gefunden.")
        self.repo.delete(entry_id)
        self._emit("register.entry_deleted", {"subject_id": entry.subject_id, "entry_id": entry.id})

    def by_passage(self, subject_id: str | None = None, kind: str | None = None) -> list[tuple[BibleRef, list[RegisterEntry]]]:
        """Bibelstellenregister: zu jeder Stelle (in Bibelreihenfolge) die Namen und Orte, die dort vorkommen."""
        grouped: dict[BibleRef, list[RegisterEntry]] = {}
        for entry in self.list_entries(subject_id, kind):
            for ref in entry.refs:
                grouped.setdefault(ref, []).append(entry)
        return sorted(grouped.items(), key=lambda kv: kv[0].sort_key)

    # Fach-Hooks
    def discard_subject(self, subject_id: str) -> None:
        self.repo.delete_subject(subject_id)

    def subject_status(self, subject_id: str) -> dict:
        entries = self.repo.list(subject_id)
        return {"persons": sum(1 for e in entries if e.kind == "person"),
                "places": sum(1 for e in entries if e.kind == "place"),
                "refs": sum(len(e.refs) for e in entries)}
