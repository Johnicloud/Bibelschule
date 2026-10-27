"""Ausgehender Adapter: Text aus PDF (pypdf), Word .docx (document.xml) und Pages (eingebettete Preview.pdf)."""
import io
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader

from app.application.ports import DateiLeser
from app.domain.druckbogen import Textstueck
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


def _pdf_stuecke(inhalt: bytes) -> list[Textstueck]:
    stuecke: list[Textstueck] = []
    try:
        reader = PdfReader(io.BytesIO(inhalt))
        for nummer, seite in enumerate(reader.pages):
            def besuche(text, cm, tm, _font, groesse, nummer=nummer):
                if not text.strip():
                    return
                x = cm[0] * tm[4] + cm[2] * tm[5] + cm[4]
                y = cm[1] * tm[4] + cm[3] * tm[5] + cm[5]
                stuecke.append(Textstueck(nummer, x, y, abs((groesse or 0) * tm[3] * cm[3]) or abs(groesse or 0), text))
            seite.extract_text(visitor_text=besuche)
    except Exception as e:
        raise InvalidInput("Die PDF-Datei ließ sich nicht lesen.") from e
    return stuecke


BILD_ENDUNGEN = ("png", "jpg", "jpeg")


def _bild_zeilen(inhalt: bytes, endung: str) -> list[str]:
    """Text aus einem Bild (z. B. Bildschirmfoto einer Fragenliste) per Tesseract, lokal im Container."""
    with tempfile.TemporaryDirectory() as ordner:
        bild = Path(ordner) / f"bild.{endung}"
        bild.write_bytes(inhalt)
        try:
            lauf = subprocess.run(["tesseract", str(bild), "stdout", "-l", "deu", "--psm", "6"],
                                  capture_output=True, text=True, timeout=300)
        except FileNotFoundError as e:
            raise InvalidInput("Die Texterkennung (tesseract) ist auf diesem Rechner nicht installiert.") from e
        except subprocess.TimeoutExpired as e:
            raise InvalidInput("Die Texterkennung hat zu lange gedauert.") from e
        if lauf.returncode != 0:
            raise InvalidInput("Das Bild ließ sich nicht lesen.")
        return lauf.stdout.splitlines()


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
        if endung in BILD_ENDUNGEN:
            return _bild_zeilen(inhalt, endung)
        if endung == "pages":
            pdf = _pages_pdf(inhalt)
            if pdf is None:
                raise InvalidInput("In dieser Pages-Datei steckt keine lesbare Vorschau. In Pages „Ablage > Exportieren > Word“ oder PDF wählen.")
            return _pdf_zeilen(pdf)
        raise InvalidInput("Nur PDF, Word (.docx), Pages und Bilder (PNG, JPG) lassen sich nach Fragen durchsuchen.")

    def hat_text(self, dateiname: str, inhalt: bytes) -> bool:
        if _endung(dateiname) != "pdf":
            return False
        try:
            seiten = PdfReader(io.BytesIO(inhalt)).pages
            return any(len((seiten[i].extract_text() or "").strip()) > 40 for i in range(min(5, len(seiten))))
        except Exception:
            return False

    def textstuecke(self, dateiname: str, inhalt: bytes) -> list[Textstueck]:
        endung = _endung(dateiname)
        if endung == "pdf":
            return _pdf_stuecke(inhalt)
        if endung == "pages":
            pdf = _pages_pdf(inhalt)
            return _pdf_stuecke(pdf) if pdf else []
        return []

    def pdf_vorschau(self, dateiname: str, inhalt: bytes) -> bytes | None:
        return _pages_pdf(inhalt) if _endung(dateiname) == "pages" else None
