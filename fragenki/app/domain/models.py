"""Domäne: ein Vorschlag für eine Verständnisfrage zu einem Bibelkapitel, wie Ollama ihn liefert.
Reine Python-Objekte, kein Speicher – der Dienst merkt sich nichts, er schlägt nur vor.
Nur die Frage selbst (siehe Entscheidungen/Vorgehen: die KI liefert sicher nur die Frage, keine
zuverlässige Antwort dazu) – eine Antwort trägt der Nutzer beim Übernehmen als Karteikarte selbst ein."""
from dataclasses import dataclass


@dataclass
class FrageVorschlag:
    frage: str
