"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import logging
import os
import threading
import time
from pathlib import Path

from app.adapters.inbound.api import create_app
from app.adapters.outbound.http_gateway import HttpServiceGateway, parse_services
from app.adapters.outbound.json_account_repository import JsonAccountRepository
from app.adapters.outbound.json_repository import JsonSubjectRepository
from app.adapters.outbound.memory_session_store import MemorySessionStore
from app.application.auth_service import AuthService
from app.application.services import SubjectService

log = logging.getLogger("kern")

data_dir = Path(os.getenv("DATA_FILE") or Path(__file__).resolve().parents[1] / "data" / "subjects.json").parent
data_file = data_dir / "subjects.json"
accounts_file = data_dir / "accounts.json"
# Fest eingetragene Dienste (Name=URL, mit Komma getrennt). Weitere Dienste melden sich selbst an (POST /api/registry).
services = parse_services(os.getenv("SERVICES", ""))

gateway = HttpServiceGateway(services, registry_file=data_dir / "registry.json")
subjects = SubjectService(JsonSubjectRepository(data_file), gateway)
auth = AuthService(JsonAccountRepository(accounts_file), MemorySessionStore())
app = create_app(subjects, auth)


def _sync_when_services_are_up(tries: int = 20, pause: float = 3.0) -> None:
    """Beim Start laufen die Dienste oft noch hoch: abgleichen, bis alle die Fächer kennen."""
    for _ in range(tries):
        result = subjects.sync()
        if all(result.values()):  # (auch bei leerem Verzeichnis: dann ist nichts zu tun)
            log.info("Alle Dienste kennen die Fächer: %s", result)
            return
        time.sleep(pause)
    log.warning("Abgleich unvollständig, später POST /api/sync aufrufen: %s", result)


threading.Thread(target=_sync_when_services_are_up, daemon=True).start()
