import io
import zipfile

import pytest
from app.adapters.outbound.datei_leser import DateiLeserAdapter
from app.application.services import SkriptService
from app.domain.errors import InvalidInput
from app.domain.fragen import fragen_erkennen
from tests.test_service import InMemoryDateien, InMemoryRepo


def test_nummerierte_fragen_mit_zeilenumbruch_und_trennung():
    zeilen = ["1. Nenne und begründe die Zeit.", "1. Schreibe den Vers auf.", "2. Welchen Zeitraum erfasst",
              "die Apostelgeschichte?", "10.Woran erkennt man die Ver-", "folgung?"]
    assert fragen_erkennen(zeilen) == ["Nenne und begründe die Zeit.", "Schreibe den Vers auf.",
                                       "Welchen Zeitraum erfasst die Apostelgeschichte?", "Woran erkennt man die Verfolgung?"]


def test_ohne_nummern_ist_jeder_absatz_eine_frage_und_ligaturen_werden_repariert():
    assert fragen_erkennen(["﻿﻿Was ist Oﬀenbarung?", "", "Wer war Paulus?"]) == ["Was ist Offenbarung?", "Wer war Paulus?"]


def test_bibelstelle_mit_zahl_am_zeilenanfang_ist_keine_neue_frage():
    zeilen = ["1. Was kennzeichnete das Leben nach Apg", "2,42-47 aus?", "2. Wer war Petrus?"]
    assert fragen_erkennen(zeilen) == ["Was kennzeichnete das Leben nach Apg 2,42-47 aus?", "Wer war Petrus?"]


def _docx(absaetze):
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    body = "".join(f"<w:p><w:r><w:t>{a}</w:t></w:r></w:p>" for a in absaetze)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", f'<w:document xmlns:w="{w}"><w:body>{body}</w:body></w:document>')
    return buf.getvalue()


def _pdf(text):
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for i, zeile in enumerate(text):
        c.drawString(50, 780 - i * 20, zeile)
    c.save()
    return buf.getvalue()


@pytest.fixture
def svc():
    return SkriptService(InMemoryRepo(), InMemoryDateien(), DateiLeserAdapter())


def test_docx_fragen(svc):
    s = svc.upload("f", "Fragen.docx", None, _docx(["Wer war Petrus?", "Wo lebte Paulus?"]))
    assert svc.fragen(s.id) == ["Wer war Petrus?", "Wo lebte Paulus?"]


def test_pdf_fragen(svc):
    s = svc.upload("f", "Fragen.pdf", None, _pdf(["1. Wer war Petrus?", "2. Wo lebte Paulus?"]))
    assert svc.fragen(s.id) == ["Wer war Petrus?", "Wo lebte Paulus?"]


def test_pages_nutzt_die_eingebettete_vorschau(svc):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("QuickLook/Preview.pdf", _pdf(["1. Wer war Petrus?", "2. Wo lebte Paulus?"]))
    s = svc.upload("f", "Fragen.pages", None, buf.getvalue())
    assert svc.fragen(s.id) == ["Wer war Petrus?", "Wo lebte Paulus?"]
    assert svc.vorschau_pdf(s.id).startswith(b"%PDF")


def test_pages_ohne_vorschau_wird_klar_abgelehnt(svc):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("Index/Document.iwa", b"x")
    s = svc.upload("f", "Fragen.pages", None, buf.getvalue())
    with pytest.raises(InvalidInput):
        svc.fragen(s.id)


def test_unbekanntes_format_wird_abgelehnt(svc):
    s = svc.upload("f", "bild.png", None, b"x")
    with pytest.raises(InvalidInput):
        svc.fragen(s.id)


class FakeOcr:
    def erkennen(self, pdf): return b"%PDF-MIT-TEXT"


def test_texterkennung_ersetzt_die_anzeige_aber_nicht_das_original():
    svc = SkriptService(InMemoryRepo(), InMemoryDateien(), DateiLeserAdapter(), FakeOcr())
    s = svc.upload("f", "Skript.pdf", None, b"%PDF-SCAN")
    assert svc.text_status(s.id)["status"] == "keine"
    svc.text_erkennen_starten(s.id, im_hintergrund=False)
    assert svc.text_status(s.id)["status"] == "fertig"
    assert svc.datei(s.id)[1] == b"%PDF-MIT-TEXT"
    assert svc.datei(s.id, original=True)[1] == b"%PDF-SCAN"
    svc.delete(s.id)
    assert not svc.dateien.vorhanden(s.id + ".text")


def test_texterkennung_nur_fuer_pdf_und_fehler_werden_gemeldet():
    class Kaputt:
        def erkennen(self, pdf): raise RuntimeError("boom")
    svc = SkriptService(InMemoryRepo(), InMemoryDateien(), DateiLeserAdapter(), Kaputt())
    w = svc.upload("f", "Fragen.docx", None, b"x")
    with pytest.raises(InvalidInput):
        svc.text_erkennen_starten(w.id, im_hintergrund=False)
    p = svc.upload("f", "Skript.pdf", None, b"x")
    svc.text_erkennen_starten(p.id, im_hintergrund=False)
    assert svc.text_status(p.id)["status"] == "fehler"


def _druckbogen(fronten, rueckseiten_gespiegelt=True):
    """Baut einen Druckbogen wie der Renderer der Karteikarten: 2 Spalten, Rückseite je Zeile spaltenverkehrt."""
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(595, 842))
    zell_b, zell_h = 297.5, 210.5
    for seite, nutz in ((0, "front"), (1, "back")):
        for i, (f, a) in enumerate(fronten):
            zeile, spalte = divmod(i, 2)
            if nutz == "back":
                spalte = 1 - spalte
            x, y = spalte * zell_b, 842 - (zeile + 1) * zell_h
            c.setFont("Helvetica", 8); c.drawString(x + 4, y + zell_h - 10, str(i + 1))
            c.setFont("Helvetica", 13)
            text = f if nutz == "front" else a
            for n, zl in enumerate(text.split("|")):
                c.drawCentredString(x + zell_b / 2, y + zell_h / 2 - n * 17, zl)
        c.showPage()
    c.save()
    return buf.getvalue()


def test_druckbogen_liefert_fragen_mit_antworten(svc):
    karten = [("Wer war Petrus?", "Ein Apostel"), ("Wo lebte Paulus?", "In Tarsus|und Antiochia"), ("Was ist Gnade?", "Unverdient"),
              ("Wer schrieb Apg?", "Lukas")]
    s = svc.upload("f", "bogen.pdf", None, _druckbogen(karten))
    erg = svc.karten(s.id)
    assert erg["quelle"] == "druckbogen"
    assert [(k["frage"], k["antwort"]) for k in erg["karten"]] == [
        ("Wer war Petrus?", "Ein Apostel"), ("Wo lebte Paulus?", "In Tarsus und Antiochia"),
        ("Was ist Gnade?", "Unverdient"), ("Wer schrieb Apg?", "Lukas")]


def test_fragenliste_ist_kein_druckbogen_und_kommt_ohne_antworten(svc):
    s = svc.upload("f", "Fragen.docx", None, _docx(["Wer war Petrus?", "Wo lebte Paulus?"]))
    erg = svc.karten(s.id)
    assert erg["quelle"] == "fragenliste"
    assert [k["antwort"] for k in erg["karten"]] == ["", ""]


def test_pdf_mit_text_braucht_keine_erkennung_und_wird_im_original_gelesen(svc):
    svc = SkriptService(svc.repo, svc.dateien, DateiLeserAdapter(), FakeOcr())
    s = svc.upload("f", "Fragen.pdf", None, _pdf(["1. Nenne und begründe die Jünger.", "2. Schlüsselvers?"]))
    with pytest.raises(InvalidInput):
        svc.text_erkennen_starten(s.id, im_hintergrund=False)
    svc.dateien.speichere(s.id + ".text", b"%PDF-ohne-umlaute")      # selbst eine alte Textfassung stört nicht
    assert svc.fragen(s.id) == ["Nenne und begründe die Jünger.", "Schlüsselvers?"]


def test_unsichtbare_zeichen_im_dateinamen_werden_entfernt(svc):
    s = svc.upload("f", "‎localhost:8170:x.pdf", None, b"x")
    assert s.dateiname == "localhost:8170:x.pdf"


def test_umbenennen_behaelt_die_endung_und_bereinigt(svc):
    s = svc.upload("f", "alt.docx", None, b"x")
    assert svc.umbenennen(s.id, "  Neuer ‎Name ").dateiname == "Neuer Name.docx"
    assert svc.umbenennen(s.id, "Anderer.DOCX").dateiname == "Anderer.DOCX"
    assert svc.umbenennen(s.id, "a/b").dateiname == "a-b.DOCX"   # Endung des aktuellen Namens
    with pytest.raises(InvalidInput):
        svc.umbenennen(s.id, " ‎ ")
