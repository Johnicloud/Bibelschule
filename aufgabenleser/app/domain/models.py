"""Domäne: ein Vorschlag für eine Aufgabe, wie Ollama ihn aus einem Aufgabenblatt herausliest.
Reine Python-Objekte, kein Speicher – der Dienst merkt sich nichts, er liest nur vor."""
from dataclasses import dataclass


@dataclass
class AufgabeVorschlag:
    titel: str
    frist: str | None = None       # JJJJ-MM-TT, wie im Aufgabenblatt
    gewichtung: float | None = None   # anteilige Bewertung in Prozent
