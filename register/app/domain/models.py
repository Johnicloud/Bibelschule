"""Domäne: Register eines Fachs mit Einträgen und ihren Bibelstellen. Reine Python-Objekte."""
from dataclasses import dataclass, field
from uuid import uuid4

from app.domain.bible import BibleRef, name_sort_key


def new_id() -> str:
    return uuid4().hex


@dataclass
class Register:
    """Ein Register eines Fachs, z. B. „Namen“, „Orte“ oder „Völker“. Pro Fach beliebig viele."""
    subject_id: str
    name: str
    id: str = field(default_factory=new_id)


@dataclass
class RegisterEntry:
    """Ein Eintrag eines Registers mit allen Bibelstellen, in denen er vorkommt."""
    subject_id: str
    register_id: str
    name: str
    refs: list[BibleRef] = field(default_factory=list)
    id: str = field(default_factory=new_id)
    legacy_kind: str = ""   # alte Daten: "person" oder "place"; nur noch für die Übernahme in Register (JSON-Feld "kind")
    lat: float | None = None   # Koordinaten, von Hand eingetragen (keine Geocoding-API); nur sinnvoll bei Orten,
    lon: float | None = None   # aber Register sind generisch, daher nicht erzwungen – bei jedem Eintrag möglich

    @property
    def name_key(self) -> str:
        return name_sort_key(self.name)

    def add_refs(self, refs: list[BibleRef]) -> int:
        """Fügt neue Stellen hinzu (ohne Doppelte), hält sie in Bibelreihenfolge. Gibt die Zahl neuer Stellen zurück."""
        new = [r for r in dict.fromkeys(refs) if r not in self.refs]
        self.refs = sorted(self.refs + new, key=lambda r: r.sort_key)
        return len(new)
