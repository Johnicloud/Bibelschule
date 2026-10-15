"""Ausgehender Adapter: erkennt beim Hochladen automatisch, auf welcher PDF-Seite jedes Bibelbuch beginnt.

Zwei Schritte, beide rein aus dem Text der PDF (pypdf, kein OCR):
1. Jede Seite trägt am Anfang ihre gedruckte Seitenzahl (Kopfzeile, z. B. "183" oder bei einer Doppelseite
   "482 483") – daraus eine Zuordnung gedruckte Seitenzahl -> PDF-Seite.
2. Ein Inhaltsverzeichnis („Inhaltsverzeichnis und Abkürzungen der Bücher des Alten/Neuen Testaments“) listet
   je Buch Name, Kurzname und gedruckte Seitenzahl – daraus mit Schritt 1 die PDF-Seite je Buch.
Das ist ein Vorschlag, kein Versprechen: Bücher, die sich nicht finden lassen (z. B. weil eine Ausgabe anders
aufgebaut ist oder kein Inhaltsverzeichnis hat), bleiben leer und werden von Hand eingetragen."""
import bisect
import io
import re

from pypdf import PdfReader

from app.application.ports import PdfText
from app.domain.bible import BOOKS

_TOC_KEYWORD = "inhaltsverzeichnis"
_DRUCKZAHL_KOPF = re.compile(r"\d{1,4}")
_MAX_ABSTAND = 5   # Buch-Titelseiten zeigen oft keine eigene Seitenzahl – auf höchstens so viele Seiten schätzen


def _nahestes(bekannt: list[tuple[int, int]], gesucht: int) -> int | None:
    """Nächstgelegene bekannte gedruckte Seitenzahl zu `gesucht`, hochgerechnet auf die PDF-Seite (1 gedruckte
    Seite = 1 PDF-Seite in der Nähe) – für Titelseiten, die selbst keine Seitenzahl zeigen (siehe Modul-Docstring)."""
    zahlen = [z for z, _ in bekannt]
    i = bisect.bisect_left(zahlen, gesucht)
    kandidaten = [bekannt[j] for j in (i - 1, i) if 0 <= j < len(bekannt)]
    if not kandidaten:
        return None
    zahl, pdf_seite = min(kandidaten, key=lambda kv: abs(kv[0] - gesucht))
    if abs(zahl - gesucht) > _MAX_ABSTAND:
        return None
    return pdf_seite - (zahl - gesucht)


class PypdfText(PdfText):
    def buchseiten_erkennen(self, pdf: bytes) -> dict[int, int]:
        seiten = [(p.extract_text() or "") for p in PdfReader(io.BytesIO(pdf)).pages]

        seite_bei_druckzahl: dict[int, int] = {}
        for i, text in enumerate(seiten):
            kopfzeile = text.lstrip().split("\n", 1)[0]
            for zahl in _DRUCKZAHL_KOPF.findall(kopfzeile):
                seite_bei_druckzahl.setdefault(int(zahl), i + 1)   # erste Fundstelle gewinnt, PDF-Seite 1-basiert
        bekannt_sortiert = sorted(seite_bei_druckzahl.items())

        ergebnis: dict[int, int] = {}
        for text in seiten:
            if _TOC_KEYWORD not in text.lower():
                continue
            for zeile in text.split("\n"):
                zeile = zeile.strip()
                for buch in BOOKS:
                    if buch.index in ergebnis:
                        continue
                    # Das Inhaltsverzeichnis nennt nicht immer den Kurznamen nach Lutherbibel (`buch.short`),
                    # manche Ausgaben nehmen eine der bekannten Schreibweisen (`buch.aliases`) – alle versuchen.
                    for variante in (buch.short, *buch.aliases):
                        treffer = re.search(rf"(?:^|\s){re.escape(variante)}\s+(\d{{1,4}})\s*$", zeile)
                        if treffer:
                            druckzahl = int(treffer.group(1))
                            pdf_seite = seite_bei_druckzahl.get(druckzahl) or _nahestes(bekannt_sortiert, druckzahl)
                            if pdf_seite:
                                ergebnis[buch.index] = pdf_seite
                            break
        return ergebnis
