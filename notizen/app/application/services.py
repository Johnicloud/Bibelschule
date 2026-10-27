"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from app.application.ports import BibelVerweise, KommentarRepository
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Kommentar

TITEL_LAENGE = 60


class NotizenService:
    def __init__(self, repo: KommentarRepository, verweise: BibelVerweise):
        self.repo = repo
        self.verweise = verweise

    def kommentar_anlegen(self, stelle: str, text: str) -> Kommentar:
        stelle = (stelle or "").strip()
        text = (text or "").strip()
        if not stelle:
            raise InvalidInput("Die Bibelstelle darf nicht leer sein.")
        if not text:
            raise InvalidInput("Der Kommentar darf nicht leer sein.")
        kommentar = Kommentar(stelle=stelle, text=text)
        # Meldet sich als Verweis beim Bibel-Dienst an, der dabei auch die Stelle selbst prüft (parse_stelle) –
        # wirft InvalidInput, wenn die Stelle nicht stimmt; None statt einer ID, wenn der Dienst nicht erreichbar
        # ist (dann bleibt der Kommentar trotzdem gespeichert, siehe BibelVerweise).
        kommentar.verweis_id = self.verweise.anlegen(stelle, kommentar.id, _titel(text))
        self.repo.save(kommentar)
        return kommentar

    def liste_zu_stelle(self, stelle: str) -> list[Kommentar]:
        stelle = (stelle or "").strip()
        if not stelle:
            raise InvalidInput("Die Bibelstelle darf nicht leer sein.")
        return self.repo.list_zu_stelle(stelle)

    def loeschen(self, kommentar_id: str) -> None:
        kommentar = self.repo.get(kommentar_id)
        if kommentar is None:
            raise NotFound("Kommentar nicht gefunden.")
        self.repo.delete(kommentar_id)
        if kommentar.verweis_id:
            self.verweise.loeschen(kommentar.verweis_id)

    # Fach-Vertrag: fachübergreifend wie der Bibel-Dienst selbst, kein eigener Fach-Bezug.
    def subject_status(self, subject_id: str) -> dict:
        return {}


def _titel(text: str) -> str:
    return text if len(text) <= TITEL_LAENGE else text[:TITEL_LAENGE - 1].rstrip() + "…"
