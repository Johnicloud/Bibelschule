import tempfile
from pathlib import Path

from app.adapters.outbound.json_account_repository import JsonAccountRepository
from app.domain.models import Account


def repo():
    return JsonAccountRepository(Path(tempfile.mkdtemp()) / "accounts.json")


def test_account_fields_survive_a_save_and_reload():
    r = repo()
    account = Account(username="johannes", password_hash="hash", is_admin=True, vorname="Johannes",
                       nachname="Löwen", gemeinde="EFG Beispielstadt", muss_passwort_aendern=True)
    r.save(account)

    geladen = r.get_by_username("johannes")
    assert geladen.is_admin is True
    assert geladen.vorname == "Johannes" and geladen.nachname == "Löwen" and geladen.gemeinde == "EFG Beispielstadt"
    assert geladen.muss_passwort_aendern is True


def test_account_without_optional_fields_defaults_after_reload():
    r = repo()
    r.save(Account(username="maria", password_hash="hash"))

    geladen = r.get_by_username("maria")
    assert geladen.is_admin is False and geladen.vorname is None and geladen.muss_passwort_aendern is False
