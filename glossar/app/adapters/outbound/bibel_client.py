"""Ausgehender Adapter: legt Verweise ("art=glossar") direkt beim Bibel-Dienst an/ab (nicht über den Kern, der
Login verlangt – wie bei schnelllesen → HttpBibelQuelle, direkter Dienst-zu-Dienst-Aufruf im Docker-Netz,
BIBEL_URL z. B. http://bibel:8000). Dienste teilen keine Datenbank, nur die öffentliche API."""
import httpx

from app.application.ports import BibelVerweise

TIMEOUT_SECONDS = 10.0
ART = "glossar"


class HttpBibelVerweise(BibelVerweise):
    def __init__(self, base_url: str, timeout: float = TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def anlegen(self, stelle: str, referenz: str, titel: str | None) -> str:
        r = httpx.post(f"{self.base_url}/api/verweise",
                        json={"stelle": stelle, "art": ART, "referenz": referenz, "titel": titel},
                        timeout=self.timeout)
        r.raise_for_status()
        return r.json()["id"]

    def loeschen(self, verweis_id: str) -> None:
        r = httpx.delete(f"{self.base_url}/api/verweise/{verweis_id}", timeout=self.timeout)
        if r.status_code not in (204, 404):
            r.raise_for_status()


class NullBibelVerweise(BibelVerweise):
    """Kein Bibel-Dienst eingerichtet (BIBEL_URL fehlt): es gibt dann nie einen Verweis-Eintrag dort, die
    Bibelstelle selbst bleibt trotzdem am Glossar-Eintrag erhalten (siehe GlossarService)."""
    def anlegen(self, stelle: str, referenz: str, titel: str | None) -> str:
        raise RuntimeError("Kein Bibel-Dienst eingerichtet (BIBEL_URL fehlt).")

    def loeschen(self, verweis_id: str) -> None:
        raise RuntimeError("Kein Bibel-Dienst eingerichtet (BIBEL_URL fehlt).")
