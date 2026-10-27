"""Domäne: ein Glossar-Eintrag für ein griechisches Wort mit Erklärung und Bibelstellen.

Fachübergreifend (kein `subject_id`, siehe Arbeitspaket F) – anders als die Vorlage kennt dieser Dienst keine
Fächer. Jede Bibelstelle eines Eintrags legt beim Bibel-Dienst einen Verweis an (`art="glossar"`); `verweis_id`
hält die dortige ID fest, damit beim Ändern/Löschen des Eintrags der zugehörige Verweis wieder entfernt werden
kann. Fehlt `verweis_id` (z. B. weil der Bibel-Dienst beim Anlegen kurz nicht erreichbar war), bleibt die Stelle
trotzdem gültig – der Verweis-Eintrag beim Bibel-Dienst ist nur eine Randnotiz für „was verweist hierher?“,
nicht die Grundlage für die Chip-Anzeige selbst."""
from dataclasses import dataclass, field
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


@dataclass
class Stellenverweis:
    stelle: str              # kanonische Adresse, z. B. "Joh.3.16" (siehe app.domain.bible.Stelle.format())
    verweis_id: str | None = None


@dataclass
class GlossarEintrag:
    wort: str                 # griechisches Wort
    transliteration: str
    erklaerung: str
    stellen: list[Stellenverweis] = field(default_factory=list)
    id: str = field(default_factory=new_id)

    @property
    def sort_key(self) -> str:
        return self.wort.casefold()
