"""Ausgehender Adapter: lädt Matthew Henrys "Commentary on the Whole Bible" (gemeinfrei, CC Public Domain
Mark) von der HelloAO Bible API (https://bible.helloao.org) – fertige, saubere JSON-Daten je Kapitel, kein
eigenes Parsen von HTML oder einem SWORD-Modul nötig (anders als die ursprünglich erwogene CCEL-HTML- oder
SWORD-Route). Englisch (siehe Projektnotizen: die App ist sonst deutschsprachig) – `Quelle.sprache = "en"`,
von der Oberfläche entsprechend markiert.

Die Kommentar-Einträge je Kapitel sind lückenhaft: Henry kommentiert oft mehrere Verse zusammen unter EINER
Überschrift, manche Verse ganz ohne eigenen Eintrag (laut API insgesamt nur rund 4100 von gut 31000 Versen
der ganzen Bibel). Ein Eintrag mit `number=n` deckt darum alle Verse bis (ausschließlich) zum nächsten
Eintrag im selben Kapitel ab; der LETZTE Eintrag eines Kapitels deckt vorsichtshalber nur seinen eigenen Vers
ab, nicht automatisch bis zum Kapitelende – die wirkliche letzte Versnummer des Kapitels ist von hier aus
nicht bekannt, und lieber zu wenig als zu viel Abdeckung behaupten."""
import time

import httpx

from app.domain.bible import BOOKS

BASIS_URL = "https://bible.helloao.org/api/c/matthew-henry"
TIMEOUT_SEKUNDEN = 20.0
WARTEZEIT_ZWISCHEN_AUFRUFEN = 0.15   # Rücksicht auf die kostenlose API, kein Limit dort veröffentlicht

# USFM-Kurzcodes (Standard in der Bible-Software-Welt), in derselben Reihenfolge wie BOOKS (domain/bible.py).
_USFM = ["GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT", "1SA", "2SA", "1KI", "2KI", "1CH", "2CH",
         "EZR", "NEH", "EST", "JOB", "PSA", "PRO", "ECC", "SNG", "ISA", "JER", "LAM", "EZK", "DAN", "HOS",
         "JOL", "AMO", "OBA", "JON", "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL", "MAT", "MRK", "LUK",
         "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT",
         "PHM", "HEB", "JAS", "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV"]


def usfm(buch_index: int) -> str:
    return _USFM[buch_index]


class HelloAoKlient:
    """Holt die Kommentar-Antwort für ein Kapitel; None, wenn es dafür keinen Eintrag gibt (404)."""
    def __init__(self, timeout: float = TIMEOUT_SEKUNDEN):
        self.timeout = timeout

    def kapitel(self, buch_usfm: str, kapitel: int) -> dict | None:
        r = httpx.get(f"{BASIS_URL}/{buch_usfm}/{kapitel}.json", timeout=self.timeout)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()


def eintraege_aus_kapitel(kapitel_json: dict) -> list[tuple[int, int, str]]:
    """[(vers_von, vers_bis, text), ...] aus der Antwort von `HelloAoKlient.kapitel()` – siehe Modul-Docstring
    für die Regel, wie weit ein Eintrag reicht."""
    eintraege = [e for e in kapitel_json.get("chapter", {}).get("content", []) if e.get("type") == "verse"]
    ergebnisse = []
    for i, e in enumerate(eintraege):
        von = e["number"]
        bis = eintraege[i + 1]["number"] - 1 if i + 1 < len(eintraege) else von
        text = "\n".join(e.get("content", [])).strip()
        if text:
            ergebnisse.append((von, bis, text))
    return ergebnisse


def alle_eintraege(klient: HelloAoKlient, buecher: list[int] | None = None,
                   wartezeit: float = WARTEZEIT_ZWISCHEN_AUFRUFEN) -> list[tuple[str, int, int, int, str]]:
    """Lädt alle Kapitel der angegebenen Bücher (Standard: alle 66) und liefert
    [(buch_kurz, kapitel, vers_von, vers_bis, text), ...] – fertig für `KommentarService.import_ersetzen`."""
    ziel_buecher = buecher if buecher is not None else range(len(BOOKS))
    ergebnisse = []
    for buch_index in ziel_buecher:
        buch = BOOKS[buch_index]
        for kapitel in range(1, buch.chapters + 1):
            daten = klient.kapitel(usfm(buch_index), kapitel)
            if wartezeit:
                time.sleep(wartezeit)
            if daten is None:
                continue
            for von, bis, text in eintraege_aus_kapitel(daten):
                ergebnisse.append((buch.short, kapitel, von, bis, text))
    return ergebnisse
