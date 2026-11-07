"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import os
import threading
from pathlib import Path

from app.adapters.inbound.api import create_app
from app.adapters.outbound.bibel_client import HttpBibelVerweise, NullBibelVerweise
from app.adapters.outbound.json_repository import JsonEintraegeRepository, JsonQuellenRepository
from app.adapters.outbound.registration import register_with_kern
from app.application.services import KommentarService

NAME = "kommentare"

data_dir = Path(os.getenv("DATA_DIR") or Path(__file__).resolve().parents[1] / "data")
bibel_url = os.getenv("BIBEL_URL")
kern_url = os.getenv("KERN_URL")                          # z. B. http://kern:8000, dann meldet sich der Dienst selbst an
own_url = os.getenv("SERVICE_URL") or f"http://{NAME}:8000"

quellen_repo = JsonQuellenRepository(data_dir / "quellen.json")
eintraege_repo = JsonEintraegeRepository(data_dir / "eintraege.json")
verweise = HttpBibelVerweise(bibel_url) if bibel_url else NullBibelVerweise()
app = create_app(KommentarService(quellen_repo, eintraege_repo, verweise))

if kern_url:
    threading.Thread(target=register_with_kern, args=(kern_url, NAME, own_url), daemon=True).start()
