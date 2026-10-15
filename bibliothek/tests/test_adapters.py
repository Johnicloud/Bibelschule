import io

from pypdf import PdfReader
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.adapters.outbound.bild_extraktor import PypdfBildExtraktor
from app.adapters.outbound.text_pdf_bauer import ReportlabTextPdfBauer


def _bild_pdf(seiten: int) -> bytes:
    """Baut eine kleine PDF mit `seiten` Seiten, auf jeder genau ein eingebettetes Bild – wie ein gescanntes Buch."""
    from PIL import Image
    bild_puffer = io.BytesIO()
    Image.new("RGB", (40, 60), color=(200, 200, 200)).save(bild_puffer, format="PNG")
    bild_puffer.seek(0)

    pdf_puffer = io.BytesIO()
    c = canvas.Canvas(pdf_puffer, pagesize=(200, 300))
    for _ in range(seiten):
        c.drawImage(ImageReader(bild_puffer), 0, 0, width=200, height=300)
        c.showPage()
        bild_puffer.seek(0)
    c.save()
    return pdf_puffer.getvalue()


def test_bild_extraktor_findet_ein_bild_je_seite():
    pdf = _bild_pdf(3)
    bilder = PypdfBildExtraktor().seiten_bilder(pdf)
    assert len(bilder) == 3
    assert all(b for b in bilder)   # kein leeres Bild


def test_bild_extraktor_liefert_leeres_bild_fuer_seiten_ohne_bild():
    pdf_puffer = io.BytesIO()
    c = canvas.Canvas(pdf_puffer, pagesize=(200, 300))
    c.drawString(10, 10, "Reiner Text, kein Bild")
    c.showPage()
    c.save()
    bilder = PypdfBildExtraktor().seiten_bilder(pdf_puffer.getvalue())
    assert bilder == [b""]


def test_text_pdf_bauer_fuegt_unsichtbaren_text_hinzu_ohne_seitenzahl_zu_aendern():
    original = _bild_pdf(2)
    ergebnis = ReportlabTextPdfBauer().baue(original, ["Erster Seitentext", "Zweiter Seitentext"])
    reader = PdfReader(io.BytesIO(ergebnis))
    assert len(reader.pages) == 2
    assert "Erster Seitentext" in reader.pages[0].extract_text()
    assert "Zweiter Seitentext" in reader.pages[1].extract_text()


def test_text_pdf_bauer_laesst_seiten_ohne_text_unveraendert():
    original = _bild_pdf(1)
    ergebnis = ReportlabTextPdfBauer().baue(original, [""])
    reader = PdfReader(io.BytesIO(ergebnis))
    assert len(reader.pages) == 1
    assert ergebnis   # trotzdem eine gültige PDF
