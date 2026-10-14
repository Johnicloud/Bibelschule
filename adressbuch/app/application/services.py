"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from app.application.ports import DozentRepository
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Dozent


def _clean(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise InvalidInput("Der Name darf nicht leer sein.")
    return text


class DozentService:
    def __init__(self, repo: DozentRepository):
        self.repo = repo

    def _dozent(self, dozent_id: str) -> Dozent:
        dozent = self.repo.get(dozent_id)
        if dozent is None:
            raise NotFound("Dozent nicht gefunden.")
        return dozent

    def list_dozenten(self) -> list[Dozent]:
        return sorted(self.repo.list(), key=lambda d: d.name.casefold())

    def add_dozent(self, name: str, email: str | None = None, telefon: str | None = None,
                    adresse: str | None = None, strasse: str | None = None, plz: str | None = None,
                    ort: str | None = None, notiz: str | None = None) -> Dozent:
        dozent = Dozent(name=_clean(name), email=email or None, telefon=telefon or None,
                         adresse=adresse or None, strasse=strasse or None, plz=plz or None,
                         ort=ort or None, notiz=notiz or None)
        self.repo.save(dozent)
        return dozent

    def update_dozent(self, dozent_id: str, name: str, email: str | None, telefon: str | None,
                       adresse: str | None, strasse: str | None, plz: str | None, ort: str | None,
                       notiz: str | None) -> Dozent:
        dozent = self._dozent(dozent_id)
        dozent.name, dozent.email, dozent.telefon = _clean(name), email or None, telefon or None
        dozent.adresse, dozent.notiz = adresse or None, notiz or None
        dozent.strasse, dozent.plz, dozent.ort = strasse or None, plz or None, ort or None
        self.repo.save(dozent)
        return dozent

    def delete_dozent(self, dozent_id: str) -> None:
        self._dozent(dozent_id)
        self.repo.delete(dozent_id)

    def assign(self, dozent_id: str, subject_id: str) -> Dozent:
        dozent = self._dozent(dozent_id)
        if subject_id not in dozent.faecher:
            dozent.faecher.append(subject_id)
            self.repo.save(dozent)
        return dozent

    def unassign(self, dozent_id: str, subject_id: str) -> Dozent:
        dozent = self._dozent(dozent_id)
        dozent.faecher = [f for f in dozent.faecher if f != subject_id]
        self.repo.save(dozent)
        return dozent

    def for_subject(self, subject_id: str) -> list[Dozent]:
        return [d for d in self.list_dozenten() if subject_id in d.faecher]

    # Fach-Hooks
    def discard_subject(self, subject_id: str) -> None:
        """Das Fach ist weg: die Zuordnung verschwindet, der Dozent (und seine anderen Fächer) bleibt."""
        for dozent in self.repo.list():
            if subject_id in dozent.faecher:
                self.unassign(dozent.id, subject_id)

    def subject_status(self, subject_id: str) -> dict:
        return {"count": len(self.for_subject(subject_id))}
