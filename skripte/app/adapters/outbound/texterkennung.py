"""Ausgehender Adapter: Texterkennung mit OCRmyPDF/Tesseract (läuft lokal im Container, keine KI-API nötig).
Legt eine unsichtbare Textebene über die Seitenbilder – das Aussehen bleibt gleich, Text lässt sich markieren."""
import subprocess
import tempfile
from pathlib import Path

from app.application.ports import Texterkennung
from app.domain.errors import InvalidInput

SPRACHE = "deu"
ZEITLIMIT_SEKUNDEN = 4 * 60 * 60     # ein ganzes Skript mit 300-dpi-Hochrechnung braucht über eine Stunde
PARALLEL = 3      # Seiten gleichzeitig: bei 300 dpi und allen Kernen reichten 7,6 GB Arbeitsspeicher nicht (Container wurde beendet)


class OcrmypdfTexterkennung(Texterkennung):
    def erkennen(self, pdf: bytes) -> bytes:
        with tempfile.TemporaryDirectory() as ordner:
            ein, aus = Path(ordner) / "ein.pdf", Path(ordner) / "aus.pdf"
            ein.write_bytes(pdf)
            try:
                # --skip-text: Seiten, die schon Text haben, bleiben unberührt
                # --deskew / --rotate-pages: schiefe oder gedrehte Scans vor dem Erkennen geradeziehen (besserer Text)
                # --optimize 2: Seitenbilder verkleinern (pngquant), ein 149-MB-Skript wird so etwa 60 % kleiner
                # --output-type pdf: kein PDF/A über Ghostscript (das hat bei Text-PDFs Umlaute aus dem Text gelöscht)
                # --oversample 300: Scans mit niedriger Auflösung vor dem Erkennen auf 300 dpi hochrechnen – am Skript fehlten
                # sonst Tabellenzeilen (z. B. „Pfingstpredigt“), mit 300 dpi wurden sie gefunden (356 -> 375 Wörter auf einer Seite)
                lauf = subprocess.run(["ocrmypdf", "--skip-text", "--deskew", "--rotate-pages", "--oversample", "300", "--jobs", str(PARALLEL), "--optimize", "2",
                                       "--output-type", "pdf", "-l", SPRACHE, str(ein), str(aus)],
                                      capture_output=True, text=True, timeout=ZEITLIMIT_SEKUNDEN)
            except FileNotFoundError as e:
                raise InvalidInput("Die Texterkennung (ocrmypdf) ist auf diesem Rechner nicht installiert.") from e
            except subprocess.TimeoutExpired as e:
                raise InvalidInput("Die Texterkennung hat zu lange gedauert.") from e
            if lauf.returncode != 0 or not aus.exists():
                if lauf.returncode in (-9, 137):
                    raise InvalidInput("Die Texterkennung wurde beendet, weil der Arbeitsspeicher nicht reichte (Docker-Speicher erhöhen oder die Datei teilen).")
                letzte = [z.strip() for z in lauf.stderr.strip().splitlines() if z.strip()][-3:]
                raise InvalidInput(f"Die Texterkennung ist fehlgeschlagen (Code {lauf.returncode}): " + " | ".join(letzte or ["unbekannter Fehler"]))
            return aus.read_bytes()
