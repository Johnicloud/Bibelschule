"""Domäne: Lesepensum und Lesenachweis. Reine Python-Objekte, kein Framework, kein Speicher."""
from dataclasses import dataclass, field
from datetime import date
from uuid import uuid4

UNITS = ("Seiten", "Kapitel")


def new_id() -> str:
    return uuid4().hex


@dataclass
class ReadingEntry:
    """Ein Eintrag im Leseprotokoll: an einem Tag wurde so viel gelesen.
    `buch_id` ist gesetzt, wenn sich der Eintrag bei einem Pensum aus mehreren Büchern auf eines davon bezieht.
    `durchlauf` (1-basiert) ist bei mehreren Durchgängen (passes > 1), welcher Durchgang gemeint ist – so lässt
    sich im ersten Durchgang Seite 5 stehen und im zweiten gleichzeitig Seite 7."""
    day: date
    amount: int
    note: str = ""
    buch_id: str | None = None
    durchlauf: int = 1
    id: str = field(default_factory=new_id)


@dataclass
class Buch:
    """Eines von mehreren Büchern, die zusammen ein Lesepensum ergeben (z. B. Pflicht-Lektüre 600 Seiten
    aus drei Büchern mit je eigenem Umfang)."""
    title: str
    total: int
    id: str = field(default_factory=new_id)


@dataclass
class ReadingTask:
    """Ein Lesepensum eines Fachs (z. B. ein Buch, oder mehrere Bücher zusammen). Aggregat: enthält sein Leseprotokoll."""
    subject_id: str
    title: str
    unit: str
    total: int            # Seiten oder Kapitel je Durchgang (= Summe der Bücher, falls welche angegeben sind)
    passes: int = 1       # Durchgänge, z. B. 2 = zweimal lesen
    buecher: list[Buch] = field(default_factory=list)
    start: date | None = None
    deadline: date | None = None
    entries: list[ReadingEntry] = field(default_factory=list)
    id: str = field(default_factory=new_id)
    skript_id: str | None = None   # optional: Datei im Skripte-Dienst, die zu diesem Pensum gehört (nur die Id, der Inhalt bleibt dort)

    @property
    def target(self) -> int:
        return self.total * self.passes

    @property
    def done(self) -> int:
        return sum(e.amount for e in self.entries)

    def get_entry(self, entry_id: str) -> ReadingEntry | None:
        return next((e for e in self.entries if e.id == entry_id), None)

    def get_buch(self, buch_id: str) -> Buch | None:
        return next((b for b in self.buecher if b.id == buch_id), None)

    def buch_done(self, buch_id: str) -> int:
        return sum(e.amount for e in self.entries if e.buch_id == buch_id)

    def durchlauf_done(self, nummer: int) -> int:
        return sum(e.amount for e in self.entries if e.durchlauf == nummer)

    def aktiver_durchlauf(self) -> int:
        """Der erste noch nicht abgeschlossene Durchgang (1-basiert) – dort tragen neue Einträge standardmäßig
        ein. Sind alle Durchgänge fertig, bleibt es beim letzten."""
        for n in range(1, self.passes + 1):
            if self.durchlauf_done(n) < self.total:
                return n
        return self.passes
