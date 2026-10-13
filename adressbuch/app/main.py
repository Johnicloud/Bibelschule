"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import os
import threading
from pathlib import Path

from app.adapters.inbound.api import create_app
from app.adapters.outbound.json_repository import JsonDozentRepository
from app.adapters.outbound.registration import register_with_kern
from app.application.services import DozentService

NAME = "adressbuch"

data_file = Path(os.getenv("DATA_FILE") or Path(__file__).resolve().parents[1] / "data" / "dozenten.json")
kern_url = os.getenv("KERN_URL")                          # z. B. http://kern:8000, dann meldet sich der Dienst selbst an
own_url = os.getenv("SERVICE_URL") or f"http://{NAME}:8000"

repo = JsonDozentRepository(data_file)
app = create_app(DozentService(repo))

if kern_url:
    threading.Thread(target=register_with_kern, args=(kern_url, NAME, own_url), daemon=True).start()
