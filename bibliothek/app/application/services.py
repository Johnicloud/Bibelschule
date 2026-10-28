"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from app.application.ports import BildExtraktor, BuchRepository, DateiSpeicher, OcrKI, TextPdfBauer
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Buch


def _clean(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise InvalidInput("Der Titel darf nicht leer sein.")
    return text


def _clean_an(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise InvalidInput("Wer das Buch ausleiht, darf nicht leer sein.")
    return text


class BibliothekService:
    def __init__(self, repo: BuchRepository, dateien: DateiSpeicher | None = None,
                 bilder: BildExtraktor | None = None, ocr: OcrKI | None = None,
                 text_pdf_bauer: TextPdfBauer | None = None):
        self.repo = repo
        self.dateien = dateien
        self.bilder = bilder
        self.ocr = ocr
        self.text_pdf_bauer = text_pdf_bauer

    def _buch(self, buch_id: str) -> Buch:
        buch = self.repo.get(buch_id)
        if buch is None:
            raise NotFound("Buch nicht gefunden.")
        return buch

    def list_buecher(self) -> list[Buch]:
        return sorted(self.repo.list(), key=lambda b: b.titel.casefold())

    def add_buch(self, titel: str, autor: str | None = None, verlag: str | None = None,
                 jahr: int | None = None, isbn: str | None = None, standort: str | None = None,
                 notiz: str | None = None) -> Buch:
        buch = Buch(titel=_clean(titel), autor=autor or None, verlag=verlag or None, jahr=jahr or None,
                    isbn=isbn or None, standort=standort or None, notiz=notiz or None)
        self.repo.save(buch)
        return buch

    def update_buch(self, buch_id: str, titel: str, autor: str | None, verlag: str | None,
                     jahr: int | None, isbn: str | None, standort: str | None, notiz: str | None) -> Buch:
        buch = self._buch(buch_id)
        buch.titel = _clean(titel)
        buch.autor, buch.verlag, buch.jahr = autor or None, verlag or None, jahr or None
        buch.isbn, buch.standort, buch.notiz = isbn or None, standort or None, notiz or None
        self.repo.save(buch)
        return buch

    def delete_buch(self, buch_id: str) -> None:
        self._buch(buch_id)
        self.repo.delete(buch_id)
        if self.dateien is not None:
            self.dateien.loesche(buch_id)

    def ausleihen(self, buch_id: str, an: str) -> Buch:
        an = _clean_an(an)
        buch = self._buch(buch_id)
        buch.ausgeliehen_an = an
        self.repo.save(buch)
        return buch

    def zurueckgeben(self, buch_id: str) -> Buch:
        buch = self._buch(buch_id)
        buch.ausgeliehen_an = None
        self.repo.save(buch)
        return buch

    def assign(self, buch_id: str, subject_id: str) -> Buch:
        buch = self._buch(buch_id)
        if subject_id not in buch.faecher:
            buch.faecher.append(subject_id)
            self.repo.save(buch)
        return buch

    def unassign(self, buch_id: str, subject_id: str) -> Buch:
        buch = self._buch(buch_id)
        buch.faecher = [f for f in buch.faecher if f != subject_id]
        self.repo.save(buch)
        return buch

    def for_subject(self, subject_id: str) -> list[Buch]:
        return [b for b in self.list_buecher() if subject_id in b.faecher]

    # Fach-Hooks
    def discard_subject(self, subject_id: str) -> None:
        """Das Fach ist weg: die Zuordnung verschwindet, das Buch (und seine anderen Fächer) bleibt."""
        for buch in self.repo.list():
            if subject_id in buch.faecher:
                self.unassign(buch.id, subject_id)

    def subject_status(self, subject_id: str) -> dict:
        return {"count": len(self.for_subject(subject_id))}

    # Datei (gescanntes Buch) und Text-Erkennung
    def datei_hochladen(self, buch_id: str, inhalt: bytes) -> Buch:
        if self.dateien is None:
            raise InvalidInput("Datei-Ablage ist gerade nicht verfügbar.")
        if not inhalt:
            raise InvalidInput("Die Datei ist leer.")
        buch = self._buch(buch_id)
        self.dateien.speichere_original(buch_id, inhalt)
        buch.hat_datei = True
        buch.text_erkannt = False   # ein neuer Scan braucht eine neue Erkennung
        self.repo.save(buch)
        return buch

    def original_datei(self, buch_id: str) -> bytes | None:
        self._buch(buch_id)
        return self.dateien.original(buch_id) if self.dateien else None

    def text_datei(self, buch_id: str) -> bytes | None:
        self._buch(buch_id)
        return self.dateien.text_pdf(buch_id) if self.dateien else None

    def text_erkennen(self, buch_id: str) -> None:
        """Liest jede Seite der hochgeladenen Scan-PDF per KI (Ollama, Vision-Modell) und baut daraus eine
        durchsuchbare Text-PDF. Dauert bei einem ganzen Buch mehrere Minuten (ein KI-Aufruf je Seite) – für
        einen Hintergrund-Thread gedacht (siehe api.py), nicht für eine direkte Antwort."""
        if None in (self.dateien, self.bilder, self.ocr, self.text_pdf_bauer):
            return
        original = self.dateien.original(buch_id)
        if original is None:
            return
        text_je_seite = [self.ocr.seite_lesen(bild) for bild in self.bilder.seiten_bilder(original)]
        text_pdf = self.text_pdf_bauer.baue(original, text_je_seite)
        self.dateien.speichere_text(buch_id, text_pdf)
        buch = self.repo.get(buch_id)
        if buch is not None:
            buch.text_erkannt = True
            self.repo.save(buch)
