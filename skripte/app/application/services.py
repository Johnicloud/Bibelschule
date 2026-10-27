"""Anwendungsfälle. Kennen nur Domäne und Ports."""
import logging
import threading
import unicodedata
from datetime import date

from app.application.ports import DateiLeser, DateiSpeicher, SkriptRepository, Texterkennung
from app.domain.druckbogen import karten_aus_druckbogen
from app.domain.errors import InvalidInput, NotFound
from app.domain.fragen import fragen_erkennen
from app.domain.models import Skript

MAX_BYTES = 200 * 1024 * 1024   # 200 MB: genug für ein Skript, schützt vor versehentlich riesigen Uploads


def _sauberer_name(name: str) -> str:
    """Ohne unsichtbare Formatzeichen (z. B. die Links-nach-rechts-Marke, die beim Kopieren eines Dateinamens mitkommt)
    und ohne Pfadanteile oder Zeilenumbrüche."""
    name = "".join(z for z in (name or "") if unicodedata.category(z) not in ("Cf", "Cc"))
    return name.replace("/", "-").replace("\\", "-").strip()


def _text_key(skript_id: str) -> str:
    return f"{skript_id}.text"


class SkriptService:
    def __init__(self, repo: SkriptRepository, dateien: DateiSpeicher, leser: DateiLeser | None = None,
                 erkennung: Texterkennung | None = None):
        self.repo = repo
        self.dateien = dateien
        self.leser = leser
        self.erkennung = erkennung
        self._laufend: set[str] = set()       # Texterkennung läuft gerade (nur im Speicher: nach Neustart ist sie ohnehin weg)
        self._fehler: dict[str, str] = {}

    def _skript(self, skript_id: str) -> Skript:
        skript = self.repo.get(skript_id)
        if skript is None:
            raise NotFound("Skript nicht gefunden.")
        return skript

    def upload(self, subject_id: str, dateiname: str, content_type: str | None, inhalt: bytes) -> Skript:
        dateiname = _sauberer_name(dateiname)
        if not dateiname:
            raise InvalidInput("Der Dateiname darf nicht leer sein.")
        if len(inhalt) > MAX_BYTES:
            raise InvalidInput("Die Datei ist zu groß (maximal 200 MB).")
        skript = Skript(subject_id=subject_id, dateiname=dateiname,
                         content_type=content_type or "application/octet-stream",
                         groesse=len(inhalt), hochgeladen_am=date.today().isoformat())
        self.repo.save(skript)
        self.dateien.speichere(skript.id, inhalt)
        return skript

    def umbenennen(self, skript_id: str, dateiname: str) -> Skript:
        """Neuer Name. Die Endung bleibt: sie entscheidet, wie die Datei angezeigt und gelesen wird."""
        skript = self._skript(skript_id)
        name = _sauberer_name(dateiname)
        if not name:
            raise InvalidInput("Der Dateiname darf nicht leer sein.")
        endung = skript.dateiname.rsplit(".", 1)[-1] if "." in skript.dateiname else ""
        if endung and not name.lower().endswith("." + endung.lower()):
            name = f"{name}.{endung}"
        skript.dateiname = name
        self.repo.save(skript)
        return skript

    def list_skripte(self, subject_id: str | None = None) -> list[Skript]:
        return sorted(self.repo.list(subject_id), key=lambda s: (s.hochgeladen_am, s.dateiname), reverse=True)

    def datei(self, skript_id: str, original: bool = False) -> tuple[Skript, bytes]:
        """Der Inhalt. Gibt es eine Fassung mit erkanntem Text, zeigt sie sich statt des Originals (sieht gleich aus,
        lässt sich aber markieren und kopieren); `original=True` liefert immer die hochgeladene Datei."""
        skript = self._skript(skript_id)
        if not original and self.dateien.vorhanden(_text_key(skript_id)):
            return skript, self.dateien.lies(_text_key(skript_id))
        inhalt = self.dateien.lies(skript_id)
        if inhalt is None:
            raise NotFound("Die Datei fehlt leider (nur die Angaben sind noch da).")
        return skript, inhalt

    def _lesefassung(self, skript_id: str) -> tuple[Skript, bytes]:
        """Was zum Auslesen dient: das Original. Nur wenn es keinen Text hat (gescannt), die Fassung mit erkanntem Text –
        ein Original mit echtem Text ist immer genauer als jede Texterkennung."""
        if self.leser is None:
            raise InvalidInput("Dateien lesen ist hier nicht eingerichtet.")
        skript, original = self.datei(skript_id, original=True)
        if skript.dateiname.lower().endswith(".pdf") and not self.leser.hat_text(skript.dateiname, original) \
                and self.dateien.vorhanden(_text_key(skript_id)):
            return skript, self.dateien.lies(_text_key(skript_id))
        return skript, original

    def fragen(self, skript_id: str) -> list[str]:
        """Die Fragen einer Fragenliste (PDF, Word, Pages) – nur ein Vorschlag, die Karteikarten legt der Nutzer an."""
        skript, inhalt = self._lesefassung(skript_id)
        return fragen_erkennen(self.leser.zeilen(skript.dateiname, inhalt))

    def karten(self, skript_id: str) -> dict:
        """Vorschläge für Karteikarten aus einer Datei. Ist sie ein Druckbogen der App („Als PDF drucken“), kommen die
        Antworten von der Rückseite mit; sonst wird sie als Fragenliste gelesen (Antworten leer)."""
        skript, inhalt = self._lesefassung(skript_id)
        paare = karten_aus_druckbogen(self.leser.textstuecke(skript.dateiname, inhalt))
        if paare:
            return {"quelle": "druckbogen", "karten": [{"frage": f, "antwort": a} for f, a in paare]}
        return {"quelle": "fragenliste", "karten": [{"frage": f, "antwort": ""} for f in self.fragen(skript_id)]}

    def vorschau_pdf(self, skript_id: str) -> bytes | None:
        skript, inhalt = self.datei(skript_id)
        return self.leser.pdf_vorschau(skript.dateiname, inhalt) if self.leser else None

    # Texterkennung für gescannte PDFs (ohne Text lässt sich nichts markieren oder kopieren)
    def text_status(self, skript_id: str) -> dict:
        if skript_id in self._laufend:
            return {"status": "laeuft", "fehler": None}
        if self.dateien.vorhanden(_text_key(skript_id)):
            return {"status": "fertig", "fehler": None}
        if skript_id in self._fehler:
            return {"status": "fehler", "fehler": self._fehler[skript_id]}
        return {"status": "keine", "fehler": None}

    def text_erkennen_starten(self, skript_id: str, im_hintergrund: bool = True) -> None:
        """Startet die Erkennung (dauert bei einem ganzen Skript Minuten, darum eigener Thread, nicht abgewartet)."""
        skript = self._skript(skript_id)
        if self.erkennung is None:
            raise InvalidInput("Texterkennung ist hier nicht eingerichtet.")
        if not skript.dateiname.lower().endswith(".pdf"):
            raise InvalidInput("Texterkennung gibt es nur für PDF-Dateien.")
        if skript_id in self._laufend:
            return
        original = self.dateien.lies(skript_id)
        if original is not None and self.leser is not None and self.leser.hat_text(skript.dateiname, original):
            raise InvalidInput("Dieses PDF hat schon Text, die Erkennung ist nicht nötig.")
        self._fehler.pop(skript_id, None)
        self._laufend.add(skript_id)
        if im_hintergrund:
            threading.Thread(target=self._erkennen, args=(skript_id,), daemon=True).start()
        else:
            self._erkennen(skript_id)

    def _erkennen(self, skript_id: str) -> None:
        try:
            original = self.dateien.lies(skript_id)
            if original is None:
                raise InvalidInput("Die Datei fehlt leider.")
            self.dateien.speichere(_text_key(skript_id), self.erkennung.erkennen(original))
        except Exception as e:
            logging.getLogger(__name__).exception("Texterkennung fehlgeschlagen")
            self._fehler[skript_id] = str(e) if isinstance(e, InvalidInput) else "Die Texterkennung ist fehlgeschlagen."
        finally:
            self._laufend.discard(skript_id)

    def delete(self, skript_id: str) -> None:
        self._skript(skript_id)
        self.repo.delete(skript_id)
        self.dateien.loesche(skript_id)
        self.dateien.loesche(_text_key(skript_id))

    # Fach-Hooks
    def discard_subject(self, subject_id: str) -> None:
        for skript in self.repo.delete_subject(subject_id):
            self.dateien.loesche(skript.id)
            self.dateien.loesche(_text_key(skript.id))

    def subject_status(self, subject_id: str) -> dict:
        return {"count": len(self.repo.list(subject_id))}
