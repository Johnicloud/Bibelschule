"""Ausgehender Adapter: Sitzungen im Speicher (nicht auf Platte). Ein Neustart des Kerns meldet alle ab;
das ist bewusst so (keine Sitzungs-Datei, die man stehlen könnte).

Automatische Abmeldung nach Inaktivität (wie bei einer Finanz-App): eine Sitzung ohne Aufruf länger als
idle_timeout gilt als abgelaufen. Jeder erfolgreiche Aufruf zählt als Aktivität und schiebt die Frist weiter
(gleitendes Fenster), nicht nur die Anmeldung selbst."""
import secrets
import threading
from datetime import datetime, timedelta, timezone
from typing import Callable

from app.application.ports import SessionStore

IDLE_TIMEOUT = timedelta(minutes=15)


class MemorySessionStore(SessionStore):
    def __init__(self, idle_timeout: timedelta = IDLE_TIMEOUT, now: Callable[[], datetime] = None):
        self.idle_timeout = idle_timeout
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._lock = threading.Lock()
        self._sessions: dict[str, tuple[str, datetime]] = {}   # token -> (account_id, zuletzt aktiv)

    def create(self, account_id: str) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[token] = (account_id, self._now())
        return token

    def account_id_for(self, token: str) -> str | None:
        with self._lock:
            entry = self._sessions.get(token)
            if entry is None:
                return None
            account_id, last_seen = entry
            now = self._now()
            if now - last_seen > self.idle_timeout:
                del self._sessions[token]
                return None
            self._sessions[token] = (account_id, now)
            return account_id

    def delete(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(token, None)

    def delete_for_account(self, account_id: str) -> None:
        with self._lock:
            self._sessions = {t: s for t, s in self._sessions.items() if s[0] != account_id}
