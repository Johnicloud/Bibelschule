"""Ausgehender Adapter: roher Text einer PDF-Datei (pypdf), wie beim aufgabenleser-Dienst."""
import io

from pypdf import PdfReader

from app.application.ports import PdfText


class PypdfText(PdfText):
    def text_auslesen(self, pdf: bytes) -> str:
        reader = PdfReader(io.BytesIO(pdf))
        return "\n".join(seite.extract_text() or "" for seite in reader.pages).strip()
