"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from app.application.ports import VersRepository
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Vers

_UNVERAENDERT = object()   # Zuordnung beim Bearbeiten weglassen = Fach/allgemein bleibt, wie es war


def _clean(text: str, feld: str) -> str:
    text = (text or "").strip()
    if not text:
        raise InvalidInput(f"{feld} darf nicht leer sein.")
    return text


class VersService:
    def __init__(self, repo: VersRepository):
        self.repo = repo

    def _vers(self, vers_id: str) -> Vers:
        vers = self.repo.get(vers_id)
        if vers is None:
            raise NotFound("Vers nicht gefunden.")
        return vers

    def add_vers(self, referenz: str, text: str, subject_id: str | None = None) -> Vers:
        vers = Vers(referenz=_clean(referenz, "Die Bibelstelle"), text=_clean(text, "Der Text"), subject_id=subject_id)
        self.repo.save(vers)
        return vers

    def list_verse(self, subject_id: str | None = None, allgemein: bool = False) -> list[Vers]:
        if allgemein:
            verse = [v for v in self.repo.list() if v.subject_id is None]
        elif subject_id is not None:
            verse = [v for v in self.repo.list() if v.subject_id == subject_id]
        else:
            verse = self.repo.list()
        return sorted(verse, key=lambda v: v.referenz.casefold())

    def due_verse(self, subject_id: str) -> list[Vers]:
        """Fällige Verse zum Lernen: die eigenen des Fachs zusammen mit den allgemeinen."""
        pool = [v for v in self.repo.list() if v.subject_id == subject_id or v.subject_id is None]
        return sorted((v for v in pool if v.is_due()), key=lambda v: v.due)

    def update_vers(self, vers_id: str, referenz: str, text: str, subject_id=_UNVERAENDERT) -> Vers:
        """Ändert Bibelstelle/Text (und wahlweise die Zuordnung zu Fach/allgemein), lässt Lernfortschritt
        (Stufe, Fälligkeit) unangetastet – Bearbeiten ist kein Lernerfolg."""
        vers = self._vers(vers_id)
        vers.referenz = _clean(referenz, "Die Bibelstelle")
        vers.text = _clean(text, "Der Text")
        if subject_id is not _UNVERAENDERT:
            vers.subject_id = subject_id
        self.repo.save(vers)
        return vers

    def review(self, vers_id: str, correct: bool) -> Vers:
        vers = self._vers(vers_id)
        vers.review(correct)
        self.repo.save(vers)
        return vers

    def delete(self, vers_id: str) -> None:
        self._vers(vers_id)
        self.repo.delete(vers_id)

    # Fach-Hooks
    def discard_subject(self, subject_id: str) -> None:
        self.repo.delete_subject(subject_id)

    def subject_status(self, subject_id: str) -> dict:
        eigene = [v for v in self.repo.list() if v.subject_id == subject_id]
        mastered = sum(1 for v in eigene if v.box >= 4)
        progress = int(mastered / len(eigene) * 100 + 0.5) if eigene else None
        return {"count": len(eigene), "faellig": sum(1 for v in eigene if v.is_due()), "progress": progress}
