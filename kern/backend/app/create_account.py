"""Legt ein Admin-Konto an. Läuft innerhalb des Containers, Aufruf über ../neues-konto.sh im Projektordner.
Wer Shell-Zugriff auf den Container hat, hat ohnehin schon vollen Zugriff auf die Daten – darum immer Admin;
weitere, nicht-Admin-Konten legt ein Admin bequemer über die Oberfläche an."""
import os
import sys
from pathlib import Path

from app.adapters.outbound.json_account_repository import JsonAccountRepository
from app.adapters.outbound.memory_session_store import MemorySessionStore
from app.application.auth_service import AuthService
from app.domain.errors import InvalidInput


def main() -> None:
    if len(sys.argv) != 3:
        print("Nutzung: python -m app.create_account <benutzername> <passwort>")
        raise SystemExit(1)
    username, password = sys.argv[1], sys.argv[2]

    data_dir = Path(os.getenv("DATA_FILE") or Path(__file__).resolve().parents[1] / "data" / "subjects.json").parent
    auth = AuthService(JsonAccountRepository(data_dir / "accounts.json"), MemorySessionStore())
    try:
        account = auth.create_account(username, password, is_admin=True)
    except InvalidInput as e:
        print(f"Fehler: {e}")
        raise SystemExit(1)
    print(f"Admin-Konto „{account.username}“ angelegt.")


if __name__ == "__main__":
    main()
