"""Anwendungsfall: zu einem Bibelkapitel Verständnisfragen vorschlagen lassen (Ollama).
Kennt nur Domäne und Ports, nicht httpx/Ollama/Bibel-Dienst direkt. Liefert immer nur Vorschläge (siehe
Projektnotizen, Entscheidungen: „Ergebnisse der KI sind immer nur Vorschläge, die der Nutzer prüft“) – legt
nie selbst eine Karteikarte an; das macht die Oberfläche danach über die bestehende Karteikarten-API des Kerns."""
import json
import re

from app.application.ports import BibelQuelle, TextKI
from app.domain.errors import InvalidInput
from app.domain.models import FrageVorschlag

PROMPT = (
    "Das folgende ist der Bibeltext eines Kapitels. Formuliere 3 bis 5 Verständnisfragen dazu, die beim "
    "Durcharbeiten des Kapitels helfen (Inhalt, Zusammenhänge, Bedeutung – keine reinen Ja/Nein-Fragen). "
    'Gib ausschließlich ein JSON-Array aus, ein Objekt je Frage mit dem Schlüssel "frage" (die Frage als '
    "Text, keine Antwort dazu). Kein weiterer Text, keine Erklärung, nur das JSON-Array.\n\nText:\n"
)


def _parse_vorschlaege(antwort: str) -> list[FrageVorschlag]:
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
        if isinstance(eintrag, str):
            frage = eintrag.strip()
        elif isinstance(eintrag, dict):
            frage = str(eintrag.get("frage") or "").strip()
        else:
            continue
        if frage:
            vorschlaege.append(FrageVorschlag(frage=frage))
    return vorschlaege


class FragenKiService:
    def __init__(self, bibel: BibelQuelle, ki: TextKI | None = None):
        self.bibel = bibel
        self.ki = ki

    def generieren(self, buch_kurz: str, kapitel: int) -> dict:
        """Holt den Verstext des Kapitels vom Bibel-Dienst, fragt Ollama nach Verständnisfragen dazu.
        `rohtext_ki` bleibt immer sichtbar, auch wenn sich daraus kein gültiges JSON gewinnen ließ –
        dann liest der Nutzer selbst nach und formuliert die Fragen von Hand."""
        if self.ki is None:
            raise InvalidInput("Keine KI eingerichtet (OLLAMA_URL fehlt). Ohne sie lassen sich keine Fragen vorschlagen.")
        try:
            text = self.bibel.kapitel(buch_kurz, kapitel)
        except Exception as e:   # Bibel-Dienst kann nicht erreichbar sein
            raise InvalidInput(f"Der Bibel-Dienst war nicht erreichbar: {e}") from e
        if not text.strip():
            raise InvalidInput("Für dieses Kapitel ist noch kein Verstext eingelesen.")
        try:
            antwort = self.ki.frage(PROMPT + text)
        except Exception as e:   # Ollama kann nicht erreichbar sein, zu lange brauchen o. Ä.
            raise InvalidInput(f"Die KI war nicht erreichbar: {e}") from e
        vorschlaege = _parse_vorschlaege(antwort)
        return {
            "vorschlaege": [{"frage": v.frage} for v in vorschlaege],
            "rohtext_ki": antwort,
        }
