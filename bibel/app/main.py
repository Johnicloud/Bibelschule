"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import os
import threading
from pathlib import Path

from app.adapters.inbound.api import create_app
from app.adapters.outbound.file_repository import FileSystemDateiSpeicher
from app.adapters.outbound.json_repository import JsonIndexRepository, JsonVersRepository
from app.adapters.outbound.pdf_text import PypdfText
from app.adapters.outbound.registration import register_with_kern
from app.adapters.outbound.verse_extractor import PypdfVerseExtractor
from app.application.services import BibelService

NAME = "bibel"

data_dir = Path(os.getenv("DATA_DIR") or Path(__file__).resolve().parents[1] / "data")
kern_url = os.getenv("KERN_URL")                          # z. B. http://kern:8000, dann meldet sich der Dienst selbst an
own_url = os.getenv("SERVICE_URL") or f"http://{NAME}:8000"

index_repo = JsonIndexRepository(data_dir / "index.json")
verse_repo = JsonVersRepository(data_dir / "verse.json")
dateien = FileSystemDateiSpeicher(data_dir / "bibel.pdf")
service = BibelService(index_repo, dateien, PypdfText(), verse_repo, PypdfVerseExtractor())
app = create_app(service)

if kern_url:
    threading.Thread(target=register_with_kern, args=(kern_url, NAME, own_url), daemon=True).start()
