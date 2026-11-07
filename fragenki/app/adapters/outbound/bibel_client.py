"""Ausgehender Adapter: holt sich den Verstext eines Kapitels direkt vom Bibel-Dienst (nicht über den Kern,
der Login verlangt – wie der Ollama-Aufruf ein direkter Dienst-zu-Dienst-Aufruf im Docker-Netz, BIBEL_URL
z. B. http://bibel:8000). Dienste teilen keine Datenbank, nur ihre öffentliche API. Gleiches Muster wie beim
schnelllesen-Dienst (siehe dessen app/adapters/outbound/bibel_client.py)."""
import httpx

from app.application.ports import BibelQuelle

TIMEOUT_SECONDS = 10.0


class HttpBibelQuelle(BibelQuelle):
    def __init__(self, base_url: str, timeout: float = TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def kapitel(self, buch_kurz: str, kapitel: int) -> str:
        r = httpx.get(f"{self.base_url}/api/kapitel", params={"buch": buch_kurz, "nummer": kapitel},
                       timeout=self.timeout)
        r.raise_for_status()
        verse = r.json().get("verse", [])
        return " ".join(v["text"] for v in verse)


class NullBibelQuelle(BibelQuelle):
    """Kein Bibel-Dienst eingerichtet (BIBEL_URL fehlt): es gibt dann nie Text für Fragen-Vorschläge."""
    def kapitel(self, buch_kurz: str, kapitel: int) -> str:
        raise RuntimeError("Kein Bibel-Dienst eingerichtet (BIBEL_URL fehlt).")
