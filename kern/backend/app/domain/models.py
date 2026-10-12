"""Domäne des Kerns: ein Fach. Die Fach-ID ist das Einzige, was alle Dienste teilen."""
from dataclasses import dataclass, field
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


@dataclass
class Subject:
    name: str
    id: str = field(default_factory=new_id)
