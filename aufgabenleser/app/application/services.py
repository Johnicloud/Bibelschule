"""Anwendungsfall: aus einem hochgeladenen Aufgabenblatt (PDF) Aufgaben-Vorschläge lesen.
Kennt nur Domäne und Ports, nicht pypdf/Ollama direkt. Liefert immer nur Vorschläge (siehe Projektnotizen,
Entscheidungen: „Ergebnisse der KI sind immer nur Vorschläge, die der Nutzer prüft“) – legt nie selbst eine
Aufgabe an; das macht die Oberfläche danach über die bestehende Aufgaben-API des Kerns."""
import json
import re

from app.application.ports import PdfText, TextKI
from app.domain.errors import InvalidInput
from app.domain.models import AufgabeVorschlag

PROMPT = (
    "Das folgende ist der Text eines Aufgabenblatts einer theologischen Ausbildungsstätte. "
    "Liste alle Aufgaben auf, die Studierende darin erledigen müssen (z. B. Lektüre, schriftliche Arbeit, "
    "Klausur, Anwesenheit). Gib ausschließlich ein JSON-Array aus, ein Objekt je Aufgabe mit den Schlüsseln "
    '"titel" (kurzer Titel), "frist" (Datum im Format JJJJ-MM-TT oder null, falls keins im Text steht) und '
    '"gewichtung" (anteilige Bewertung in Prozent als Zahl oder null, falls keine angegeben ist). '
    "Kein weiterer Text, keine Erklärung, nur das JSON-Array.\n\nText:\n"
)


def _parse_vorschlaege(antwort: str) -> list[AufgabeVorschlag]:
    """Ollama hält sich nicht immer ans reine JSON – nimmt den ersten Array-Abschnitt der Antwort.
    Ungültige oder unvollständige Einträge werden übersprungen statt die ganze Antwort zu verwerfen."""
    match = re.search(r"\[.*\]", antwort, re.DOTALL)
    if not match:
        return []
    try:
        rohdaten = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    vorschlaege = []
    for eintrag in rohdaten if isinstance(rohdaten, list) else []:
        if not isinstance(eintrag, dict):
            continue
        titel = str(eintrag.get("titel") or "").strip()
        if not titel:
            continue
        frist = eintrag.get("frist")
        frist = str(frist).strip() if frist else None
        gewichtung = eintrag.get("gewichtung")
        gewichtung = gewichtung if isinstance(gewichtung, (int, float)) and not isinstance(gewichtung, bool) else None
        vorschlaege.append(AufgabeVorschlag(titel=titel, frist=frist or None, gewichtung=gewichtung))
    return vorschlaege


class AufgabenLeseService:
    def __init__(self, pdf_text: PdfText, ki: TextKI | None = None):
        self.pdf_text = pdf_text
        self.ki = ki

    def lesen(self, pdf: bytes) -> dict:
        """Liest den Text des Aufgabenblatts, fragt Ollama nach den enthaltenen Aufgaben.
        `rohtext_ki` bleibt immer sichtbar, auch wenn sich daraus kein gültiges JSON gewinnen ließ –
        dann liest der Nutzer selbst nach und legt die Aufgaben von Hand an."""
        if self.ki is None:
            raise InvalidInput("Keine KI eingerichtet (OLLAMA_URL fehlt). Ohne sie lassen sich keine Aufgaben vorschlagen.")
        text = self.pdf_text.text_auslesen(pdf)
        if not text.strip():
            raise InvalidInput("Aus der PDF-Datei ließ sich kein Text lesen.")
        try:
            antwort = self.ki.frage(PROMPT + text)
        except Exception as e:   # Ollama kann nicht erreichbar sein, zu lange brauchen o. Ä.
            raise InvalidInput(f"Die KI war nicht erreichbar: {e}") from e
        vorschlaege = _parse_vorschlaege(antwort)
        return {
            "vorschlaege": [{"titel": v.titel, "frist": v.frist, "gewichtung": v.gewichtung} for v in vorschlaege],
            "rohtext_ki": antwort,
        }
