"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from app.application.ports import BibelQuelle, EinheitRepository
from app.domain.bible import find_book
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Einheit


class SchnelllesenService:
    def __init__(self, repo: EinheitRepository, bibel: BibelQuelle):
        self.repo = repo
        self.bibel = bibel

    def _text_holen(self, buch_kurz: str, kapitel: int):
        buch = find_book(buch_kurz)
        if buch is None:
            raise InvalidInput(f"Das Bibelbuch „{buch_kurz}“ kenne ich nicht.")
        if not 1 <= kapitel <= buch.chapters:
            raise InvalidInput(f"{buch.name} hat nur {buch.chapters} Kapitel.")
        text = (self.bibel.kapitel(buch.short, kapitel) or "").strip()
        if not text:
            raise NotFound(f"Für {buch.name} {kapitel} ist im Bibel-Dienst noch kein Verstext eingelesen.")
        return buch, text

    def neue_einheit(self, buch_kurz: str, kapitel: int) -> Einheit:
        buch, text = self._text_holen(buch_kurz, kapitel)
        einheit = Einheit(buch=buch.short, buch_name=buch.name, kapitel=kapitel,
                           text=text, wortanzahl=len(text.split()))
        self.repo.save(einheit)
        return einheit

    def durchgang_abschliessen(self, einheit_id: str, sekunden: float) -> Einheit:
        einheit = self.repo.get(einheit_id)
        if einheit is None:
            raise NotFound("Trainingseinheit nicht gefunden.")
        if einheit.fertig:
            raise InvalidInput("Diese Einheit hat schon alle drei Durchgänge.")
        if sekunden is None or sekunden <= 0:
            raise InvalidInput("Die gebrauchte Zeit muss größer als null sein.")
        einheit.durchgang_hinzufuegen(sekunden)
        self.repo.save(einheit)
        return einheit

    def liste(self) -> list[Einheit]:
        return self.repo.list()

    def get(self, einheit_id: str) -> Einheit:
        einheit = self.repo.get(einheit_id)
        if einheit is None:
            raise NotFound("Trainingseinheit nicht gefunden.")
        return einheit

    def loeschen(self, einheit_id: str) -> None:
        self.repo.delete(einheit_id)

    # Fach-Vertrag: fachübergreifend wie der Bibel-Dienst selbst, kein eigener Fach-Bezug.
    def subject_status(self, subject_id: str) -> dict:
        return {}
