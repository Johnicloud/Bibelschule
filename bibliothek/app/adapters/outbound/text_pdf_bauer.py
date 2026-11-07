"""Ausgehender Adapter: legt den von der KI erkannten Text als UNSICHTBARE Textebene über die ursprünglichen
Seiten (reportlab-Overlay + pypdf-Merge, dieselbe Technik wie beim pdfcreator-Dienst). Das Bild bleibt genau
wie im Original sichtbar, die PDF wird aber durchsuchbar und der Text kopierbar – echte OCR-Software setzt
die unsichtbaren Wörter zusätzlich exakt über ihre Bildposition, das bräuchte Wortkoordinaten von der KI
(hat ein Sprachmodell nicht); hier reicht eine einfache Textebene oben auf der Seite für Volltextsuche."""
import io

from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

from app.application.ports import TextPdfBauer

FONT, FONT_SIZE = "Helvetica", 10
RAND = 20


class ReportlabTextPdfBauer(TextPdfBauer):
    def baue(self, original_pdf: bytes, text_je_seite: list[str]) -> bytes:
        reader = PdfReader(io.BytesIO(original_pdf))
        schreiber = PdfWriter()
        for i, seite in enumerate(reader.pages):
            box = seite.mediabox
            breite, hoehe = float(box.width), float(box.height)
            text = text_je_seite[i] if i < len(text_je_seite) else ""
            if text:
                overlay = self._overlay(text, breite, hoehe)
                seite.merge_page(overlay)
            schreiber.add_page(seite)
        ausgabe = io.BytesIO()
        schreiber.write(ausgabe)
        return ausgabe.getvalue()

    def _overlay(self, text: str, breite: float, hoehe: float):
        puffer = io.BytesIO()
        c = canvas.Canvas(puffer, pagesize=(breite, hoehe))
        zeilen = simpleSplit(text, FONT, FONT_SIZE, max(breite - 2 * RAND, 10))
        textobjekt = c.beginText(RAND, hoehe - RAND)
        textobjekt.setFont(FONT, FONT_SIZE)
        textobjekt.setTextRenderMode(3)   # unsichtbar: nur auswähl-/durchsuchbar, nichts wird gezeichnet
        textobjekt.setLeading(FONT_SIZE * 1.2)
        for zeile in zeilen:
            if textobjekt.getY() < RAND:
                break
            textobjekt.textLine(zeile)
        c.drawText(textobjekt)
        c.save()
        puffer.seek(0)
        return PdfReader(puffer).pages[0]
