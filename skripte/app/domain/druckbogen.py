"""Domäne: Karteikarten aus einem Druckbogen wieder herauslesen (der Bogen, den die App unter „Als PDF drucken“ erzeugt).
Jede Karte trägt oben links eine kleine Nummer, auf Vorder- und Rückseite dieselbe; die Rückseiten stehen je Zeile
spaltenverkehrt. Darum wird nicht nach Lage, sondern nach der Nummer zugeordnet: erstes Vorkommen = Vorderseite,
zweites = Rückseite."""
import re
from dataclasses import dataclass

NUMMER_MAX_GROESSE = 9.5      # die Nummern sind klein gesetzt (8 pt), der Kartentext größer


@dataclass
class Textstueck:
    seite: int
    x: float
    y: float
    groesse: float
    text: str


def _zellen(stuecke: list[Textstueck]) -> list[tuple[int, int, str]]:
    """(Seite, Nummer, Text) je Zelle: jedes Textstück gehört zur Nummer links oberhalb von ihm."""
    ergebnis = []
    for seite in sorted({s.seite for s in stuecke}):
        auf_seite = [s for s in stuecke if s.seite == seite]
        nummern = [s for s in auf_seite if s.groesse <= NUMMER_MAX_GROESSE and re.fullmatch(r"\d{1,4}", s.text.strip())]
        texte = [s for s in auf_seite if s not in nummern and s.text.strip()]
        je_nummer: dict[int, list[Textstueck]] = {id(n): [] for n in nummern}
        for t in texte:
            kandidaten = [n for n in nummern if n.x <= t.x + 1 and n.y >= t.y]
            if not kandidaten:
                continue
            n = min(kandidaten, key=lambda n: (-n.x, n.y - t.y))
            je_nummer[id(n)].append(t)
        for n in nummern:
            zeilen = sorted(je_nummer[id(n)], key=lambda t: -t.y)
            ergebnis.append((seite, int(n.text), " ".join(z.text.strip() for z in zeilen)))
    return ergebnis


def karten_aus_druckbogen(stuecke: list[Textstueck]) -> list[tuple[str, str]]:
    """[(Frage, Antwort)] in Nummern-Reihenfolge – leer, wenn das kein Druckbogen ist."""
    vorder: dict[int, str] = {}
    hinter: dict[int, str] = {}
    for _seite, nummer, text in _zellen(stuecke):
        if nummer not in vorder:
            vorder[nummer] = text
        elif nummer not in hinter:
            hinter[nummer] = text
    if len(hinter) < 1 or len(hinter) < len(vorder) * 0.8:      # fast alle Nummern müssen zweimal vorkommen
        return []
    return [(vorder[n], hinter[n]) for n in sorted(hinter) if vorder[n] and hinter[n]]
