"""Domäne: reine Python-Objekte, kein Framework, kein Speicher.
Beispiel der Vorlage: ein Eintrag gehört zu einem Fach (subject_id). Ersetze das durch deine eigene Fachlogik."""
from dataclasses import dataclass, field
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


@dataclass
class Item:
    subject_id: str
    text: str
    id: str = field(default_factory=new_id)
