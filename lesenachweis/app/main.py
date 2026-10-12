"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import os
from pathlib import Path

from app.adapters.inbound.api import create_app
from app.adapters.outbound.event_publishers import NullPublisher, WebhookPublisher
from app.adapters.outbound.json_repository import JsonReadingRepository
from app.application.services import ReadingService

data_file = Path(os.getenv("DATA_FILE") or Path(__file__).resolve().parents[1] / "data" / "tasks.json")
service_url = os.getenv("EXTERNAL_SERVICE_URL")

repo = JsonReadingRepository(data_file)
events = WebhookPublisher(service_url, os.getenv("EXTERNAL_SERVICE_TOKEN")) if service_url else NullPublisher()
app = create_app(ReadingService(repo, events))
