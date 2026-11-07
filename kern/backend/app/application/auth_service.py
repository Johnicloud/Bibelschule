"""Anwendungsfälle rund um Konten und Anmeldung. Kennt nur Domäne und Ports.
Neue Konten legt entweder ./neues-konto.sh an oder ein schon angemeldetes Konto über die Oberfläche
(„Benutzer verwalten“) – nie ein Fremder ohne Anmeldung."""
import secrets

from app.application.ports import AccountRepository, SessionStore
from app.domain.auth import hash_password, verify_password
from app.domain.errors import InvalidInput, NotFound, Unauthorized
from app.domain.models import Account

MIN_PASSWORD_LENGTH = 8


class AuthService:
    def __init__(self, accounts: AccountRepository, sessions: SessionStore):
        self.accounts = accounts
        self.sessions = sessions

    def create_account(self, username: str, password: str, is_admin: bool = False) -> Account:
        username = (username or "").strip()
        if not username:
            raise InvalidInput("Der Benutzername darf nicht leer sein.")
        if len(password or "") < MIN_PASSWORD_LENGTH:
            raise InvalidInput(f"Das Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen haben.")
        if self.accounts.get_by_username(username):
            raise InvalidInput("Diesen Benutzernamen gibt es schon.")
        account = Account(username=username, password_hash=hash_password(password), is_admin=is_admin)
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

    def list_accounts(self) -> list[Account]:
        return self.accounts.list()

    def change_password(self, account_id: str, old_password: str, new_password: str) -> None:
        account = next((a for a in self.accounts.list() if a.id == account_id), None)
        if account is None or not verify_password(old_password or "", account.password_hash):
            raise Unauthorized("Das bisherige Passwort ist falsch.")
        if len(new_password or "") < MIN_PASSWORD_LENGTH:
            raise InvalidInput(f"Das neue Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen haben.")
        account.password_hash = hash_password(new_password)
        account.muss_passwort_aendern = False   # eigenes Passwort gewählt: ein Admin-Reset ist damit erledigt
        self.accounts.save(account)

    def set_is_admin(self, username: str, is_admin: bool) -> Account:
        """Der letzte Admin kann sein Admin-Recht nicht verlieren – sonst könnte niemand mehr Konten verwalten."""
        account = self.accounts.get_by_username(username)
        if account is None:
            raise NotFound("Dieses Konto gibt es nicht.")
        if account.is_admin and not is_admin:
            admins = [a for a in self.accounts.list() if a.is_admin]
            if len(admins) <= 1:
                raise InvalidInput("Der letzte Admin kann sein Admin-Recht nicht abgeben.")
        account.is_admin = is_admin
        self.accounts.save(account)
        return account

    def reset_password(self, username: str) -> str:
        """Ein Admin setzt für ein anderes Konto ein neues, zufälliges Passwort – das Konto wird überall
        abgemeldet (delete_for_account) und muss beim nächsten Anmelden selbst ein eigenes Passwort wählen
        (muss_passwort_aendern), damit der Admin das endgültige Passwort nie kennt."""
        account = self.accounts.get_by_username(username)
        if account is None:
            raise NotFound("Dieses Konto gibt es nicht.")
        temp_password = secrets.token_urlsafe(9)
        account.password_hash = hash_password(temp_password)
        account.muss_passwort_aendern = True
        self.accounts.save(account)
        self.sessions.delete_for_account(account.id)
        return temp_password

    def update_profile(self, account_id: str, vorname: str, nachname: str, gemeinde: str) -> Account:
        account = next((a for a in self.accounts.list() if a.id == account_id), None)
        if account is None:
            raise Unauthorized("Bitte anmelden.")
        account.vorname = (vorname or "").strip() or None
        account.nachname = (nachname or "").strip() or None
        account.gemeinde = (gemeinde or "").strip() or None
        self.accounts.save(account)
        return account
