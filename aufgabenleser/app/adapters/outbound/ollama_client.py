"""Ausgehender Adapter: ein lokal laufendes Ollama (läuft in eigenem Docker auf dem Mac, nicht in diesem
Compose-Stack). Großzügiges Zeitlimit: lokale Modelle auf der CPU/GPU des Mac brauchen deutlich länger als
eine Cloud-API, besonders beim ersten Laden eines Modells. Gleiches Muster wie beim pdfcreator-Dienst."""
import httpx

from app.application.ports import TextKI

TIMEOUT_SECONDS = 180.0


class OllamaClient(TextKI):
    def __init__(self, base_url: str, model: str, timeout: float = TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def frage(self, prompt: str) -> str:
        r = httpx.post(f"{self.base_url}/api/generate",
                        json={"model": self.model, "prompt": prompt, "stream": False},
                        timeout=self.timeout)
        r.raise_for_status()
        return (r.json().get("response") or "").strip()
