"""Domäne: ein Skript (Datei) gehört zu einem Fach. Der Inhalt selbst liegt nicht hier, nur die Angaben dazu."""
from dataclasses import dataclass, field
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


@dataclass
class Skript:
    subject_id: str
    dateiname: str
    content_type: str
    groesse: int
    hochgeladen_am: str
    id: str = field(default_factory=new_id)
