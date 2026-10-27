"""Ausgehender Adapter: Texterkennung mit OCRmyPDF/Tesseract (läuft lokal im Container, keine KI-API nötig).
Legt eine unsichtbare Textebene über die Seitenbilder – das Aussehen bleibt gleich, Text lässt sich markieren."""
import subprocess
import tempfile
from pathlib import Path

from app.application.ports import Texterkennung
from app.domain.errors import InvalidInput

SPRACHE = "deu"
ZEITLIMIT_SEKUNDEN = 60 * 60


class OcrmypdfTexterkennung(Texterkennung):
    def erkennen(self, pdf: bytes) -> bytes:
        with tempfile.TemporaryDirectory() as ordner:
            ein, aus = Path(ordner) / "ein.pdf", Path(ordner) / "aus.pdf"
            ein.write_bytes(pdf)
            try:
                # --skip-text: Seiten, die schon Text haben, bleiben unberührt; --optimize 0: Bilder nicht neu komprimieren
                lauf = subprocess.run(["ocrmypdf", "--skip-text", "--optimize", "0", "-l", SPRACHE, str(ein), str(aus)],
                                      capture_output=True, text=True, timeout=ZEITLIMIT_SEKUNDEN)
            except FileNotFoundError as e:
                raise InvalidInput("Die Texterkennung (ocrmypdf) ist auf diesem Rechner nicht installiert.") from e
            except subprocess.TimeoutExpired as e:
                raise InvalidInput("Die Texterkennung hat zu lange gedauert.") from e
            if lauf.returncode != 0 or not aus.exists():
                raise InvalidInput("Die Texterkennung ist fehlgeschlagen: " + (lauf.stderr.strip().splitlines() or ["unbekannter Fehler"])[-1])
            return aus.read_bytes()
