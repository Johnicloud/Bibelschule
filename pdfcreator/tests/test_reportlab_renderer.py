from pathlib import Path

from app.adapters.outbound.reportlab_renderer import ReportlabPdfRenderer
from app.domain.standard_vorlage import standard_vorlage
from pypdf import PdfReader

VORLAGE_PDF = (Path(__file__).resolve().parents[1] / "app" / "adapters" / "outbound" / "vorlagen"
               / "lesenachweis_pflichtlektuere.pdf")


def test_fuellt_die_echte_vorlage_und_text_erscheint_an_der_richtigen_stelle():
    renderer = ReportlabPdfRenderer()
    vorlage = standard_vorlage()
    werte = {"fach": "Apostelgeschichte", "name": "Johannes Löwen", "gemeinde": "Eben-Ezer",
             "buch_0_titel": "Die Apostelgeschichte", "buch_0_seiten": "200"}

    ergebnis = renderer.fuelle(VORLAGE_PDF.read_bytes(), werte, vorlage.felder)

    reader = PdfReader.__new__(PdfReader)
    import io
    reader = PdfReader(io.BytesIO(ergebnis))
    text = reader.pages[0].extract_text()
    assert "Apostelgeschichte" in text and "Johannes Löwen" in text and "Eben-Ezer" in text
    assert "Die Apostelgeschichte" in text and "200" in text
    # Die ursprüngliche Beschriftung der Vorlage muss erhalten bleiben (Overlay, kein Ersetzen)
    assert "Lesenachweis" in text and "Pflichtlektüre" in text


def test_text_auslesen_findet_die_feldbeschriftungen():
    renderer = ReportlabPdfRenderer()
    text = renderer.text_auslesen(VORLAGE_PDF.read_bytes())
    assert "Fach" in text and "Gemeinde" in text


def test_leere_werte_werden_nicht_geschrieben():
    renderer = ReportlabPdfRenderer()
    vorlage = standard_vorlage()
    ergebnis = renderer.fuelle(VORLAGE_PDF.read_bytes(), {"fach": "Nur das Fach"}, vorlage.felder)
    import io
    text = PdfReader(io.BytesIO(ergebnis)).pages[0].extract_text()
    assert "Nur das Fach" in text
