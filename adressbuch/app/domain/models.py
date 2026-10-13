"""Domäne: ein Dozent, der beliebig vielen Fächern zugeordnet sein kann (faecher = Fach-IDs)."""
from dataclasses import dataclass, field
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


@dataclass
class Dozent:
    name: str
    email: str | None = None
    telefon: str | None = None
    notiz: str | None = None
    faecher: list[str] = field(default_factory=list)
    id: str = field(default_factory=new_id)
