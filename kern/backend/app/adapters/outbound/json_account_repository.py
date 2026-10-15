"""Ausgehender Adapter: speichert Konten in einer JSON-Datei (atomar, mit täglicher Sicherung).
Gespeichert wird nur der Passwort-Hash (siehe domain/auth.py), nie das Passwort selbst."""
import json
import threading
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.application.ports import AccountRepository
from app.domain.models import Account


class JsonAccountRepository(AccountRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Account]:
        if not self.path.exists():
            return {}
        return {d["id"]: Account(id=d["id"], username=d["username"], password_hash=d["password_hash"],
                                  is_admin=d.get("is_admin", False), vorname=d.get("vorname"),
                                  nachname=d.get("nachname"), gemeinde=d.get("gemeinde"),
                                  muss_passwort_aendern=d.get("muss_passwort_aendern", False))
                for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, accounts: dict[str, Account]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps(
            [{"id": a.id, "username": a.username, "password_hash": a.password_hash, "is_admin": a.is_admin,
              "vorname": a.vorname, "nachname": a.nachname, "gemeinde": a.gemeinde,
              "muss_passwort_aendern": a.muss_passwort_aendern}
             for a in accounts.values()],
            ensure_ascii=False, indent=2))

    def list(self) -> list[Account]:
        with self._lock:
            return list(self._read().values())

    def get_by_username(self, username: str) -> Account | None:
        with self._lock:
            return next((a for a in self._read().values() if a.username == username), None)

    def save(self, account: Account) -> None:
        with self._lock:
            accounts = self._read()
            accounts[account.id] = account
            self._write(accounts)
