import io

from reportlab.pdfgen import canvas

from app.adapters.outbound.pdf_text import PypdfText
from app.domain.bible import find_book


def _seite(c, zeilen: list[str]) -> None:
    y = 800
    for zeile in zeilen:
        c.drawString(50, y, zeile)
        y -= 20
    c.showPage()


def _baue_pdf() -> bytes:
    """Vier Seiten: eine Titelseite ohne eigene Seitenzahl, ein Inhaltsverzeichnis, die Buch-Titelseite
    selbst (auf die es ankommt) und eine Folgeseite mit Seitenzahl – wie im echten Schlachter-PDF, bei dem
    Buch-Titelseiten ihre gedruckte Seitenzahl nicht zeigen (siehe pdf_text.py)."""
    puffer = io.BytesIO()
    c = canvas.Canvas(puffer)
    _seite(c, ["1", "Umschlagseite ohne Bedeutung"])                         # PDF-Seite 1, Druckzahl 1
    _seite(c, ["Inhaltsverzeichnis und Abkürzungen", "Das Buch Jona Jon 5"])  # PDF-Seite 2 (TOC)
    _seite(c, ["Das Buch Jona", "Und das Wort des HERRN erging an Jona."])   # PDF-Seite 3, zeigt KEINE Zahl
    _seite(c, ["6", "Und Jona machte sich auf."])                           # PDF-Seite 4, Druckzahl 6
    c.save()
    return puffer.getvalue()


def test_erkennt_die_titelseite_ohne_eigene_seitenzahl_ueber_die_naechste_seite():
    ergebnis = PypdfText().buchseiten_erkennen(_baue_pdf())
    jona = find_book("Jon")
    assert ergebnis[jona.index] == 3   # PDF-Seite 3 (1-basiert), nicht 1 und nicht 4


def test_ohne_inhaltsverzeichnis_wird_nichts_erkannt():
    puffer = io.BytesIO()
    c = canvas.Canvas(puffer)
    _seite(c, ["Nur ein bisschen Text ohne Verzeichnis."])
    c.save()
    assert PypdfText().buchseiten_erkennen(puffer.getvalue()) == {}
