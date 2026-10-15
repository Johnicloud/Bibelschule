"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from datetime import date

from app.application.ports import DateiSpeicher, PdfText, SkriptRepository
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Skript

MAX_BYTES = 50 * 1024 * 1024   # 50 MB: genug für ein Skript, schützt vor versehentlich riesigen Uploads
MAX_TREFFER = 50
_AUSSCHNITT_RADIUS = 80   # Zeichen vor/nach dem Fundort, für eine lesbare Vorschau im Suchergebnis


def _ausschnitt(text: str, pos: int, laenge: int) -> str:
    von = max(0, pos - _AUSSCHNITT_RADIUS)
    bis = min(len(text), pos + laenge + _AUSSCHNITT_RADIUS)
    stueck = " ".join(text[von:bis].split())   # Zeilenumbrüche/Mehrfach-Leerraum glätten
    return ("…" if von > 0 else "") + stueck + ("…" if bis < len(text) else "")


class SkriptService:
    def __init__(self, repo: SkriptRepository, dateien: DateiSpeicher, pdf_text: PdfText | None = None):
        self.repo = repo
        self.dateien = dateien
        self.pdf_text = pdf_text

    def _skript(self, skript_id: str) -> Skript:
        skript = self.repo.get(skript_id)
        if skript is None:
            raise NotFound("Skript nicht gefunden.")
        return skript

    def upload(self, subject_id: str, dateiname: str, content_type: str | None, inhalt: bytes) -> Skript:
        if not (dateiname or "").strip():
            raise InvalidInput("Der Dateiname darf nicht leer sein.")
        if len(inhalt) > MAX_BYTES:
            raise InvalidInput("Die Datei ist zu groß (maximal 50 MB).")
        skript = Skript(subject_id=subject_id, dateiname=dateiname.strip(),
                         content_type=content_type or "application/octet-stream",
                         groesse=len(inhalt), hochgeladen_am=date.today().isoformat())
        self.repo.save(skript)
        self.dateien.speichere(skript.id, inhalt)
        return skript

    def list_skripte(self, subject_id: str | None = None) -> list[Skript]:
        return sorted(self.repo.list(subject_id), key=lambda s: (s.hochgeladen_am, s.dateiname), reverse=True)

    def datei(self, skript_id: str) -> tuple[Skript, bytes]:
        skript = self._skript(skript_id)
        inhalt = self.dateien.lies(skript_id)
        if inhalt is None:
            raise NotFound("Die Datei fehlt leider (nur die Angaben sind noch da).")
        return skript, inhalt

    def delete(self, skript_id: str) -> None:
        self._skript(skript_id)
        self.repo.delete(skript_id)
        self.dateien.loesche(skript_id)

    def suche(self, text: str, subject_id: str | None = None) -> list[dict]:
        """Volltextsuche über die hochgeladenen PDF-Skripte (andere Dateitypen liefern keinen Text, siehe
        `PdfText`-Port; keine KI, reiner Textvergleich wie bei der Bibelsuche). Liest den Text je Datei bei
        jedem Aufruf neu (kein eigener Speicher dafür) – für den üblichen Bestand an Skripten schnell genug."""
        text = (text or "").strip()
        if len(text) < 2:
            raise InvalidInput("Bitte mindestens 2 Zeichen eingeben.")
        if self.pdf_text is None:
            return []
        gesucht = text.lower()
        treffer = []
        for skript in self.list_skripte(subject_id):
            if skript.content_type != "application/pdf":
                continue
            inhalt = self.dateien.lies(skript.id)
            if inhalt is None:
                continue
            inhalt_text = self.pdf_text.text(inhalt)
            pos = inhalt_text.lower().find(gesucht)
            if pos >= 0:
                treffer.append({"id": skript.id, "subject_id": skript.subject_id, "dateiname": skript.dateiname,
                                "ausschnitt": _ausschnitt(inhalt_text, pos, len(text))})
            if len(treffer) >= MAX_TREFFER:
                break
        return treffer

    # Fach-Hooks
    def discard_subject(self, subject_id: str) -> None:
        for skript in self.repo.delete_subject(subject_id):
            self.dateien.loesche(skript.id)

    def subject_status(self, subject_id: str) -> dict:
        return {"count": len(self.repo.list(subject_id))}
