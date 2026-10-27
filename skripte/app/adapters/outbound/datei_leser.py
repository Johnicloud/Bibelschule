"""Ausgehender Adapter: Text aus PDF (pypdf), Word .docx (document.xml) und Pages (eingebettete Preview.pdf)."""
import io
import zipfile
from xml.etree import ElementTree

from pypdf import PdfReader

from app.application.ports import DateiLeser
from app.domain.errors import InvalidInput

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _endung(dateiname: str) -> str:
    return dateiname.rsplit(".", 1)[-1].lower() if "." in dateiname else ""


def _pdf_zeilen(inhalt: bytes) -> list[str]:
    try:
        reader = PdfReader(io.BytesIO(inhalt))
        return "\n".join((seite.extract_text() or "") for seite in reader.pages).splitlines()
    except Exception as e:
        raise InvalidInput("Die PDF-Datei ließ sich nicht lesen.") from e


def _docx_absaetze(inhalt: bytes) -> list[str]:
    try:
        with zipfile.ZipFile(io.BytesIO(inhalt)) as z:
            wurzel = ElementTree.fromstring(z.read("word/document.xml"))
    except Exception as e:
        raise InvalidInput("Die Word-Datei ließ sich nicht lesen (nur .docx, nicht das alte .doc).") from e
    return ["".join(t.text or "" for t in p.iter(f"{W}t")) for p in wurzel.iter(f"{W}p")]


def _pages_pdf(inhalt: bytes) -> bytes | None:
    try:
        with zipfile.ZipFile(io.BytesIO(inhalt)) as z:
            name = next((n for n in z.namelist() if n.lower().endswith("quicklook/preview.pdf")), None)
            return z.read(name) if name else None
    except zipfile.BadZipFile:
        return None


class DateiLeserAdapter(DateiLeser):
    def zeilen(self, dateiname: str, inhalt: bytes) -> list[str]:
        endung = _endung(dateiname)
        if endung == "pdf":
            return _pdf_zeilen(inhalt)
        if endung == "docx":
            return _docx_absaetze(inhalt)
        if endung == "pages":
            pdf = _pages_pdf(inhalt)
            if pdf is None:
                raise InvalidInput("In dieser Pages-Datei steckt keine lesbare Vorschau. In Pages „Ablage > Exportieren > Word“ oder PDF wählen.")
            return _pdf_zeilen(pdf)
        raise InvalidInput("Nur PDF, Word (.docx) und Pages lassen sich nach Fragen durchsuchen.")

    def pdf_vorschau(self, dateiname: str, inhalt: bytes) -> bytes | None:
        return _pages_pdf(inhalt) if _endung(dateiname) == "pages" else None
