import io

from pypdf import PdfReader
from reportlab.lib.units import mm

from app.adapters.outbound.print_renderer import FORMATE, ReportlabPrintRenderer
from app.domain.models import Card


def _cards(n):
    return [Card(front=f"Frage {i}", back=f"Antwort {i}") for i in range(n)]


def _je_bogen(format):
    r = FORMATE[format]
    return r["cols"] * r["rows"]


def test_one_sheet_makes_two_pages():
    pdf = ReportlabPrintRenderer().druckbogen(_cards(3))
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) == 2   # eine Vorderseite, eine Rückseite


def test_two_sheets_for_more_cards_than_fit_on_one():
    pdf = ReportlabPrintRenderer().druckbogen(_cards(_je_bogen("a7") + 1))
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) == 4   # zwei Bögen, je Vorder- und Rückseite


def test_empty_list_makes_an_empty_but_valid_pdf():
    pdf = ReportlabPrintRenderer().druckbogen([])
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) == 0


def test_cells_are_exactly_a7_by_default():
    a7 = FORMATE["a7"]
    assert a7["cell_w"] == 105 * mm
    assert a7["cell_h"] == 74 * mm
    assert a7["cols"] * a7["rows"] == 8


def test_a8_format_fits_more_cards_per_sheet():
    a8 = FORMATE["a8"]
    assert a8["cell_w"] == 52 * mm
    assert a8["cell_h"] == 74 * mm
    assert a8["cols"] * a8["rows"] == 16

    pdf = ReportlabPrintRenderer().druckbogen(_cards(16), format="a8")
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) == 2   # alle 16 passen auf einen Bogen


def test_unknown_format_falls_back_to_a7():
    pdf = ReportlabPrintRenderer().druckbogen(_cards(1), format="quatsch")
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) == 2


def test_cards_are_numbered_on_front_and_back():
    pdf = ReportlabPrintRenderer().druckbogen(_cards(2))
    reader = PdfReader(io.BytesIO(pdf))
    front_text = reader.pages[0].extract_text()
    back_text = reader.pages[1].extract_text()
    assert "1" in front_text and "2" in front_text
    assert "1" in back_text and "2" in back_text
