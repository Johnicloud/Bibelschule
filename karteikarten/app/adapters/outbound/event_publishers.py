"""Ausgehende Adapter für den Port EventPublisher (Schnittstelle zu einem übergeordneten Service)."""
import json
import logging
import threading
import urllib.request
from datetime import datetime, timezone

from app.application.ports import EventPublisher

log = logging.getLogger(__name__)


class NullPublisher(EventPublisher):
    """Standard: kein externer Service konfiguriert."""
    def publish(self, event: str, payload: dict) -> None:
        pass


class WebhookPublisher(EventPublisher):
    """Schickt jedes Ereignis als JSON per POST an eine URL (im Hintergrund, Fehler blockieren nichts)."""
    def __init__(self, url: str, token: str | None = None, timeout: float = 5):
        self.url, self.token, self.timeout = url, token, timeout

    def publish(self, event: str, payload: dict) -> None:
        body = json.dumps({
            "event": event,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        }).encode("utf-8")
        threading.Thread(target=self._send, args=(body,), daemon=True).start()

    def _send(self, body: bytes) -> None:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            req = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
            urllib.request.urlopen(req, timeout=self.timeout).close()
        except Exception as e:  # der Lernbetrieb darf nie am externen Service hängen
            log.warning("Externer Service nicht erreichbar: %s", e)
