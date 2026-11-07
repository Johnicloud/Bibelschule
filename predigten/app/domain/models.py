"""Domäne: ein Eintrag im Predigt-/Schreibarchiv (Predigt, eigener Text, Notiz) – mit optionaler hochgeladener
Datei (wie beim Skripte-/Bibliothek-Dienst) und optionalen Bibelstellen, auf die verwiesen wird
(siehe Entscheidungen: Bibel als Grundlage, generischer Verweis-Mechanismus des Bibel-Diensts).
Fachübergreifend wie bibel/pdfcreator/aufgabenleser/schnelllesen (keine Fach-Zuordnung)."""
from dataclasses import dataclass, field
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


@dataclass
class Predigt:
    """`stellen` sind kanonische Bibelstellen-Adressen (`Stelle.format()`, z. B. "Joh.3.16"). `verweis_ids`
    hält zu jeder davon die beim Bibel-Dienst angelegte Verweis-ID fest (stelle -> Verweis-ID) – nur so lässt
    sich ein Verweis beim Bearbeiten/Löschen der Predigt dort gezielt wieder entfernen."""
    titel: str
    datum: str | None = None       # ISO-Datum (YYYY-MM-DD), optional
    prediger: str | None = None
    notiz: str | None = None
    stellen: list[str] = field(default_factory=list)
    verweis_ids: dict[str, str] = field(default_factory=dict)
    hat_datei: bool = False
    id: str = field(default_factory=new_id)
