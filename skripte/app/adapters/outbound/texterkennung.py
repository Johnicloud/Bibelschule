"""Ausgehender Adapter: Texterkennung mit OCRmyPDF/Tesseract (läuft lokal im Container, keine KI-API nötig).
Legt eine unsichtbare Textebene über die Seitenbilder – das Aussehen bleibt gleich, Text lässt sich markieren.

Große Skripte werden in Stücken zu je STUECK_SEITEN Seiten erkannt und danach wieder zusammengefügt: ein ganzes Skript auf
einmal (135 Seiten, 300 dpi) brauchte mehr Arbeitsspeicher, als Docker hergab, und der Container wurde beendet. So bleibt der
Verbrauch gleich, egal wie dick das Skript ist, und ein Fehler trifft nur ein Stück."""
import gc
import io
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.application.ports import Texterkennung
from app.domain.errors import InvalidInput

SPRACHE = "deu"
ZEITLIMIT_SEKUNDEN = 4 * 60 * 60     # für das Ganze; ein einzelnes Stück bekommt davon höchstens eine Stunde
STUECK_SEITEN = 20
PARALLEL = 3      # Seiten gleichzeitig innerhalb eines Stücks


class OcrmypdfTexterkennung(Texterkennung):
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
            # --skip-text: Seiten, die schon Text haben, bleiben unberührt
            # --deskew / --rotate-pages: schiefe oder gedrehte Scans vor dem Erkennen geradeziehen (besserer Text)
            # --optimize 2: Seitenbilder verkleinern (pngquant), ein 149-MB-Skript wird so etwa 60 % kleiner
            # --output-type pdf: kein PDF/A über Ghostscript (das hat bei Text-PDFs Umlaute aus dem Text gelöscht)
            # --oversample 300: Scans mit niedriger Auflösung auf 300 dpi hochrechnen – sonst fehlten Tabellenzeilen
            lauf = subprocess.run(["ocrmypdf", "--skip-text", "--deskew", "--rotate-pages", "--oversample", "300",
                                   "--jobs", str(PARALLEL), "--optimize", "2", "--output-type", "pdf", "-l", SPRACHE, str(ein), str(aus)],
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
