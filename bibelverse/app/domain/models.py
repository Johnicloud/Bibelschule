"""Domäne: ein Bibelvers zum Auswendiglernen. subject_id = None heißt „allgemein“ (keinem Fach zugeordnet).
Leitner-System wie bei den Karteikarten: dieselben Stufen, dieselbe Logik."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import uuid4

INTERVALS_DAYS = [0, 1, 2, 4, 8, 16]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid4().hex


@dataclass
class Vers:
    referenz: str
    text: str
    subject_id: str | None = None
    box: int = 0
    due: datetime = field(default_factory=utcnow)
    id: str = field(default_factory=new_id)

    def is_due(self, at: datetime | None = None) -> bool:
        return self.due <= (at or utcnow())

    def review(self, correct: bool, at: datetime | None = None) -> None:
        at = at or utcnow()
        self.box = min(self.box + 1, len(INTERVALS_DAYS) - 1) if correct else 0
        self.due = at + timedelta(days=INTERVALS_DAYS[self.box])
