"""Ausgehender Adapter: baut aus Karten einen PDF-Druckbogen (reportlab, kein Overlay nötig – anders als beim
pdfcreator-Dienst wird hier eine ganz neue PDF-Seite gezeichnet statt eine Vorlage befüllt).

Raster je Bogen: `FORMATE[format]` gibt Spalten/Zeilen und Zellgröße vor – A7 quer (105 x 74 mm, 2x4 Zellen)
oder A8 hoch (52 x 74 mm, 4x4 Zellen), beide füllen eine A4-Seite fast randlos (A4 = 8x A7 = 16x A8). Je
Bogen zwei Seiten im Wechsel (Vorderseiten, dann Rückseiten) – so liegen aufeinanderfolgende PDF-Seiten beim
doppelseitigen Drucken direkt richtig. Die Rückseite ist je Zeile spaltenverkehrt gezeichnet (Karte
oben-links vorne landet oben-rechts hinten), das passt zum „Wenden an der langen Kante“, der verbreitetsten
Standardeinstellung am Drucker. Jede Karte trägt oben links ihre laufende Nummer (auf Vorder- UND
Rückseite dieselbe) – hilft beim Zuschneiden und Sortieren, welche Rückseite zu welcher Vorderseite gehört."""
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

from app.application.ports import PrintRenderer
from app.domain.models import Card

PAGE_W, PAGE_H = A4
FORMATE = {
    "a7": {"cols": 2, "rows": 4, "cell_w": 105 * mm, "cell_h": 74 * mm},
    "a8": {"cols": 4, "rows": 4, "cell_w": 52 * mm, "cell_h": 74 * mm},
}
FONT, FONT_SIZE, PADDING = "Helvetica", 13, 10   # größere Schrift auf Wunsch – mehr Zeilenumbrüche sind in Ordnung
NUMMER_FONT_SIZE = 8


class ReportlabPrintRenderer(PrintRenderer):
    def druckbogen(self, cards: list[Card], format: str = "a7") -> bytes:
        raster = FORMATE.get(format, FORMATE["a7"])
        cols, rows = raster["cols"], raster["rows"]
        cell_w, cell_h = raster["cell_w"], raster["cell_h"]
        margin_x = (PAGE_W - cols * cell_w) / 2
        margin_y = (PAGE_H - rows * cell_h) / 2
        je_bogen = cols * rows

        puffer = io.BytesIO()
        c = canvas.Canvas(puffer, pagesize=A4)
        for anfang in range(0, len(cards), je_bogen):
            bogen = cards[anfang:anfang + je_bogen]
            self._seite(c, bogen, [k.front for k in bogen], anfang, cols, cell_w, cell_h, margin_x, margin_y, spiegeln=False)
            c.showPage()
            self._seite(c, bogen, [k.back for k in bogen], anfang, cols, cell_w, cell_h, margin_x, margin_y, spiegeln=True)
            c.showPage()
        c.save()
        return puffer.getvalue()

    def _seite(self, c: canvas.Canvas, bogen: list[Card], texte: list[str], anfang: int, cols: int,
               cell_w: float, cell_h: float, margin_x: float, margin_y: float, spiegeln: bool) -> None:
        for i in range(len(bogen)):
            row, col = divmod(i, cols)
            zeichen_col = cols - 1 - col if spiegeln else col
            x = margin_x + zeichen_col * cell_w
            y = PAGE_H - margin_y - (row + 1) * cell_h
            c.setDash(3, 3)
            c.rect(x, y, cell_w, cell_h)
            c.setDash()
            self._text(c, texte[i], x, y, cell_w, cell_h)
            self._nummer(c, anfang + i + 1, x, y, cell_h)

    def _text(self, c: canvas.Canvas, text: str, x: float, y: float, cell_w: float, cell_h: float) -> None:
        breite = cell_w - 2 * PADDING
        zeilen = simpleSplit(text, FONT, FONT_SIZE, breite)
        c.setFont(FONT, FONT_SIZE)
        gesamt_h = len(zeilen) * FONT_SIZE * 1.3
        start_y = y + cell_h / 2 + gesamt_h / 2 - FONT_SIZE
        for n, zeile in enumerate(zeilen):
            c.drawCentredString(x + cell_w / 2, start_y - n * FONT_SIZE * 1.3, zeile)

    def _nummer(self, c: canvas.Canvas, nummer: int, x: float, y: float, cell_h: float) -> None:
        c.setFont(FONT, NUMMER_FONT_SIZE)
        c.drawString(x + 4, y + cell_h - NUMMER_FONT_SIZE - 2, str(nummer))
