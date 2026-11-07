"""Anwendungsfälle. Kennen nur Domäne und Ports."""
import logging

from app.application.ports import BibelVerweise, GlossarRepository
from app.domain.bible import Stelle, parse_ref
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import GlossarEintrag, Stellenverweis

log = logging.getLogger(__name__)


def _parse_stellen(texte: list[str]) -> list[str]:
    """Freie Eingaben wie 'Joh 3,16' zu kanonischen Adressen ('Joh.3.16'), ohne Doppelte, in Bibelreihenfolge.
    Verweise brauchen immer einen Vers (kein ganzes Kapitel, siehe Stelle)."""
    kanonisch: list[str] = []
    for text in texte:
        text = (text or "").strip()
        if not text:
            continue
        ref = parse_ref(text)
        if ref.verse is None:
            raise InvalidInput(f"Für einen Verweis fehlt der Vers („{text}“, z. B. „Joh 3,16“ statt „Joh 3“).")
        stelle = Stelle(ref.book, ref.chapter, ref.verse).format()
        if stelle not in kanonisch:
            kanonisch.append(stelle)
    return kanonisch


class GlossarService:
    def __init__(self, repo: GlossarRepository, verweise: BibelVerweise):
        self.repo = repo
        self.verweise = verweise

    def _verweis_anlegen_sicher(self, stelle: str, referenz: str, titel: str) -> str | None:
        """Best effort: ein kurz nicht erreichbarer Bibel-Dienst darf das Anlegen/Ändern eines Glossar-Eintrags
        nicht verhindern – die Stelle selbst bleibt in jedem Fall gültig (siehe Domänen-Docstring)."""
        try:
            return self.verweise.anlegen(stelle, referenz, titel)
        except Exception as e:
            log.warning("Verweis beim Bibel-Dienst nicht angelegt (%s): %s", stelle, e)
            return None

    def _verweis_loeschen_sicher(self, verweis_id: str | None) -> None:
        if not verweis_id:
            return
        try:
            self.verweise.loeschen(verweis_id)
        except Exception as e:
            log.warning("Verweis beim Bibel-Dienst nicht gelöscht (%s): %s", verweis_id, e)

    def list_entries(self) -> list[GlossarEintrag]:
        return sorted(self.repo.list(), key=lambda e: e.sort_key)

    def get(self, eintrag_id: str) -> GlossarEintrag:
        eintrag = self.repo.get(eintrag_id)
        if eintrag is None:
            raise NotFound("Glossar-Eintrag nicht gefunden.")
        return eintrag

    def create(self, wort: str, transliteration: str, erklaerung: str, stellen_text: list[str]) -> GlossarEintrag:
        wort = (wort or "").strip()
        if not wort:
            raise InvalidInput("Das griechische Wort darf nicht leer sein.")
        kanonisch = _parse_stellen(stellen_text)
        eintrag = GlossarEintrag(wort=wort, transliteration=(transliteration or "").strip(),
                                  erklaerung=(erklaerung or "").strip())
        eintrag.stellen = [Stellenverweis(s, self._verweis_anlegen_sicher(s, eintrag.id, wort)) for s in kanonisch]
        self.repo.save(eintrag)
        return eintrag

    def update(self, eintrag_id: str, wort: str, transliteration: str, erklaerung: str,
                stellen_text: list[str]) -> GlossarEintrag:
        eintrag = self.get(eintrag_id)
        wort = (wort or "").strip()
        if not wort:
            raise InvalidInput("Das griechische Wort darf nicht leer sein.")
        kanonisch = _parse_stellen(stellen_text)

        bisherige = {s.stelle: s for s in eintrag.stellen}
        neue_stellen = []
        for s in kanonisch:
            if s in bisherige:
                neue_stellen.append(bisherige.pop(s))
            else:
                neue_stellen.append(Stellenverweis(s, self._verweis_anlegen_sicher(s, eintrag.id, wort)))
        for uebrig in bisherige.values():   # nicht mehr genannte Stellen: Verweis beim Bibel-Dienst aufräumen
            self._verweis_loeschen_sicher(uebrig.verweis_id)

        eintrag.wort = wort
        eintrag.transliteration = (transliteration or "").strip()
        eintrag.erklaerung = (erklaerung or "").strip()
        eintrag.stellen = neue_stellen
        self.repo.save(eintrag)
        return eintrag

    def delete(self, eintrag_id: str) -> None:
        eintrag = self.get(eintrag_id)
        for s in eintrag.stellen:
            self._verweis_loeschen_sicher(s.verweis_id)
        self.repo.delete(eintrag_id)
