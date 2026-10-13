"""Anwendungsfälle. Kennen nur Domäne und Ports, nicht reportlab/pypdf/Ollama direkt."""
from app.application.ports import DateiSpeicher, PdfRenderer, TextKI, VorlageRepository
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import MAX_BUECHER, Vorlage
from app.domain.standard_vorlage import STANDARD_VORLAGE_ID


def _clean(text: str, feld: str) -> str:
    text = (text or "").strip()
    if not text:
        raise InvalidInput(f"{feld} darf nicht leer sein.")
    return text


class PdfService:
    def __init__(self, vorlagen: VorlageRepository, dateien: DateiSpeicher, renderer: PdfRenderer,
                 ki: TextKI | None = None):
        self.vorlagen = vorlagen
        self.dateien = dateien
        self.renderer = renderer
        self.ki = ki

    def _vorlage(self, vorlage_id: str) -> Vorlage:
        vorlage = self.vorlagen.get(vorlage_id)
        if vorlage is None:
            raise NotFound("Vorlage nicht gefunden.")
        return vorlage

    def list_vorlagen(self) -> list[Vorlage]:
        return sorted(self.vorlagen.list(), key=lambda v: v.name.casefold())

    def hochladen(self, name: str, dateiname: str, inhalt: bytes) -> Vorlage:
        """Neue Vorlage ohne Felder (die trägt man danach von Hand ein); Ollama liefert dazu nur einen
        Textvorschlag, welche Angaben im Formular vorkommen – keine automatische Positionierung."""
        vorlage = Vorlage(name=_clean(name, "Der Name"), dateiname=_clean(dateiname, "Der Dateiname"))
        if self.ki is not None:
            try:
                text = self.renderer.text_auslesen(inhalt)
                vorlage.ki_vorschlag = self.ki.frage(
                    "Das ist der Text eines PDF-Formulars. Liste stichpunktartig auf, welche Angaben "
                    "darin ausgefüllt werden müssen (z. B. Name, Datum, Tabellen-Spalten):\n\n" + text
                ) if text else None
            except Exception as e:   # Ollama kann fehlen/nicht erreichbar sein – dann eben kein Vorschlag
                vorlage.ki_vorschlag = f"(Kein KI-Vorschlag: {e})"
        self.vorlagen.save(vorlage)
        self.dateien.speichere(vorlage.id, inhalt)
        return vorlage

    def delete(self, vorlage_id: str) -> None:
        if vorlage_id == STANDARD_VORLAGE_ID:
            raise InvalidInput("Die mitgelieferte Vorlage kann nicht gelöscht werden.")
        self._vorlage(vorlage_id)
        self.vorlagen.delete(vorlage_id)
        self.dateien.loesche(vorlage_id)

    def fuellen(self, vorlage_id: str, werte: dict[str, str], buecher: list[dict] | None = None) -> bytes:
        vorlage = self._vorlage(vorlage_id)
        pdf = self.dateien.lies(vorlage_id)
        if pdf is None:
            raise NotFound("Die Datei der Vorlage fehlt.")
        alle_werte = dict(werte)
        for i, buch in enumerate((buecher or [])[:MAX_BUECHER]):
            alle_werte[f"buch_{i}_titel"] = str(buch.get("titel", ""))
            alle_werte[f"buch_{i}_seiten"] = str(buch.get("seiten", ""))
        if buecher and len(buecher) > MAX_BUECHER:
            raise InvalidInput(f"Das Formular hat nur Platz für {MAX_BUECHER} Bücher.")
        return self.renderer.fuelle(pdf, alle_werte, vorlage.felder)
