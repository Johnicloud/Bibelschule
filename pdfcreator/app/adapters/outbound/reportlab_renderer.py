"""Ausgehender Adapter: schreibt Text per reportlab auf eine Overlay-Seite und legt sie mit pypdf über die
Vorlage. Liest auch den reinen Text einer PDF (für den KI-Vorschlag bei neuen Vorlagen)."""
import io

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from app.application.ports import PdfRenderer
from app.domain.models import Feld


class ReportlabPdfRenderer(PdfRenderer):
    def fuelle(self, vorlage_pdf: bytes, werte: dict[str, str], felder: list[Feld]) -> bytes:
        reader = PdfReader(io.BytesIO(vorlage_pdf))
        schreiber = PdfWriter()

        # Je Seite ein Overlay mit genau den Feldern, die auf diese Seite gehören.
        for seiten_index, seite in enumerate(reader.pages):
            box = seite.mediabox
            puffer = io.BytesIO()
            c = canvas.Canvas(puffer, pagesize=(float(box.width), float(box.height)))
            for feld in felder:
                if feld.seite != seiten_index:
                    continue
                text = werte.get(feld.schluessel, "")
                if text:
                    c.setFont("Helvetica", feld.groesse)
                    c.drawString(feld.x, feld.y, text)
            c.save()
            puffer.seek(0)
            overlay_seite = PdfReader(puffer).pages[0]
            seite.merge_page(overlay_seite)
            schreiber.add_page(seite)

        ausgabe = io.BytesIO()
        schreiber.write(ausgabe)
        return ausgabe.getvalue()

    def text_auslesen(self, pdf: bytes) -> str:
        reader = PdfReader(io.BytesIO(pdf))
        return "\n".join(seite.extract_text() or "" for seite in reader.pages).strip()
