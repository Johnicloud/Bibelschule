"""Domäne: ein Bibelkommentar-Eintrag aus einer Quelle (Kommentarwerk), für einen Versbereich eines Kapitels.

Fachübergreifend (kein `subject_id`) wie glossar/predigten. Eine `Quelle` steht für ein ganzes Kommentarwerk
mit Autor/Lizenz-/Herkunftsangabe (z. B. Dächsel, gemeinfrei) – ein `KommentarEintrag` gehört zu genau einer
Quelle und deckt einen Versbereich ab (`vers_von`..`vers_bis`, bei den meisten Werken nur ein einzelner Vers).
Der erste Vers des Bereichs legt beim Bibel-Dienst einen Verweis an (`art="kommentare"`, wie beim Glossar);
`verweis_id` hält die dortige ID fest, damit er beim Löschen/erneuten Import wieder aufgeräumt werden kann.
Fehlt `verweis_id` (Bibel-Dienst kurz nicht erreichbar), bleibt der Eintrag trotzdem gültig – der Verweis
dort ist nur eine Randnotiz für „was verweist hierher?“, nicht die Grundlage der eigentlichen Anzeige."""
from dataclasses import dataclass, field
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


@dataclass
class Quelle:
    """`sprache` z. B. "de"/"en" – die Oberfläche zeigt bei nicht-deutschen Quellen eine Sprachmarke, die App
    ist sonst konsequent deutschsprachig (siehe Projektnotizen). `namensnennung` ist der Text, den die Lizenz
    beim Zitieren verlangt (z. B. „Karl August Dächsel, Bibelwerk, gemeinfrei“)."""
    titel: str
    autor: str
    sprache: str
    lizenz: str
    quell_url: str = ""
    namensnennung: str = ""
    id: str = field(default_factory=new_id)


@dataclass
class KommentarEintrag:
    quelle_id: str
    buch_index: int
    kapitel: int
    vers_von: int
    vers_bis: int
    text: str
    verweis_id: str | None = None
    id: str = field(default_factory=new_id)

    def deckt_ab(self, vers: int) -> bool:
        return self.vers_von <= vers <= self.vers_bis
