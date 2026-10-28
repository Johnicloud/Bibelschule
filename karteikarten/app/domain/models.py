"""Domäne: reine Python-Objekte, keine Abhängigkeit zu Framework oder Speicher."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import uuid4

# Leitner-System: Wartezeit in Tagen je Stufe (Box)
INTERVALS_DAYS = [0, 1, 2, 4, 8, 16]

# Kartentypen: Umdrehen, Multiple Choice (4 Antworten), Richtig/Falsch
KINDS = ("classic", "choice", "truefalse")
TRUE_FALSE = ["Richtig", "Falsch"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid4().hex


@dataclass
class Card:
    front: str
    back: str
    kind: str = "classic"
    options: list[str] = field(default_factory=list)
    correct_index: int | None = None
    id: str = field(default_factory=new_id)
    set_name: str = ""          # optional: Name eines Sets (z. B. aus einer Datei übernommen), leer = keins
    box: int = 0
    due: datetime = field(default_factory=utcnow)

    def is_due(self, at: datetime | None = None) -> bool:
        return self.due <= (at or utcnow())

    def review(self, correct: bool, at: datetime | None = None) -> None:
        at = at or utcnow()
        self.box = min(self.box + 1, len(INTERVALS_DAYS) - 1) if correct else 0
        self.due = at + timedelta(days=INTERVALS_DAYS[self.box])


@dataclass
class Deck:
    """Ein Fach. Aggregat: enthält seine Karteikarten."""
    name: str
    id: str = field(default_factory=new_id)
    cards: list[Card] = field(default_factory=list)
    sets: list[str] = field(default_factory=list)    # angelegte Sets (auch leere); Sets, die nur auf Karten stehen, kommen dazu

    def set_namen(self) -> list[str]:
        namen = list(self.sets)
        for c in self.cards:
            if c.set_name and c.set_name not in namen:
                namen.append(c.set_name)
        return namen

    def finde_set(self, name: str) -> str | None:
        """Der vorhandene Name zu einer Eingabe (Groß/Klein egal), sonst None."""
        wunsch = (name or "").strip().casefold()
        return next((n for n in self.set_namen() if n.casefold() == wunsch), None) if wunsch else None

    def get_card(self, card_id: str) -> Card | None:
        return next((c for c in self.cards if c.id == card_id), None)

    def due_cards(self, at: datetime | None = None) -> list[Card]:
        return [c for c in self.cards if c.is_due(at)]
