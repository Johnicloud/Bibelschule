"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import os
import threading
from pathlib import Path

from app.adapters.inbound.api import create_app
from app.adapters.outbound.event_publishers import NullPublisher, WebhookPublisher
from app.adapters.outbound.json_repository import JsonItemRepository
from app.adapters.outbound.registration import register_with_kern
from app.application.services import ItemService

NAME = "__NAME__"

data_file = Path(os.getenv("DATA_FILE") or Path(__file__).resolve().parents[1] / "data" / "items.json")
service_url = os.getenv("EXTERNAL_SERVICE_URL")
kern_url = os.getenv("KERN_URL")                          # z. B. http://kern:8000, dann meldet sich der Dienst selbst an
own_url = os.getenv("SERVICE_URL") or f"http://{NAME}:8000"

repo = JsonItemRepository(data_file)
events = WebhookPublisher(service_url, os.getenv("EXTERNAL_SERVICE_TOKEN")) if service_url else NullPublisher()
app = create_app(ItemService(repo, events))

if kern_url:
    threading.Thread(target=register_with_kern, args=(kern_url, NAME, own_url), daemon=True).start()
