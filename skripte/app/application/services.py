"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from datetime import date

from app.application.ports import DateiSpeicher, SkriptRepository
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Skript

MAX_BYTES = 50 * 1024 * 1024   # 50 MB: genug für ein Skript, schützt vor versehentlich riesigen Uploads


class SkriptService:
    def __init__(self, repo: SkriptRepository, dateien: DateiSpeicher):
        self.repo = repo
        self.dateien = dateien

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

    # Fach-Hooks
    def discard_subject(self, subject_id: str) -> None:
        for skript in self.repo.delete_subject(subject_id):
            self.dateien.loesche(skript.id)

    def subject_status(self, subject_id: str) -> dict:
        return {"count": len(self.repo.list(subject_id))}
