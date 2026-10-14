"""Ausgehender Adapter: baut aus Karten einen PDF-Druckbogen (reportlab, kein Overlay nötig – anders als beim
pdfcreator-Dienst wird hier eine ganz neue PDF-Seite gezeichnet statt eine Vorlage befüllt).

Raster je Bogen: `COLS` x `ROWS` Karten. Je Bogen zwei Seiten im Wechsel (Vorderseiten, dann Rückseiten) –
so liegen aufeinanderfolgende PDF-Seiten beim doppelseitigen Drucken direkt richtig. Die Rückseite ist je
Zeile spaltenverkehrt gezeichnet (Karte oben-links vorne landet oben-rechts hinten), das passt zum
„Wenden an der langen Kante“, der verbreitetsten Standardeinstellung am Drucker."""
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

from app.application.ports import PrintRenderer
from app.domain.models import Card

COLS, ROWS = 2, 4
PAGE_W, PAGE_H = A4
MARGIN = 28
CELL_W = (PAGE_W - 2 * MARGIN) / COLS
CELL_H = (PAGE_H - 2 * MARGIN) / ROWS
FONT, FONT_SIZE, PADDING = "Helvetica", 11, 14


class ReportlabPrintRenderer(PrintRenderer):
    def druckbogen(self, cards: list[Card]) -> bytes:
        puffer = io.BytesIO()
        c = canvas.Canvas(puffer, pagesize=A4)
        for anfang in range(0, len(cards), COLS * ROWS):
            bogen = cards[anfang:anfang + COLS * ROWS]
            self._seite(c, bogen, [card.front for card in bogen], spiegeln=False)
            c.showPage()
            self._seite(c, bogen, [card.back for card in bogen], spiegeln=True)
            c.showPage()
        c.save()
        return puffer.getvalue()

    def _seite(self, c: canvas.Canvas, bogen: list[Card], texte: list[str], spiegeln: bool) -> None:
        for i in range(len(bogen)):
            row, col = divmod(i, COLS)
            zeichen_col = COLS - 1 - col if spiegeln else col
            x = MARGIN + zeichen_col * CELL_W
            y = PAGE_H - MARGIN - (row + 1) * CELL_H
            c.setDash(3, 3)
            c.rect(x, y, CELL_W, CELL_H)
            c.setDash()
            self._text(c, texte[i], x, y)

    def _text(self, c: canvas.Canvas, text: str, x: float, y: float) -> None:
        breite = CELL_W - 2 * PADDING
        zeilen = simpleSplit(text, FONT, FONT_SIZE, breite)
        c.setFont(FONT, FONT_SIZE)
        gesamt_h = len(zeilen) * FONT_SIZE * 1.3
        start_y = y + CELL_H / 2 + gesamt_h / 2 - FONT_SIZE
        for n, zeile in enumerate(zeilen):
            c.drawCentredString(x + CELL_W / 2, start_y - n * FONT_SIZE * 1.3, zeile)
