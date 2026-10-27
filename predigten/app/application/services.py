"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from app.application.ports import BibelVerweise, DateiSpeicher, PredigtRepository
from app.domain.bible import Stelle, parse_ref
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Predigt


def _clean(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise InvalidInput("Der Titel darf nicht leer sein.")
    return text


def _normalize_stellen(stellen_roh: list[str] | None) -> list[str]:
    """Liest frei eingegebene Bibelstellen (z. B. "Joh 3,16" oder nur "Ps 23") und macht daraus die kanonische
    Adresse. Eine Stelle ohne genannten Vers (reine Kapitelangabe) zeigt auf deren ersten Vers – ein Verweis
    braucht immer genau eine Stelle (siehe Entscheidungen: Bibel als Grundlage), eine Predigt über ein ganzes
    Kapitel verweist damit zumindest auf dessen Anfang. Mehrfachnennungen bleiben einmal, in Eingabereihenfolge."""
    ergebnis: list[str] = []
    for roh in stellen_roh or []:
        roh = (roh or "").strip()
        if not roh:
            continue
        ref = parse_ref(roh)
        stelle = Stelle(ref.book, ref.chapter, ref.verse or 1).format()
        if stelle not in ergebnis:
            ergebnis.append(stelle)
    return ergebnis


class PredigtenService:
    def __init__(self, repo: PredigtRepository, dateien: DateiSpeicher | None = None,
                 verweise: BibelVerweise | None = None):
        self.repo = repo
        self.dateien = dateien
        self.verweise = verweise

    def _predigt(self, predigt_id: str) -> Predigt:
        predigt = self.repo.get(predigt_id)
        if predigt is None:
            raise NotFound("Predigt nicht gefunden.")
        return predigt

    def list_predigten(self) -> list[Predigt]:
        return sorted(self.repo.list(), key=lambda p: p.datum or "", reverse=True)

    def _verweise_anlegen(self, referenz: str, stellen: list[str]) -> dict[str, str]:
        if self.verweise is None:
            return {}
        ids: dict[str, str] = {}
        for stelle in stellen:
            verweis_id = self.verweise.anlegen(stelle, referenz)
            if verweis_id:
                ids[stelle] = verweis_id
        return ids

    def _verweise_entfernen(self, verweis_ids: dict[str, str]) -> None:
        if self.verweise is None:
            return
        for verweis_id in verweis_ids.values():
            self.verweise.loeschen(verweis_id)

    def add_predigt(self, titel: str, datum: str | None = None, prediger: str | None = None,
                     notiz: str | None = None, stellen: list[str] | None = None) -> Predigt:
        predigt = Predigt(titel=_clean(titel), datum=datum or None, prediger=prediger or None,
                          notiz=notiz or None, stellen=_normalize_stellen(stellen))
        predigt.verweis_ids = self._verweise_anlegen(predigt.id, predigt.stellen)
        self.repo.save(predigt)
        return predigt

    def update_predigt(self, predigt_id: str, titel: str, datum: str | None, prediger: str | None,
                        notiz: str | None, stellen: list[str] | None) -> Predigt:
        predigt = self._predigt(predigt_id)
        neue_stellen = _normalize_stellen(stellen)
        entfernt = [s for s in predigt.stellen if s not in neue_stellen]
        hinzugekommen = [s for s in neue_stellen if s not in predigt.stellen]

        self._verweise_entfernen({s: predigt.verweis_ids[s] for s in entfernt if s in predigt.verweis_ids})
        for s in entfernt:
            predigt.verweis_ids.pop(s, None)
        predigt.verweis_ids.update(self._verweise_anlegen(predigt.id, hinzugekommen))

        predigt.titel = _clean(titel)
        predigt.datum, predigt.prediger, predigt.notiz = datum or None, prediger or None, notiz or None
        predigt.stellen = neue_stellen
        self.repo.save(predigt)
        return predigt

    def delete_predigt(self, predigt_id: str) -> None:
        predigt = self._predigt(predigt_id)
        self._verweise_entfernen(predigt.verweis_ids)
        self.repo.delete(predigt_id)
        if self.dateien is not None:
            self.dateien.loesche(predigt_id)

    # Fach-Hooks: der Dienst ist fachübergreifend, eine Predigt gehört zu keinem Fach.
    def discard_subject(self, subject_id: str) -> None:
        pass

    def subject_status(self, subject_id: str) -> dict:
        return {}

    # Datei (z. B. die gehaltene Predigt als PDF)
    def datei_hochladen(self, predigt_id: str, inhalt: bytes) -> Predigt:
        if self.dateien is None:
            raise InvalidInput("Datei-Ablage ist gerade nicht verfügbar.")
        if not inhalt:
            raise InvalidInput("Die Datei ist leer.")
        predigt = self._predigt(predigt_id)
        self.dateien.speichere(predigt_id, inhalt)
        predigt.hat_datei = True
        self.repo.save(predigt)
        return predigt

    def datei(self, predigt_id: str) -> bytes | None:
        self._predigt(predigt_id)
        return self.dateien.lies(predigt_id) if self.dateien else None
