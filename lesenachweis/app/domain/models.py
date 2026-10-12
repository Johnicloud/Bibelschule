"""Domäne: Lesepensum und Lesenachweis. Reine Python-Objekte, kein Framework, kein Speicher."""
from dataclasses import dataclass, field
from datetime import date
from uuid import uuid4

UNITS = ("Seiten", "Kapitel")


def new_id() -> str:
    return uuid4().hex


@dataclass
class ReadingEntry:
    """Ein Eintrag im Leseprotokoll: an einem Tag wurde so viel gelesen."""
    day: date
    amount: int
    note: str = ""
    id: str = field(default_factory=new_id)


@dataclass
class ReadingTask:
    """Ein Lesepensum eines Fachs (z. B. ein Buch). Aggregat: enthält sein Leseprotokoll."""
    subject_id: str
    title: str
    unit: str
    total: int            # Seiten oder Kapitel je Durchgang
    passes: int = 1       # Durchgänge, z. B. 2 = zweimal lesen
    deadline: date | None = None
    entries: list[ReadingEntry] = field(default_factory=list)
    id: str = field(default_factory=new_id)

    @property
    def target(self) -> int:
        return self.total * self.passes

    @property
    def done(self) -> int:
        return sum(e.amount for e in self.entries)

    def get_entry(self, entry_id: str) -> ReadingEntry | None:
        return next((e for e in self.entries if e.id == entry_id), None)
