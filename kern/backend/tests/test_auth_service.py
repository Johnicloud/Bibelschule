import pytest
from app.application.auth_service import AuthService
from app.application.ports import AccountRepository, SessionStore
from app.domain.errors import InvalidInput, Unauthorized


class InMemoryAccounts(AccountRepository):
    def __init__(self): self.d = {}
    def list(self): return list(self.d.values())
    def get_by_username(self, u): return next((a for a in self.d.values() if a.username == u), None)
    def save(self, a): self.d[a.id] = a


class InMemorySessions(SessionStore):
    def __init__(self): self.d = {}
    def create(self, account_id):
        token = f"token-{len(self.d)}"
        self.d[token] = account_id
        return token
    def account_id_for(self, token): return self.d.get(token)
    def delete(self, token): self.d.pop(token, None)


@pytest.fixture
def svc():
    return AuthService(InMemoryAccounts(), InMemorySessions())


def test_create_account_and_login(svc):
    account = svc.create_account("johannes", "geheim123")
    token = svc.login("johannes", "geheim123")
    found = svc.current_account(token)
    assert found.id == account.id and found.username == "johannes"


def test_create_account_rejects_duplicate_username(svc):
    svc.create_account("johannes", "geheim123")
    with pytest.raises(InvalidInput):
        svc.create_account("johannes", "anderes")


def test_create_account_requires_username_and_password(svc):
    with pytest.raises(InvalidInput):
        svc.create_account(" ", "geheim123")
    with pytest.raises(InvalidInput):
        svc.create_account("johannes", "kurz")


def test_login_rejects_wrong_password_or_unknown_user(svc):
    svc.create_account("johannes", "geheim123")
    with pytest.raises(Unauthorized):
        svc.login("johannes", "falsch")
    with pytest.raises(Unauthorized):
        svc.login("gibtesnicht", "geheim123")


def test_logout_invalidates_the_session(svc):
    svc.create_account("johannes", "geheim123")
    token = svc.login("johannes", "geheim123")
    svc.logout(token)
    assert svc.current_account(token) is None


def test_current_account_without_or_unknown_token(svc):
    assert svc.current_account(None) is None
    assert svc.current_account("gibt-es-nicht") is None
