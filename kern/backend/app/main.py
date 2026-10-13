"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import logging
import os
import threading
import time
from pathlib import Path

from app.adapters.inbound.api import create_app
from app.adapters.outbound.http_gateway import HttpServiceGateway, parse_services
from app.adapters.outbound.json_repository import JsonSubjectRepository
from app.application.services import SubjectService

log = logging.getLogger("kern")

data_file = Path(os.getenv("DATA_FILE") or Path(__file__).resolve().parents[1] / "data" / "subjects.json")
# Fest eingetragene Dienste (Name=URL, mit Komma getrennt). Weitere Dienste melden sich selbst an (POST /api/registry).
services = parse_services(os.getenv("SERVICES", ""))

gateway = HttpServiceGateway(services, registry_file=data_file.parent / "registry.json")
subjects = SubjectService(JsonSubjectRepository(data_file), gateway)
app = create_app(subjects)


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
