"""Domäne: eine Vorlage (PDF-Formular) mit den Stellen, an die Text geschrieben wird."""
from dataclasses import dataclass, field
from uuid import uuid4

MAX_BUECHER = 6   # so viele Zeilen hat die Tabelle im Lesenachweis-Formular


def new_id() -> str:
    return uuid4().hex


@dataclass
class Feld:
    """Eine beschreibbare Stelle auf einer Seite der Vorlage. x/y in PDF-Punkten von unten links
    (wie reportlab/pypdf sie erwarten), nicht von oben wie beim Lesen mit pdfplumber."""
    schluessel: str
    seite: int
    x: float
    y: float
    groesse: float = 10.5


@dataclass
class Vorlage:
    """Eine PDF-Vorlage. Die Datei selbst liegt nicht hier (siehe file_repository.py), nur die Angaben dazu."""
    name: str
    dateiname: str
    felder: list[Feld] = field(default_factory=list)
    ki_vorschlag: str | None = None   # Rohtext der Ollama-Antwort bei neu hochgeladenen Vorlagen, nur zur Ansicht
    id: str = field(default_factory=new_id)
