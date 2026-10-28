"""Domäne: wie zuverlässig ist der erkannte Text einer Seite? Eine Schätzung ohne Wörterbuch: Texterkennung macht aus
Rauschen (Logos, Randnotizen, Flecken) Zeichenfolgen, die wie Wörter aussehen, aber keine deutschen Wörter sein können
(zu wenige Vokale, lange Konsonantenketten, Groß/Klein mitten im Wort). Der Anteil der Zeichen in glaubhaften Wörtern
ist die Zahl; Sonderzeichen-Müll senkt sie."""
import re

VOKALE = set("aeiouäöüyAEIOUÄÖÜY")
WORT = re.compile(r"[^\W\d_]+")
MIN_WOERTER = 15         # darunter sagt die Zahl nichts (Titelseite, Bild, leere Seite)
UNSICHER_UNTER = 85      # Seiten darunter gelten als „unsicher“ (an einem gut erkannten Skript gemessen: schlechteste Seiten 89)


def _glaubhaft(wort: str) -> bool:
    if sum(1 for z in wort if z in VOKALE) / len(wort) not in _SPANNE:
        return False
    if re.search(r"[^aeiouäöüyAEIOUÄÖÜY]{6,}", wort):
        return False
    return wort.islower() or wort.isupper() or (wort[0].isupper() and wort[1:].islower())


class _Spanne:
    def __contains__(self, anteil: float) -> bool:
        return 0.2 <= anteil <= 0.75


_SPANNE = _Spanne()


def seitenqualitaet(text: str) -> int | None:
    """0 bis 100, oder None, wenn zu wenig Text da ist, um etwas zu sagen."""
    woerter = [w for w in WORT.findall(text) if len(w) >= 3]
    if len(woerter) < MIN_WOERTER:
        return None
    buchstaben = sum(len(w) for w in woerter)
    gut = sum(len(w) for w in woerter if _glaubhaft(w))
    zeichen = [z for z in text if not z.isspace()]
    muell = sum(1 for z in zeichen if not (z.isalnum() or z in ".,;:!?()-–„“\"'’»«/%§&*"))
    return max(0, round(100 * gut / buchstaben - min(30, 100 * muell / max(len(zeichen), 1))))
