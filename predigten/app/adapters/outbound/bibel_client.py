"""Ausgehender Adapter: legt einen Verweis auf eine Bibelstelle direkt beim Bibel-Dienst an bzw. entfernt ihn
wieder (nicht über den Kern, der Login verlangt – wie der Kapitel-Abruf bei schnelllesen ein direkter
Dienst-zu-Dienst-Aufruf im Docker-Netz, BIBEL_URL z. B. http://bibel:8000). Dienste teilen keine Datenbank,
nur ihre öffentliche API. Fehler (Bibel-Dienst offline o. Ä.) brechen das Anlegen/Bearbeiten/Löschen einer
Predigt nie ab – der Verweis ist eine Zusatzleistung, kein Pflichtteil (wie der Ollama-Aufruf bei pdfcreator)."""
import logging

import httpx

from app.application.ports import BibelVerweise

log = logging.getLogger(__name__)
TIMEOUT_SECONDS = 10.0
ART = "predigt"


class HttpBibelVerweise(BibelVerweise):
    def __init__(self, base_url: str, timeout: float = TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def anlegen(self, stelle: str, referenz: str) -> str | None:
        try:
            r = httpx.post(f"{self.base_url}/api/verweise",
                           json={"stelle": stelle, "art": ART, "referenz": referenz},
                           timeout=self.timeout)
            r.raise_for_status()
            return r.json()["id"]
        except Exception as e:
            log.warning("Verweis bei %s konnte nicht angelegt werden: %s", stelle, e)
            return None

    def loeschen(self, verweis_id: str) -> None:
        try:
            httpx.delete(f"{self.base_url}/api/verweise/{verweis_id}", timeout=self.timeout)
        except Exception as e:
            log.warning("Verweis %s konnte nicht gelöscht werden: %s", verweis_id, e)


class NullBibelVerweise(BibelVerweise):
    """Kein Bibel-Dienst eingerichtet (BIBEL_URL fehlt): es gibt dann nie einen Verweis, die Bibelstelle
    bleibt trotzdem an der Predigt gespeichert."""
    def anlegen(self, stelle: str, referenz: str) -> str | None:
        return None

    def loeschen(self, verweis_id: str) -> None:
        pass
