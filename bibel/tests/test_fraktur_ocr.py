import io
import shutil

import pytest
from app.adapters.outbound import fraktur_ocr
from app.adapters.outbound.fraktur_ocr import OcrmypdfFrakturTexterkennung
from pypdf import PdfReader


def _pdf_ohne_text(seiten: int) -> bytes:
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for _ in range(seiten):
        c.showPage()   # leere Seiten: kein Text, wie ein gescanntes Bild ohne eigene Textebene
    c.save()
    return buf.getvalue()


def _pdf_mit_text(seiten: int) -> bytes:
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for i in range(seiten):
        c.drawString(50, 780, f"Dies ist eine ganz normale Textseite Nummer {i + 1} mit genug Zeichen.")
        c.showPage()
    c.save()
    return buf.getvalue()


def test_noetig_ist_wahr_ohne_textebene():
    assert OcrmypdfFrakturTexterkennung().noetig(_pdf_ohne_text(3)) is True


def test_noetig_ist_falsch_mit_textebene():
    assert OcrmypdfFrakturTexterkennung().noetig(_pdf_mit_text(3)) is False


def test_grosses_dokument_wird_in_stuecken_erkannt_und_in_der_reihenfolge_zusammengefuegt(monkeypatch):
    monkeypatch.setattr(fraktur_ocr, "STUECK_SEITEN", 3)
    stuecke = []

    def fake_ocr(self, ein, aus):
        stuecke.append(len(PdfReader(str(ein)).pages))
        shutil.copy(ein, aus)

    monkeypatch.setattr(OcrmypdfFrakturTexterkennung, "_ocr", fake_ocr)
    OcrmypdfFrakturTexterkennung().erkennen(_pdf_ohne_text(8))
    assert stuecke == [3, 3, 2]


def test_kleines_dokument_wird_am_stueck_erkannt(monkeypatch):
    aufrufe = []
    monkeypatch.setattr(OcrmypdfFrakturTexterkennung, "_ocr",
                        lambda self, ein, aus: (aufrufe.append(1), shutil.copy(ein, aus)))
    OcrmypdfFrakturTexterkennung().erkennen(_pdf_ohne_text(2))
    assert aufrufe == [1]


def test_fehler_in_einem_stueck_bricht_ab_mit_meldung(monkeypatch):
    from app.domain.errors import InvalidInput
    monkeypatch.setattr(fraktur_ocr, "STUECK_SEITEN", 2)

    def kaputt(self, ein, aus):
        raise InvalidInput("zu wenig Speicher")

    monkeypatch.setattr(OcrmypdfFrakturTexterkennung, "_ocr", kaputt)
    with pytest.raises(InvalidInput, match="zu wenig Speicher"):
        OcrmypdfFrakturTexterkennung().erkennen(_pdf_ohne_text(5))
