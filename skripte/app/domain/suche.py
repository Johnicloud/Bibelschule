"""Domäne: Volltextsuche in den Seitentexten der Skripte. Reine Textbearbeitung, keine Suchmaschine nötig."""
import re
import unicodedata
from dataclasses import dataclass

AUSSCHNITT = 70      # Zeichen links und rechts vom Fund


def glatt(text: str) -> str:
    """Ligaturen aufgelöst, Silbentrennung am Zeilenende (\"Apostel-\\nGeschichte\") zusammengezogen, Leerraum vereinheitlicht –
    Groß/Klein bleibt (für den Ausschnitt)."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"(?<=\w)[-\u00ad]\s*\n\s*(?=\w)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def normalisiert(text: str) -> str:
    return glatt(text).lower()      # lower statt casefold: behält die Länge, damit Fundstellen im geglätteten Text passen


def suchwoerter(anfrage: str) -> list[str]:
    return [w for w in normalisiert(anfrage).split(" ") if w]


@dataclass
class Fund:
    ausschnitt: str
    von: int          # Lage des ersten Suchworts im Ausschnitt (zum Hervorheben)
    bis: int


def finde(seitentext: str, woerter: list[str]) -> Fund | None:
    """Ein Fund, wenn ALLE Wörter auf der Seite vorkommen (Teilwörter zählen, „Gemeinde“ findet „Gemeinden“)."""
    if not woerter:
        return None
    text = glatt(seitentext)
    suchtext = text.lower()
    positionen = [suchtext.find(w) for w in woerter]
    if any(p < 0 for p in positionen):
        return None
    start = positionen[0]
    links = max(0, start - AUSSCHNITT)
    rechts = min(len(text), start + len(woerter[0]) + AUSSCHNITT)
    return Fund(("…" if links else "") + text[links:rechts] + ("…" if rechts < len(text) else ""),
                start - links + (1 if links else 0), start - links + (1 if links else 0) + len(woerter[0]))
