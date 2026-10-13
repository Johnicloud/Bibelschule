"""Anwendungsfälle rund um Konten und Anmeldung. Kennt nur Domäne und Ports.
Konten legt man per Skript an (./neues-konto.sh), es gibt keine Selbstregistrierung über die API."""
from app.application.ports import AccountRepository, SessionStore
from app.domain.auth import hash_password, verify_password
from app.domain.errors import InvalidInput, Unauthorized
from app.domain.models import Account

MIN_PASSWORD_LENGTH = 8


class AuthService:
    def __init__(self, accounts: AccountRepository, sessions: SessionStore):
        self.accounts = accounts
        self.sessions = sessions

    def create_account(self, username: str, password: str) -> Account:
        username = (username or "").strip()
        if not username:
            raise InvalidInput("Der Benutzername darf nicht leer sein.")
        if len(password or "") < MIN_PASSWORD_LENGTH:
            raise InvalidInput(f"Das Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen haben.")
        if self.accounts.get_by_username(username):
            raise InvalidInput("Diesen Benutzernamen gibt es schon.")
        account = Account(username=username, password_hash=hash_password(password))
        self.accounts.save(account)
        return account

    def login(self, username: str, password: str) -> str:
        account = self.accounts.get_by_username((username or "").strip())
        if account is None or not verify_password(password or "", account.password_hash):
            raise Unauthorized("Benutzername oder Passwort falsch.")
        return self.sessions.create(account.id)

    def logout(self, token: str) -> None:
        self.sessions.delete(token)

    def current_account(self, token: str | None) -> Account | None:
        if not token:
            return None
        account_id = self.sessions.account_id_for(token)
        if not account_id:
            return None
        return next((a for a in self.accounts.list() if a.id == account_id), None)
