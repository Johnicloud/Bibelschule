"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import os
import threading
from pathlib import Path

from app.adapters.inbound.api import create_app
from app.adapters.outbound.bild_wandler import PillowBildWandler
from app.adapters.outbound.datei_leser import DateiLeserAdapter
from app.adapters.outbound.file_repository import FileSystemDateiSpeicher
from app.adapters.outbound.json_repository import JsonSkriptRepository
from app.adapters.outbound.texterkennung import OcrmypdfTexterkennung
from app.adapters.outbound.registration import register_with_kern
from app.application.services import SkriptService

NAME = "skripte"

data_dir = Path(os.getenv("DATA_DIR") or Path(__file__).resolve().parents[1] / "data")
kern_url = os.getenv("KERN_URL")                          # z. B. http://kern:8000, dann meldet sich der Dienst selbst an
own_url = os.getenv("SERVICE_URL") or f"http://{NAME}:8000"

repo = JsonSkriptRepository(data_dir / "skripte.json")
dateien = FileSystemDateiSpeicher(data_dir / "dateien")
app = create_app(SkriptService(repo, dateien, DateiLeserAdapter(), OcrmypdfTexterkennung(), PillowBildWandler()))

if kern_url:
    threading.Thread(target=register_with_kern, args=(kern_url, NAME, own_url), daemon=True).start()
