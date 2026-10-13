"""Domäne des Kerns: ein Fach mit seinen Aufgaben. Die Fach-ID ist das Einzige, was alle Dienste teilen."""
from dataclasses import dataclass, field
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


@dataclass
class Aufgabe:
    """Eine Aufgabe umreißt den Umfang eines Fachs (Zeile im Aufgabenblatt der Dozentin).
    gewichtung = anteilige Bewertung in Prozent, wie im Aufgabenblatt (z. B. Klausur 50 %)."""
    titel: str
    frist: str | None = None
    gewichtung: float | None = None
    erledigt: bool = False
    id: str = field(default_factory=new_id)


@dataclass
class Subject:
    name: str
    id: str = field(default_factory=new_id)
    aufgaben: list[Aufgabe] = field(default_factory=list)
    se: float | None = None   # Studieneinheiten (alt); Credits = se * 1.5 (neues System, wird nicht gespeichert)
