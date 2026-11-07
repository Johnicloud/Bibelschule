"""Domäne: ein Buch im eigenen Bestand, das beliebig vielen Fächern zugeordnet sein kann (faecher = Fach-IDs) –
wie Dozenten im Adressbuch-Dienst, dasselbe Muster."""
from dataclasses import dataclass, field
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


@dataclass
class Buch:
    """`ausgeliehen_an` ist gesetzt, wenn das Buch gerade verliehen ist (Name/Kurztext, wer es hat) –
    None heißt verfügbar. `standort` ist frei (z. B. „Regal 3“ oder „Büro“).
    `hat_datei`/`text_erkannt` spiegeln nur an, ob eine PDF-Datei bzw. eine daraus erkannte Text-PDF
    hinterlegt ist (siehe ocr.py) – der Inhalt selbst liegt in der DateiSpeicher, nicht hier."""
    titel: str
    autor: str | None = None
    verlag: str | None = None
    jahr: int | None = None
    isbn: str | None = None
    standort: str | None = None
    notiz: str | None = None
    ausgeliehen_an: str | None = None
    hat_datei: bool = False
    text_erkannt: bool = False
    faecher: list[str] = field(default_factory=list)
    id: str = field(default_factory=new_id)
