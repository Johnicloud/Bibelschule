"""Ausgehender Adapter: Texterkennung für eine gescannte Bibel-PDF ohne eigene Textebene (z. B. ein altes,
in Fraktur gesetztes Faksimile) – nach demselben Muster wie beim Skripte-Dienst (ocrmypdf + Tesseract, läuft
lokal im Container, keine KI-API). Zusätzlich zum modernen Deutsch (`deu`) zwei auf historischen Fraktur-/
Schwabacher-Druck trainierte Sprachdaten aus `tessdata_best` (siehe Dockerfile): `deu_latf` (eigens für
deutschen Fraktur-Text) und `Fraktur` (das allgemeinere Skript-Modell) – `-l deu_latf+Fraktur+deu` lässt
Tesseract alle drei versuchen, da ein Faksimile oft zusätzlich moderne Vor-/Titelseiten in Antiqua hat.

Wie bei der Texterkennung des Skripte-Diensts wird eine ganze (oft über tausend Seiten lange) Bibel in
Stücken erkannt und danach wieder zusammengefügt, damit der Speicherverbrauch nicht von der Seitenzahl abhängt
und ein Fehler nur ein Stück trifft."""
import gc
import io
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.application.ports import Texterkennung
from app.domain.errors import InvalidInput

SPRACHEN = "deu_latf+Fraktur+deu"
GEPRUEFTE_SEITEN = 20            # für die schnelle "braucht es das?"-Prüfung reichen die ersten paar Seiten
MINDEST_ZEICHEN_JE_SEITE = 40    # darunter gilt eine Seite praktisch als textlos (Streuzeichen zählen nicht)
STUECK_SEITEN = 20
PARALLEL = 3                     # Seiten gleichzeitig innerhalb eines Stücks


class OcrmypdfFrakturTexterkennung(Texterkennung):
    def noetig(self, pdf: bytes) -> bool:
        try:
            seiten = PdfReader(io.BytesIO(pdf)).pages[:GEPRUEFTE_SEITEN]
        except Exception:
            return False
        return not any(len((s.extract_text() or "").strip()) > MINDEST_ZEICHEN_JE_SEITE for s in seiten)

    def erkennen(self, pdf: bytes) -> bytes:
        with tempfile.TemporaryDirectory() as ordner:
            ordner = Path(ordner)
            reader = PdfReader(io.BytesIO(pdf))
            seiten = len(reader.pages)
            if seiten <= STUECK_SEITEN:
                (ordner / "ein.pdf").write_bytes(pdf)
                self._ocr(ordner / "ein.pdf", ordner / "aus.pdf")
                return (ordner / "aus.pdf").read_bytes()
            ergebnisse = []
            for nr, start in enumerate(range(0, seiten, STUECK_SEITEN)):
                teil_ein, teil_aus = ordner / f"ein{nr}.pdf", ordner / f"aus{nr}.pdf"
                schreiber = PdfWriter()
                for i in range(start, min(start + STUECK_SEITEN, seiten)):
                    schreiber.add_page(reader.pages[i])
                with teil_ein.open("wb") as f:
                    schreiber.write(f)
                del schreiber
                self._ocr(teil_ein, teil_aus)
                teil_ein.unlink()
                ergebnisse.append(teil_aus)
                gc.collect()
            gesamt = PdfWriter()
            for teil in ergebnisse:
                gesamt.append(str(teil))
            ziel = io.BytesIO()
            gesamt.write(ziel)
            return ziel.getvalue()

    def _ocr(self, ein: Path, aus: Path) -> None:
        try:
            # --deskew / --rotate-pages: alte Scans sind selten ganz gerade eingescannt.
            # --oversample 300: niedrig aufgelöste Scans vor der Erkennung hochrechnen.
            # --optimize 2: Seitenbilder verkleinern (pngquant).
            # --output-type pdf: kein PDF/A über Ghostscript (siehe Skripte-Dienst: hat Umlaute im Text gelöscht).
            lauf = subprocess.run(["ocrmypdf", "--deskew", "--rotate-pages", "--oversample", "300",
                                   "--jobs", str(PARALLEL), "--optimize", "2", "--output-type", "pdf",
                                   "-l", SPRACHEN, str(ein), str(aus)],
                                  capture_output=True, text=True, timeout=60 * 60)
        except FileNotFoundError as e:
            raise InvalidInput("Die Texterkennung (ocrmypdf) ist auf diesem Rechner nicht installiert.") from e
        except subprocess.TimeoutExpired as e:
            raise InvalidInput("Die Texterkennung hat bei einem Stück zu lange gedauert.") from e
        if lauf.returncode != 0 or not aus.exists():
            if lauf.returncode in (-9, 137):
                raise InvalidInput("Die Texterkennung wurde beendet, weil der Arbeitsspeicher nicht reichte (Docker-Speicher erhöhen).")
            letzte = [z.strip() for z in lauf.stderr.strip().splitlines() if z.strip()][-3:]
            raise InvalidInput(f"Die Texterkennung ist fehlgeschlagen (Code {lauf.returncode}): " + " | ".join(letzte or ["unbekannter Fehler"]))
