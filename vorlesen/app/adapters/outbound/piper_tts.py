"""Ausgehender Adapter: vertont Text lokal und kostenlos mit Piper (https://github.com/rhasspy/piper), einer
kleinen, offline laufenden KI-Stimme (kein Cloud-Dienst, kein API-Key, läuft direkt in diesem Container –
das deutsche Stimmmodell liegt dem Image bei, siehe Dockerfile). `piper` wird als eigener Prozess aufgerufen
statt über die Python-Bibliothek, weil sich deren Schnittstelle zwischen Versionen schon geändert hat, die
Kommandozeile aber stabil ist."""
import subprocess
import tempfile
from pathlib import Path

from app.application.ports import TextToSpeech

TIMEOUT_SECONDS = 120.0


class PiperTextToSpeech(TextToSpeech):
    def __init__(self, model_path: str, timeout: float = TIMEOUT_SECONDS):
        self.model_path = model_path
        self.timeout = timeout

    def sprich(self, text: str) -> bytes:
        with tempfile.TemporaryDirectory() as tmp:
            ausgabe = Path(tmp) / "audio.wav"
            ergebnis = subprocess.run(
                ["piper", "--model", self.model_path, "--output_file", str(ausgabe)],
                input=text, capture_output=True, text=True, timeout=self.timeout,
            )
            if ergebnis.returncode != 0 or not ausgabe.exists():
                raise RuntimeError(ergebnis.stderr.strip() or "piper hat kein Audio erzeugt.")
            return ausgabe.read_bytes()
