import io
import shutil

import pytest
from app.adapters.outbound import texterkennung
from app.adapters.outbound.texterkennung import OcrmypdfTexterkennung
from pypdf import PdfReader


def _pdf(seiten):
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for i in range(seiten):
        c.drawString(50, 780, f"Seite {i + 1}")
        c.showPage()
    c.save()
    return buf.getvalue()


def test_grosses_skript_wird_in_stuecken_erkannt_und_in_der_reihenfolge_zusammengefuegt(monkeypatch):
    monkeypatch.setattr(texterkennung, "STUECK_SEITEN", 3)
    stuecke = []

    def fake_ocr(self, ein, aus):
        stuecke.append(len(PdfReader(str(ein)).pages))
        shutil.copy(ein, aus)

    monkeypatch.setattr(OcrmypdfTexterkennung, "_ocr", fake_ocr)
    ergebnis = OcrmypdfTexterkennung().erkennen(_pdf(8))
    assert stuecke == [3, 3, 2]
    seiten = PdfReader(io.BytesIO(ergebnis)).pages
    assert [s.extract_text().strip() for s in seiten] == [f"Seite {i}" for i in range(1, 9)]


def test_kleines_skript_wird_am_stueck_erkannt(monkeypatch):
    aufrufe = []
    monkeypatch.setattr(OcrmypdfTexterkennung, "_ocr", lambda self, ein, aus: (aufrufe.append(1), shutil.copy(ein, aus)))
    OcrmypdfTexterkennung().erkennen(_pdf(2))
    assert aufrufe == [1]


def test_fehler_in_einem_stueck_bricht_ab_mit_meldung(monkeypatch):
    from app.domain.errors import InvalidInput
    monkeypatch.setattr(texterkennung, "STUECK_SEITEN", 2)

    def kaputt(self, ein, aus):
        raise InvalidInput("zu wenig Speicher")

    monkeypatch.setattr(OcrmypdfTexterkennung, "_ocr", kaputt)
    with pytest.raises(InvalidInput, match="zu wenig Speicher"):
        OcrmypdfTexterkennung().erkennen(_pdf(5))
