"""Ausgehender Adapter: liest den eigentlichen Bibeltext (Verse) aus der PDF heraus, je Buch innerhalb seines
Seitenbereichs (von `buchseiten_erkennen` in pdf_text.py, also schon bekannt, wo ein Buch beginnt und endet).

Kein OCR, keine KI – reine Textbereinigung: Seitenzahl-Kopfzeilen, Fußnotenzeilen (z. B. "a (1,26) hebr. ...")
und Querverweiszeilen (z. B. "Ps 104,2; Jos 45,7; 2Kor 4,6") werden herausgefiltert, Ligaturen (ﬂ, ﬁ, …) und
Trennungen am Zeilenumbruch repariert. Versgrenzen erkennt man an der Zahl, die jeden Vers einleitet – entweder
ganz am Zeilenanfang oder nach ".  " (Punkt + zwei Leerzeichen) mitten in der Zeile, beides im Text sichtbare
Muster dieser Ausgabe.

Bekannte Lücke: Vers 1 eines Kapitels steht im Druck nie mit einer eigenen Zahl da (nur Vers 2 und folgende
sind nummeriert). Innerhalb eines Kapitels erkennt das kein Problem (der Text vor der ersten Zahl ist Vers 1).
Am KAPITELWECHSEL aber steht zwischen dem letzten nummerierten Vers des alten und der "2" des neuen Kapitels
nichts, was die Grenze im Text markiert (Zwischenüberschriften werden nicht zuverlässig erkannt, da die PDF
keine Schriftart-Information mehr hergibt) – der unnummerierte Vers 1 jedes Kapitels (außer dem ersten Kapitel
eines Buches) hängt darum am Ende des letzten Verses des VORIGEN Kapitels, statt eine eigene Zeile zu sein.
Betrifft nur Vers 1 nach einem Kapitelwechsel, sonst ist die Verszählung durchgehend korrekt. Ergebnisse sind
ein Vorschlag zum Prüfen und Nachbessern (siehe Projektnotizen, Entscheidungen), keine redaktionell geprüfte
Ausgabe."""
import io
import re

from pypdf import PdfReader

from app.application.ports import VerseExtractor
from app.domain.bible import find_book

_SEITENZAHL = re.compile(r"^[\divxlc]+(\s+[\divxlc]+)?$", re.I)
_FUSSNOTE = re.compile(r"^[a-z]\s*\(\d")
_VERS_ZEILENANFANG = re.compile(r"^(\d{1,3})\s+(?=[A-ZÄÖÜ„\"\[])")
_VERS_MITTEN = re.compile(r"([.!?:;])\s{1,2}(\d{1,3})\s+(?=[A-ZÄÖÜ„\"\[])")
_QUERVERWEIS_TEIL = re.compile(r"^([1-3]?\s*\.?\s*[^\W\d_][^\d,:;\-–—]*?)\s*\d")
_LIGATUREN = {"ﬂ": "fl", "ﬁ": "fi", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}


def _ist_querverweis_zeile(zeile: str) -> bool:
    """Eine Zeile aus nichts als Bibelstellen (Buch + Zahl), durch Semikolon getrennt, z. B.
    "Ps 104,2; Jos 45,7; 2Kor 4,6" – keine echte Verszeile, auch wenn sie Ziffern enthält."""
    if not zeile or len(zeile) > 120:
        return False
    teile = [t.strip() for t in zeile.split(";") if t.strip()]
    if not teile:
        return False
    for teil in teile:
        treffer = _QUERVERWEIS_TEIL.match(teil)
        if not treffer or find_book(treffer.group(1)) is None:
            return False
    return True


def _buchtext_bereinigen(seiten: list[str]) -> tuple[str, list[tuple[int, int]]]:
    """Baut den bereinigten Fließtext eines Buches und merkt sich dabei, an welcher Zeichen-Stelle welche
    Vers-Zahl beginnt. Gibt (text, [(stelle, zahl), ...]) zurück."""
    stuecke: list[str] = []
    marken: list[tuple[int, int]] = []
    pos = 0
    for seiten_text in seiten:
        for zeichen, ersatz in _LIGATUREN.items():
            seiten_text = seiten_text.replace(zeichen, ersatz)
        for n, roh in enumerate(seiten_text.split("\n")):
            zeile = roh.strip()
            if n == 0 and _SEITENZAHL.match(zeile):
                continue
            if _FUSSNOTE.match(zeile) or _ist_querverweis_zeile(zeile):
                continue
            rest = zeile
            vers_am_anfang = None
            treffer = _VERS_ZEILENANFANG.match(rest)
            if treffer:
                vers_am_anfang = int(treffer.group(1))
                rest = rest[treffer.end():]

            # Verszahlen mitten in der Zeile (nach Satzzeichen + 2 Leerzeichen) aus dem Text herauslösen,
            # dabei das Satzzeichen behalten – sonst bliebe die Zahl als Text stehen.
            bereinigt: list[str] = []
            mitten_marken: list[tuple[int, int]] = []   # (Stelle INNERHALB von "rest bereinigt", Zahl)
            letztes_ende = 0
            for mm in _VERS_MITTEN.finditer(rest):
                bereinigt.append(rest[letztes_ende:mm.start()])
                bereinigt.append(mm.group(1) + " ")   # Satzzeichen + ein Leerzeichen bleiben erhalten
                mitten_marken.append((sum(len(t) for t in bereinigt), int(mm.group(2))))
                letztes_ende = mm.end()
            bereinigt.append(rest[letztes_ende:])
            rest = "".join(bereinigt)

            # Trennung am Zeilenumbruch ("fruchtbrin-" + "gend"): ohne Leerzeichen und Bindestrich fortsetzen.
            if stuecke and stuecke[-1].endswith("-") and rest[:1].islower():
                stuecke[-1] = stuecke[-1][:-1]
                pos -= 1
                trenner = ""
            else:
                trenner = " " if stuecke else ""
            if vers_am_anfang is not None:
                marken.append((pos + len(trenner), vers_am_anfang))
            for stelle, zahl in mitten_marken:
                marken.append((pos + len(trenner) + stelle, zahl))
            stueck = trenner + rest
            stuecke.append(stueck)
            pos += len(stueck)
    return "".join(stuecke), marken


_UNPLAUSIBLER_SPRUNG = 15   # z. B. "782 Jahre" in einem Stammbaum-Kapitel: ein Großbuchstabe folgt (deutsche
                             # Nomen sind immer groß geschrieben), aber keine echte Versgrenze – verwerfen


def _verse_aus_marken(text: str, marken: list[tuple[int, int]]) -> list[tuple[int, int, str]]:
    """[(kapitel, vers, text), ...] – siehe Modul-Docstring für die bekannte Lücke bei Vers 1 nach einem
    Kapitelwechsel."""
    marken = sorted(marken)
    ergebnisse = []
    kapitel = 1
    letzte_nummer = 1   # Vers 1 ist nie selbst nummeriert
    start = 0
    for stelle, nummer in marken:
        ist_sprung = nummer >= letzte_nummer and nummer > letzte_nummer + _UNPLAUSIBLER_SPRUNG
        if ist_sprung:
            continue   # keine Versgrenze, sondern z. B. eine Jahreszahl mitten im Vers – Text läuft weiter
        stueck = text[start:stelle].strip()
        if stueck:
            ergebnisse.append((kapitel, letzte_nummer, stueck))
        if nummer < letzte_nummer:
            kapitel += 1   # Verszahl ist kleiner als zuvor: neues Kapitel hat begonnen
        letzte_nummer = nummer
        start = stelle
    rest = text[start:].strip()
    if rest:
        ergebnisse.append((kapitel, letzte_nummer, rest))
    return ergebnisse


class PypdfVerseExtractor(VerseExtractor):
    def buch_verse(self, pdf_bytes: bytes, von_seite: int, bis_seite: int | None) -> list[tuple[int, int, str]]:
        """`von_seite`/`bis_seite` sind 1-basierte PDF-Seiten (bis_seite inklusive, None = bis zum Ende)."""
        reader = PdfReader(io.BytesIO(pdf_bytes))
        ende = bis_seite if bis_seite is not None else len(reader.pages)
        seiten = [reader.pages[i].extract_text() or "" for i in range(von_seite - 1, min(ende, len(reader.pages)))]
        text, marken = _buchtext_bereinigen(seiten)
        return _verse_aus_marken(text, marken)
