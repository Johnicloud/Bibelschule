"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import os
import threading
from pathlib import Path

from app.adapters.inbound.api import create_app
from app.adapters.outbound.bibel_client import HttpBibelVerweise, NullBibelVerweise
from app.adapters.outbound.file_repository import FileSystemDateiSpeicher
from app.adapters.outbound.json_repository import JsonPredigtRepository
from app.adapters.outbound.registration import register_with_kern
from app.application.services import PredigtenService

NAME = "predigten"

data_dir = Path(os.getenv("DATA_DIR") or Path(__file__).resolve().parents[1] / "data")
kern_url = os.getenv("KERN_URL")                          # z. B. http://kern:8000, dann meldet sich der Dienst selbst an
own_url = os.getenv("SERVICE_URL") or f"http://{NAME}:8000"
bibel_url = os.getenv("BIBEL_URL")                         # z. B. http://bibel:8000, für Verweise auf Bibelstellen

repo = JsonPredigtRepository(data_dir / "predigten.json")
dateien = FileSystemDateiSpeicher(data_dir / "dateien")
verweise = HttpBibelVerweise(bibel_url) if bibel_url else NullBibelVerweise()
service = PredigtenService(repo, dateien, verweise)
app = create_app(service)

if kern_url:
    threading.Thread(target=register_with_kern, args=(kern_url, NAME, own_url), daemon=True).start()
