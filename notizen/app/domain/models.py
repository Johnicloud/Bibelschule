"""Domäne: ein Kommentar ist ein eigener Gedanke zu einer Bibelstelle (kanonische Adresse wie
„Joh.3.16“, siehe Bibel-Dienst, domain/bible.py). Kein Fach-Bezug – ein Kommentar hängt an der Stelle,
nicht an einem bestimmten Lernweg (siehe Projektnotizen, Arbeitspaket A)."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Kommentar:
    """`stelle` ist die kanonische Adresse (`Stelle.format()` des Bibel-Diensts, z. B. „Joh.3.16“).
    `verweis_id` ist die ID des beim Bibel-Dienst angelegten Verweises (`art="kommentar"`) – None, wenn
    der Bibel-Dienst beim Anlegen nicht erreichbar war (siehe HttpBibelVerweise/NullBibelVerweise)."""
    stelle: str
    text: str
    erstellt: datetime = field(default_factory=utcnow)
    verweis_id: str | None = None
    id: str = field(default_factory=new_id)
