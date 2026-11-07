"""Anwendungsfälle. Kennen nur Domäne und Ports."""
import logging

from app.application.ports import BibelVerweise, EintraegeRepository, QuellenRepository
from app.domain.bible import Stelle, find_book
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import KommentarEintrag, Quelle

log = logging.getLogger(__name__)


class KommentarService:
    def __init__(self, quellen: QuellenRepository, eintraege: EintraegeRepository, verweise: BibelVerweise):
        self.quellen = quellen
        self.eintraege = eintraege
        self.verweise = verweise

    def _verweis_anlegen_sicher(self, stelle: str, referenz: str, titel: str | None) -> str | None:
        """Best effort: ein kurz nicht erreichbarer Bibel-Dienst darf das Anlegen eines Kommentar-Eintrags
        nicht verhindern – der Eintrag selbst bleibt in jedem Fall gültig (siehe Domänen-Docstring)."""
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

    def _buch_pruefen(self, buch_kurz: str, kapitel: int, vers_von: int, vers_bis: int):
        buch = find_book(buch_kurz)
        if buch is None:
            raise InvalidInput(f"Das Bibelbuch „{buch_kurz}“ kenne ich nicht.")
        if not 1 <= kapitel <= buch.chapters:
            raise InvalidInput(f"{buch.name} hat nur {buch.chapters} Kapitel.")
        if vers_von < 1 or vers_bis < vers_von:
            raise InvalidInput("Der Versbereich ist ungültig.")
        return buch

    # --- Quellen ---

    def quellen_liste(self) -> list[Quelle]:
        return sorted(self.quellen.list(), key=lambda q: q.titel.casefold())

    def quelle(self, quelle_id: str) -> Quelle:
        quelle = self.quellen.get(quelle_id)
        if quelle is None:
            raise NotFound("Quelle nicht gefunden.")
        return quelle

    def quelle_anlegen(self, titel: str, autor: str, sprache: str, lizenz: str, quell_url: str,
                        namensnennung: str) -> Quelle:
        titel = (titel or "").strip()
        if not titel:
            raise InvalidInput("Der Titel der Quelle darf nicht leer sein.")
        quelle = Quelle(titel=titel, autor=(autor or "").strip(), sprache=(sprache or "de").strip(),
                        lizenz=(lizenz or "").strip(), quell_url=(quell_url or "").strip(),
                        namensnennung=(namensnennung or "").strip())
        self.quellen.save(quelle)
        return quelle

    def quelle_loeschen(self, quelle_id: str) -> None:
        self.quelle(quelle_id)   # wirft NotFound, falls unbekannt
        for eintrag in self.eintraege.delete_zu_quelle(quelle_id):
            self._verweis_loeschen_sicher(eintrag.verweis_id)
        self.quellen.delete(quelle_id)

    # --- Einträge ---

    def eintrag_anlegen(self, quelle_id: str, buch_kurz: str, kapitel: int, vers_von: int, vers_bis: int,
                        text: str) -> KommentarEintrag:
        self.quelle(quelle_id)
        buch = self._buch_pruefen(buch_kurz, kapitel, vers_von, vers_bis)
        text = (text or "").strip()
        if not text:
            raise InvalidInput("Der Kommentartext darf nicht leer sein.")
        stelle = Stelle(buch.index, kapitel, vers_von).format()
        verweis_id = self._verweis_anlegen_sicher(stelle, quelle_id, f"{buch.name} {kapitel}")
        eintrag = KommentarEintrag(quelle_id=quelle_id, buch_index=buch.index, kapitel=kapitel,
                                   vers_von=vers_von, vers_bis=vers_bis, text=text, verweis_id=verweis_id)
        self.eintraege.save(eintrag)
        return eintrag

    def eintrag_loeschen(self, eintrag_id: str) -> None:
        eintrag = self.eintraege.get(eintrag_id)
        if eintrag is None:
            raise NotFound("Kommentar-Eintrag nicht gefunden.")
        self._verweis_loeschen_sicher(eintrag.verweis_id)
        self.eintraege.delete(eintrag_id)

    def zu_stelle(self, buch_kurz: str, kapitel: int, vers: int) -> list[KommentarEintrag]:
        buch = find_book(buch_kurz)
        if buch is None:
            raise InvalidInput(f"Das Bibelbuch „{buch_kurz}“ kenne ich nicht.")
        return sorted(self.eintraege.zu_stelle(buch.index, kapitel, vers), key=lambda e: e.vers_von)

    def eintraege_zu_quelle(self, quelle_id: str) -> list[KommentarEintrag]:
        self.quelle(quelle_id)
        return sorted(self.eintraege.zu_quelle(quelle_id), key=lambda e: (e.buch_index, e.kapitel, e.vers_von))

    def _eintraege_aus_roh(self, quelle_id: str, eintraege_roh: list[tuple[str, int, int, int, str]]) -> list[KommentarEintrag]:
        """Baut KommentarEintrag-Objekte aus rohen (buch_kurz, kapitel, vers_von, vers_bis, text)-Tupeln und
        legt je Eintrag einen Verweis an. Ein einzelner ungültiger Eintrag (z. B. ein nicht erkanntes
        Bibelbuch beim Parsen) bricht den Import nicht ab, nur dieser eine wird übersprungen (geloggt)."""
        neue: list[KommentarEintrag] = []
        for buch_kurz, kapitel, vers_von, vers_bis, text in eintraege_roh:
            try:
                buch = self._buch_pruefen(buch_kurz, kapitel, vers_von, vers_bis)
            except InvalidInput as e:
                log.warning("Eintrag beim Import übersprungen (%s %s,%s-%s): %s",
                           buch_kurz, kapitel, vers_von, vers_bis, e)
                continue
            text = (text or "").strip()
            if not text:
                continue
            stelle = Stelle(buch.index, kapitel, vers_von).format()
            verweis_id = self._verweis_anlegen_sicher(stelle, quelle_id, None)
            neue.append(KommentarEintrag(quelle_id=quelle_id, buch_index=buch.index, kapitel=kapitel,
                                        vers_von=vers_von, vers_bis=vers_bis, text=text, verweis_id=verweis_id))
        return neue

    def import_ersetzen(self, quelle_id: str, eintraege_roh: list[tuple[str, int, int, int, str]]) -> list[KommentarEintrag]:
        """Ersetzt ALLE Einträge einer Quelle durch die übergebenen (buch_kurz, kapitel, vers_von, vers_bis,
        text) – für einen (erneuten) Import, z. B. aus einem Dächsel-Band. Alte Verweise werden zuerst
        aufgeräumt, dann neue angelegt (siehe `_eintraege_aus_roh`)."""
        self.quelle(quelle_id)
        for alt in self.eintraege.delete_zu_quelle(quelle_id):
            self._verweis_loeschen_sicher(alt.verweis_id)
        neue = self._eintraege_aus_roh(quelle_id, eintraege_roh)
        self.eintraege.save_alle(neue)
        return neue

    def import_teilweise(self, quelle_id: str, eintraege_roh: list[tuple[str, int, int, int, str]]) -> list[KommentarEintrag]:
        """Wie `import_ersetzen`, ersetzt aber nur die Bücher, die in `eintraege_roh` tatsächlich vorkommen –
        Einträge derselben Quelle zu anderen Büchern bleiben unangetastet. Für einen Import in mehreren
        Schritten (z. B. Buch für Buch, wie bei Matthew Henry über die HelloAO-API)."""
        self.quelle(quelle_id)
        betroffene_buecher = {find_book(b).index for b, *_ in eintraege_roh if find_book(b) is not None}
        for alt in self.eintraege.zu_quelle(quelle_id):
            if alt.buch_index in betroffene_buecher:
                self._verweis_loeschen_sicher(alt.verweis_id)
                self.eintraege.delete(alt.id)
        neue = self._eintraege_aus_roh(quelle_id, eintraege_roh)
        self.eintraege.save_alle(neue)
        return neue
