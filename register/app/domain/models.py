"""Domäne: Register der Namen und Orte mit ihren Bibelstellen. Reine Python-Objekte."""
from dataclasses import dataclass, field
from uuid import uuid4

from app.domain.bible import BibleRef, name_sort_key

KINDS = ("person", "place")   # Namen und Orte


def new_id() -> str:
    return uuid4().hex


@dataclass
class RegisterEntry:
    """Ein Name oder Ort eines Fachs mit allen Bibelstellen, in denen er vorkommt."""
    subject_id: str
    kind: str
    name: str
    refs: list[BibleRef] = field(default_factory=list)
    id: str = field(default_factory=new_id)

    @property
    def name_key(self) -> str:
        return name_sort_key(self.name)

    def add_refs(self, refs: list[BibleRef]) -> int:
        """Fügt neue Stellen hinzu (ohne Doppelte), hält sie in Bibelreihenfolge. Gibt die Zahl neuer Stellen zurück."""
        new = [r for r in dict.fromkeys(refs) if r not in self.refs]
        self.refs = sorted(self.refs + new, key=lambda r: r.sort_key)
        return len(new)
