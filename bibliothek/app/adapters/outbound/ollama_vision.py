"""Ausgehender Adapter: ein lokal laufendes Ollama mit einem Vision-Modell (z. B. llama3.2-vision) liest den
Text von einer Seiten-Abbildung ab. Läuft nicht in diesem Compose-Stack, sondern auf dem Mac (wie bei
pdfcreator/aufgabenleser) – großzügiges Zeitlimit, lokale Bildmodelle sind langsam."""
import base64

import httpx

from app.application.ports import OcrKI

TIMEOUT_SECONDS = 180.0
PROMPT = ("Lies den gesamten Text auf diesem Bild einer Buchseite ab und gib NUR den reinen, abgeschriebenen "
          "Text zurück – keine Beschreibung des Bildes, keine Kommentare, keine Markdown-Formatierung, in "
          "der normalen Lesereihenfolge.")


class OllamaOcrKI(OcrKI):
    def __init__(self, base_url: str, model: str, timeout: float = TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def seite_lesen(self, bild: bytes) -> str:
        if not bild:
            return ""
        b64 = base64.b64encode(bild).decode("ascii")
        r = httpx.post(f"{self.base_url}/api/generate",
                        json={"model": self.model, "prompt": PROMPT, "images": [b64], "stream": False},
                        timeout=self.timeout)
        r.raise_for_status()
        return (r.json().get("response") or "").strip()


class NullOcrKI(OcrKI):
    """Kein Ollama eingerichtet (OLLAMA_URL fehlt): Text-Erkennung ist dann einfach nicht verfügbar."""
    def seite_lesen(self, bild: bytes) -> str:
        raise RuntimeError("Keine KI eingerichtet (OLLAMA_URL fehlt).")
