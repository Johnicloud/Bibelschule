"""Ausgehender Adapter: meldet einen Kommentar als Verweis beim Bibel-Dienst an (direkter Dienst-zu-Dienst-
Aufruf im Docker-Netz, BIBEL_URL, wie bei schnelllesen → HttpBibelQuelle). Dienste teilen keine Datenbank,
nur die öffentliche API des Bibel-Diensts."""
import logging

import httpx

from app.application.ports import BibelVerweise
from app.domain.errors import InvalidInput

log = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10.0
ART = "kommentar"


class HttpBibelVerweise(BibelVerweise):
    def __init__(self, base_url: str, timeout: float = TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def anlegen(self, stelle: str, referenz: str, titel: str | None) -> str | None:
        try:
            r = httpx.post(f"{self.base_url}/api/verweise",
                           json={"stelle": stelle, "art": ART, "referenz": referenz, "titel": titel},
                           timeout=self.timeout)
        except httpx.HTTPError as e:
            log.warning("Bibel-Dienst nicht erreichbar, Kommentar bleibt ohne Verweis: %s", e)
            return None
        if r.status_code == 422:
            # Der Bibel-Dienst prüft die Stelle selbst (parse_stelle) – dessen Fehlermeldung durchreichen.
            raise InvalidInput(r.json().get("detail") or "Die Bibelstelle ist ungültig.")
        r.raise_for_status()
        return r.json()["id"]

    def loeschen(self, verweis_id: str) -> None:
        try:
            httpx.delete(f"{self.base_url}/api/verweise/{verweis_id}", timeout=self.timeout)
        except httpx.HTTPError as e:
            log.warning("Bibel-Dienst nicht erreichbar, Verweis bleibt dort stehen: %s", e)


class NullBibelVerweise(BibelVerweise):
    """Kein Bibel-Dienst eingerichtet (BIBEL_URL fehlt): Kommentare werden gespeichert, aber nie als
    Verweis angemeldet."""
    def anlegen(self, stelle: str, referenz: str, titel: str | None) -> str | None:
        return None

    def loeschen(self, verweis_id: str) -> None:
        pass
