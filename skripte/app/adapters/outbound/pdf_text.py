"""Ausgehender Adapter: liest den Text einer PDF-Datei (pypdf), für die Volltextsuche über Skripte."""
import io

from pypdf import PdfReader

from app.application.ports import PdfText


class PypdfText(PdfText):
    def text(self, pdf: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(pdf))
            return "\n".join(seite.extract_text() or "" for seite in reader.pages)
        except Exception:
            return ""
