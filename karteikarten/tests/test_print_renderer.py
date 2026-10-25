import io

from pypdf import PdfReader
from reportlab.lib.units import mm

from app.adapters.outbound.print_renderer import CELL_H, CELL_W, COLS, ROWS, ReportlabPrintRenderer
from app.domain.models import Card


def _cards(n):
    return [Card(front=f"Frage {i}", back=f"Antwort {i}") for i in range(n)]


def test_one_sheet_makes_two_pages():
    pdf = ReportlabPrintRenderer().druckbogen(_cards(3))
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) == 2   # eine Vorderseite, eine Rückseite


def test_two_sheets_for_more_cards_than_fit_on_one():
    pdf = ReportlabPrintRenderer().druckbogen(_cards(COLS * ROWS + 1))
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) == 4   # zwei Bögen, je Vorder- und Rückseite


def test_empty_list_makes_an_empty_but_valid_pdf():
    pdf = ReportlabPrintRenderer().druckbogen([])
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) == 0


def test_cells_are_exactly_a7():
    assert CELL_W == 105 * mm
    assert CELL_H == 74 * mm
