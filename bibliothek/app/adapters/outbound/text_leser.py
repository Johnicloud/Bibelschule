"""Ausgehender Adapter: liest den Text aus einer PDF (pypdf) – für die Volltextsuche über die von
`ReportlabTextPdfBauer` gebaute, durchsuchbare Text-PDF."""
import io

from pypdf import PdfReader

from app.application.ports import TextLeser


class PypdfTextLeser(TextLeser):
    def text(self, pdf: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(pdf))
            return "\n".join(seite.extract_text() or "" for seite in reader.pages)
        except Exception:
            return ""
