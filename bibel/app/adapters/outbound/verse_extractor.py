"""Ausgehender Adapter: liest den eigentlichen Bibeltext (Verse) aus der PDF heraus, je Buch innerhalb seines
Seitenbereichs (von `buchseiten_erkennen` in pdf_text.py, also schon bekannt, wo ein Buch beginnt und endet).

Kein OCR, keine KI – aber anders als eine reine Textbereinigung über rohen Fließtext: PyMuPDF liefert je
Textabschnitt (Span) Schriftart UND -größe, und die Schlachter-PDF nutzt das sehr konsequent:
- Fließtext steht in `*-Regular`, die Verszahl direkt davor in einer FETTEN Schriftart und etwas kleiner
  (z. B. `Utopia-Semibold`, ~88 % der Fließtextgröße) – eine Verszahl lässt sich daran sicher erkennen, nicht
  nur über "Zahl am Zeilenanfang" (das verwechselte z. B. eine Jahreszahl leicht mit einer neuen Versgrenze).
- Fußnotenzeichen mitten im Satz UND die Fußnoten selbst am Seitenende sind deutlich KLEINER als der Fließtext
  (< 80 % dessen Größe) – fallen jetzt komplett weg, statt wie zuvor nur über eine Regelerkennung für ganze
  Fußnotenzeilen (einzelne Fußnotenzeichen mitten im Wort, z. B. "Welt" + hochgestelltes "b", blieben bisher
  als "Weltb" im Text stehen). ABER: der Gottesname "HERR" steht in dieser Ausgabe in Kapitälchen (auch in
  kursiven Psalm-Überschriften) – nur das "H" in normaler Größe, "ERR"/"ERRN" in derselben kleinen Schriftgröße
  wie ein Fußnotenzeichen (~69 % statt < 80 % wie erwartet, keine klare Trennung über die Größe allein möglich)!
  Unterschieden wird darum über die LÄNGE (ein Fußnotenzeichen ist immer genau ein Zeichen, ein Kapitälchen-
  Rest mehrere) UND darüber, ob die ZEILE daneben noch normal großen Fließtext hat: ein mehrzeichiger kleiner
  Abschnitt in einer sonst normal großen Zeile ist ein Kapitälchen-Rest (bleibt stehen, z. B. "H" + "ERR" wird
  wieder "HERR"), eine ZEILE, die komplett nur aus kleinen Abschnitten besteht, ist eine echte Fußnotenzeile
  (fällt weiterhin weg) – ein einzelnes Fußnotenzeichen fällt so oder so immer weg.
- Zwischenüberschriften ("Die Hochzeit von Kana", manchmal zweizeilig mit einer Art Augenbraue darüber, z. B.
  "Jesus und Nikodemus." + "Die Notwendigkeit der Wiedergeburt") stehen kursiv, meist direkt gefolgt von einer
  Bibelstellen-Zeile (wie die Querverweis-Erkennung unten) – beides fiel bisher nicht zuverlässig weg und
  landete mitten im Verstext.
- Der Buchtitel am Anfang jedes Buches ("Das Evangelium nach Johannes") steht deutlich GRÖSSER als der Fließtext
  (über 120 % dessen Größe) – fällt ebenfalls weg, sonst hinge er am ersten Vers.

Eine per OCR erkannte Textebene (siehe fraktur_ocr.py, für ein gescanntes Faksimile ohne eigenen Text) kennt
keine fetten Verszahlen – jedes Zeichen kommt dort gleich gewichtet heraus. Findet eine Zeile keine Verszahl
über die Schriftart, fällt `_regelbasierte_marken` auf die alte, reine Textregel zurück (Zahl am Zeilenanfang
oder nach Satzzeichen + 1-2 Leerzeichen, gefolgt von einem Großbuchstaben) – dieselbe (ungefähre) Güte wie vor
dieser Umstellung, nur dort, wo das Schriftbild selbst keine bessere Information hergibt.

Bekannte Lücke bleibt dieselbe wie vorher, nur kleiner: Vers 1 eines Kapitels steht im Druck nie mit einer
eigenen Zahl da. Jede verworfene Zwischenüberschrift (siehe oben) ist ein KANDIDAT für eine genaue Kapitel-
grenze – aber erst, wenn danach tatsächlich eine Verszahl kommt, die kleiner ist als die zuletzt gesehene
(derselbe Hinweis, der schon vorher ein neues Kapitel erkannte): eine Seite hat oft MEHRERE Zwischenüber-
schriften (z. B. "Die erste Tempelreinigung" mitten in Johannes 2, lange vor dessen Ende), nur die, der
unmittelbar eine solche Verszahl-Rücksetzung folgt, ist wirklich ein Kapitelanfang (siehe `_verse_aus_marken`:
der Kandidat direkt vor dieser Rücksetzung gewinnt). Ohne eine Überschrift unmittelbar vor der Rücksetzung
bleibt die bekannte Lücke wie zuvor: der unnummerierte Vers 1 hängt am Ende des letzten Verses des vorigen
Kapitels. Ergebnisse sind weiterhin ein Vorschlag zum Prüfen und Nachbessern (siehe Projektnotizen,
Entscheidungen), keine redaktionell geprüfte Ausgabe."""
import re
from dataclasses import dataclass

import pymupdf

from app.application.ports import VerseExtractor
from app.domain.bible import find_book

_LIGATUREN = {"ﬂ": "fl", "ﬁ": "fi", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}
_QUERVERWEIS_TEIL = re.compile(r"^([1-3]?\s*\.?\s*[^\W\d_][^\d,:;\-–—]*?)\s*\d")
_QUERVERWEIS_FORTSETZUNG = re.compile(r"^\d")   # z. B. "6,44-45" nach "Joh 17,6;" – dasselbe Buch, nicht wiederholt
_KOPF_Y = 42.0                 # Seitenzahl + Buch/Kapitel-Kopfzeile stehen nie weiter unten als das
_FUSSNOTE_ANTEIL = 0.80         # Spannen unter 80 % der Fließtextgröße sind Fußnoten(-zeichen), kein Verstext
_VERSZAHL_MIN_ANTEIL = 0.80
_VERSZAHL_MAX_ANTEIL = 0.97
_KOERPER_MIN_ANTEIL = 0.97       # ab hier gilt eine Spanne als normal großer Fließtext
_TITEL_ANTEIL = 1.2             # Spannen über 120 % der Fließtextgröße sind ein Buchtitel, kein Verstext
_UNPLAUSIBLER_SPRUNG = 15       # z. B. "782 Jahre" in einem Stammbaum-Kapitel – keine echte Versgrenze


def _ist_fett(font: str) -> bool:
    f = font.lower()
    return "bold" in f or "semibold" in f or "black" in f


def _ist_kursiv(font: str) -> bool:
    f = font.lower()
    return "italic" in f or "oblique" in f


def _ist_querverweis_zeile(zeile: str) -> bool:
    """Eine Zeile aus nichts als Bibelstellen (Buch + Zahl), durch Semikolon getrennt, z. B.
    "Ps 104,2; Jos 45,7; 2Kor 4,6" – keine echte Verszeile, auch wenn sie Ziffern enthält. Bei mehreren
    Stellen aus demselben Buch bleibt der Buchname oft nur beim ersten Mal stehen (z. B. "Joh 17,6; 6,44-45" –
    das zweite Stück gilt weiter für Johannes), ein solches Stück zählt mit, wenn vorher schon ein Buch erkannt wurde."""
    if not zeile or len(zeile) > 120:
        return False
    teile = [t.strip() for t in zeile.split(";") if t.strip()]
    if not teile:
        return False
    hat_buch = False
    for teil in teile:
        treffer = _QUERVERWEIS_TEIL.match(teil)
        if treffer and find_book(treffer.group(1)) is not None:
            hat_buch = True
            continue
        if hat_buch and _QUERVERWEIS_FORTSETZUNG.match(teil):
            continue
        return False
    return hat_buch


@dataclass
class _Zeile:
    text: str
    vers_marken: list[tuple[int, int]]   # (Stelle INNERHALB von text, Zahl)
    nur_kursiv: bool

    @property
    def leer(self) -> bool:
        return not self.text.strip()


_VERS_ZEILENANFANG = re.compile(r"^(\d{1,3})\s+(?=[A-ZÄÖÜ„\"\[])")
_VERS_MITTEN = re.compile(r"([.!?:;])\s{1,2}(\d{1,3})\s+(?=[A-ZÄÖÜ„\"\[])")


def _regelbasierte_marken(text: str) -> tuple[str, list[tuple[int, int]]]:
    """Fällt zurück auf die alte, reine Textregel (Zahl am Zeilenanfang oder nach Satzzeichen + 1-2
    Leerzeichen, gefolgt von einem Großbuchstaben) – für eine per OCR erkannte Textebene (siehe fraktur_ocr.py),
    die keine fetten Verszahlen im Schriftbild kennt, dort ist jedes Zeichen gleich gewichtet."""
    marken: list[tuple[int, int]] = []
    rest = text
    treffer = _VERS_ZEILENANFANG.match(rest)
    vers_am_anfang = None
    if treffer:
        vers_am_anfang = int(treffer.group(1))
        rest = rest[treffer.end():]
    bereinigt: list[str] = []
    mitten_marken: list[tuple[int, int]] = []
    letztes_ende = 0
    for mm in _VERS_MITTEN.finditer(rest):
        bereinigt.append(rest[letztes_ende:mm.start()])
        bereinigt.append(mm.group(1) + " ")
        mitten_marken.append((sum(len(t) for t in bereinigt), int(mm.group(2))))
        letztes_ende = mm.end()
    bereinigt.append(rest[letztes_ende:])
    rest = "".join(bereinigt)
    if vers_am_anfang is not None:
        marken.append((0, vers_am_anfang))
    marken.extend(mitten_marken)
    return rest, marken


def _koerpergroesse(spans: list[dict]) -> float:
    """Die mit Abstand häufigste Schriftgröße auf der Seite, nach Zeichenzahl gewichtet – das ist der
    Fließtext (Verszahlen, Fußnoten und Überschriften kommen auf viel weniger Zeichen)."""
    gewicht: dict[float, int] = {}
    for s in spans:
        n = len(s["text"].strip())
        if n:
            gewicht[s["size"]] = gewicht.get(s["size"], 0) + n
    return max(gewicht, key=gewicht.get) if gewicht else 8.0


def _zeile_aus_spans(spans: list[dict], koerpergroesse: float) -> _Zeile | None:
    """Baut eine Zeile aus ihren Spans: Fußnotenzeichen/-text (deutlich kleinere Schrift) fallen weg, eine
    Verszahl (etwas kleinere, FETTE Schrift) wird als Marke gemerkt statt in den sichtbaren Text übernommen."""
    zeile_hat_koerpertext = any(
        _KOERPER_MIN_ANTEIL <= (s["size"] / koerpergroesse if koerpergroesse else 1) <= _TITEL_ANTEIL
        for s in spans if s["text"].strip())

    stuecke: list[str] = []
    marken: list[tuple[int, int]] = []
    pos = 0
    alles_kursiv = True
    irgendwas_gesehen = False
    for span in spans:
        text = span["text"]
        for zeichen, ersatz in _LIGATUREN.items():
            text = text.replace(zeichen, ersatz)
        if not text.strip():
            continue
        anteil = span["size"] / koerpergroesse if koerpergroesse else 1
        if anteil > _TITEL_ANTEIL:
            continue
        if anteil < _FUSSNOTE_ANTEIL:
            # Ein Fußnotenzeichen ist immer nur EIN Zeichen (a, b, …), ein Kapitälchen-Rest sind mehrere
            # (z. B. "ERR" bei "HERR", auch kursiv – eine Psalm-Überschrift steht ganz in Kursivschrift, siehe
            # Modul-Docstring). Ein Fußnotenzeichen fällt immer weg; ein Kapitälchen-Rest nur dann, wenn die
            # Zeile daneben gar keinen normal großen Text hat (dann eine echte Fußnotenzeile, die komplett
            # wegfällt) – sonst bleibt er stehen.
            ist_fussnotenzeichen = len(text.strip()) <= 2
            if ist_fussnotenzeichen or not zeile_hat_koerpertext:
                continue
        irgendwas_gesehen = True
        if _VERSZAHL_MIN_ANTEIL <= anteil <= _VERSZAHL_MAX_ANTEIL and _ist_fett(span["font"]):
            zahl_text = re.sub(r"\D", "", text)
            if zahl_text:
                marken.append((pos, int(zahl_text)))
            continue
        if not _ist_kursiv(span["font"]):
            alles_kursiv = False
        stuecke.append(text)
        pos += len(text)
    if not irgendwas_gesehen:
        return None
    text = "".join(stuecke)
    if not marken:
        text, marken = _regelbasierte_marken(text)
    return _Zeile(text=text, vers_marken=marken, nur_kursiv=alles_kursiv)


def _seite_lesen(page) -> list[_Zeile]:
    """Die Körper-Zeilen dieser Seite – die obere Kopfzeile (Seitenzahl, Buch/Kapitel-Angabe) ausgeschlossen."""
    d = page.get_text("dict")
    alle_spans = [sp for b in d["blocks"] for l in b.get("lines", []) for sp in l["spans"]]
    koerpergroesse = _koerpergroesse(alle_spans)

    zeilen: list[_Zeile] = []
    for block in d["blocks"]:
        for line in block.get("lines", []):
            spans = line["spans"]
            if not spans or line["bbox"][1] < _KOPF_Y:
                continue
            zeile = _zeile_aus_spans(spans, koerpergroesse)
            if zeile is not None:
                zeilen.append(zeile)
    return zeilen


def _buchtext_bauen(seiten_zeilen: list[list[_Zeile]]) -> tuple[str, list[tuple[int, int]], list[int]]:
    """Baut den Fließtext eines Buches über alle seine Seiten, dazu die Verszahl-Marken (Stelle, Zahl) und
    die Stellen aller verworfenen Zwischenüberschriften (Kandidaten für eine genaue Kapitelgrenze, siehe
    Modul-Docstring und `_verse_aus_marken`)."""
    stuecke: list[str] = []
    marken: list[tuple[int, int]] = []
    ueberschriften: list[int] = []
    pos = 0
    for zeilen in seiten_zeilen:
        i = 0
        while i < len(zeilen):
            zeile = zeilen[i]
            if zeile.leer:
                i += 1
                continue
            ist_ueberschrift = zeile.nur_kursiv and not zeile.vers_marken
            if ist_ueberschrift:
                # Eine Zwischenüberschrift ist manchmal zweizeilig (eine Art Augenbraue über der eigentlichen
                # Überschrift, z. B. "Jesus und Nikodemus." + "Die Notwendigkeit der Wiedergeburt") – jede
                # weitere, ebenfalls rein kursive Zeile gehört noch dazu.
                ende = i + 1
                while ende < len(zeilen) and zeilen[ende].nur_kursiv and not zeilen[ende].vers_marken:
                    ende += 1
                bibelstellenzeile = zeilen[ende] if ende < len(zeilen) else None
                if (bibelstellenzeile is not None and not bibelstellenzeile.vers_marken
                        and _ist_querverweis_zeile(bibelstellenzeile.text)):
                    # Die ganze Überschrift + die Bibelstellen-Zeile darunter verwerfen (kein Verstext), die
                    # Stelle davor als Kandidat merken – ob daraus wirklich eine Kapitelgrenze wird, entscheidet
                    # erst `_verse_aus_marken` anhand der nächsten Verszahl.
                    ueberschriften.append(pos)
                    i = ende + 1
                    continue
            if not zeile.vers_marken and _ist_querverweis_zeile(zeile.text):
                i += 1
                continue
            if stuecke and stuecke[-1].endswith("-") and zeile.text[:1].islower():
                stuecke[-1] = stuecke[-1][:-1]
                pos -= 1
                trenner = ""
            else:
                trenner = " " if stuecke else ""
            if zeile.vers_marken:
                marken.extend((pos + len(trenner) + stelle, zahl) for stelle, zahl in zeile.vers_marken)
            stueck = trenner + zeile.text
            stuecke.append(stueck)
            pos += len(stueck)
            i += 1
    return "".join(stuecke), marken, ueberschriften


def _verse_aus_marken(text: str, marken: list[tuple[int, int]], ueberschriften: list[int]) -> list[tuple[int, int, str]]:
    """[(kapitel, vers, text), ...] – siehe Modul-Docstring für die verbleibende Lücke bei Vers 1."""
    ueberschriften = sorted(ueberschriften)
    ergebnisse = []
    kapitel = 1
    letzte_nummer = 1   # Vers 1 ist nie selbst nummeriert
    start = 0
    for stelle, nummer in sorted(marken):
        ist_sprung = nummer >= letzte_nummer and nummer > letzte_nummer + _UNPLAUSIBLER_SPRUNG
        if ist_sprung:
            continue   # keine Versgrenze, sondern z. B. eine Jahreszahl mitten im Vers – Text läuft weiter
        if nummer < letzte_nummer:
            # Neues Kapitel hat begonnen. Gab es seit Beginn des laufenden Verses eine verworfene Zwischen-
            # überschrift, trennt GENAU sie den unnummerierten Vers 1 vom letzten Vers des alten Kapitels
            # (die ihr am nächsten liegende, falls mehrere – eine frühere gehört zu einem Abschnitt MITTEN
            # im alten Kapitel, siehe Modul-Docstring); ohne eine bleibt die bekannte Lücke.
            kandidat = next((u for u in reversed(ueberschriften) if start <= u <= stelle), None)
            if kandidat is not None:
                stueck = text[start:kandidat].strip()
                if stueck:
                    ergebnisse.append((kapitel, letzte_nummer, stueck))
                kapitel += 1
                stueck = text[kandidat:stelle].strip()
                if stueck:
                    ergebnisse.append((kapitel, 1, stueck))
                letzte_nummer = nummer
                start = stelle
                continue
            stueck = text[start:stelle].strip()
            if stueck:
                ergebnisse.append((kapitel, letzte_nummer, stueck))
            kapitel += 1
            letzte_nummer = nummer
            start = stelle
            continue
        stueck = text[start:stelle].strip()
        if stueck:
            ergebnisse.append((kapitel, letzte_nummer, stueck))
        letzte_nummer = nummer
        start = stelle
    rest = text[start:].strip()
    if rest:
        ergebnisse.append((kapitel, letzte_nummer, rest))
    return ergebnisse


class PyMuPdfVerseExtractor(VerseExtractor):
    def buch_verse(self, pdf_bytes: bytes, von_seite: int, bis_seite: int | None) -> list[tuple[int, int, str]]:
        """`von_seite`/`bis_seite` sind 1-basierte PDF-Seiten (bis_seite inklusive, None = bis zum Ende)."""
        dokument = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        ende = bis_seite if bis_seite is not None else len(dokument)
        seiten_zeilen = [_seite_lesen(dokument[i]) for i in range(von_seite - 1, min(ende, len(dokument)))]
        text, marken, ueberschriften = _buchtext_bauen(seiten_zeilen)
        verse = _verse_aus_marken(text, marken, ueberschriften)
        # Ein übersprungenes Fußnotenzeichen lässt manchmal zwei Leerzeichen stehen (eins davor, eins danach).
        return [(k, v, re.sub(r" {2,}", " ", t)) for k, v, t in verse]
