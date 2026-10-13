"""Ausgehender Adapter: Sitzungen im Speicher (nicht auf Platte). Ein Neustart des Kerns meldet alle ab;
das ist bewusst so (keine Sitzungs-Datei, die man stehlen könnte)."""
import secrets
import threading

from app.application.ports import SessionStore


class MemorySessionStore(SessionStore):
    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: dict[str, str] = {}

    def create(self, account_id: str) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[token] = account_id
        return token

    def account_id_for(self, token: str) -> str | None:
        with self._lock:
            return self._sessions.get(token)

    def delete(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(token, None)
