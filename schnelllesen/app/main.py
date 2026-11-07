"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import os
import threading
from pathlib import Path

from app.adapters.inbound.api import create_app
from app.adapters.outbound.bibel_client import HttpBibelQuelle, NullBibelQuelle
from app.adapters.outbound.json_repository import JsonEinheitRepository
from app.adapters.outbound.registration import register_with_kern
from app.application.services import SchnelllesenService

NAME = "schnelllesen"

data_file = Path(os.getenv("DATA_FILE") or Path(__file__).resolve().parents[1] / "data" / "einheiten.json")
kern_url = os.getenv("KERN_URL")                          # z. B. http://kern:8000, dann meldet sich der Dienst selbst an
own_url = os.getenv("SERVICE_URL") or f"http://{NAME}:8000"
# Der Bibel-Dienst läuft im selben Docker-Netz, direkter Aufruf statt über den Kern (der Login verlangt).
bibel_url = os.getenv("BIBEL_URL")

repo = JsonEinheitRepository(data_file)
bibel = HttpBibelQuelle(bibel_url) if bibel_url else NullBibelQuelle()
app = create_app(SchnelllesenService(repo, bibel))

if kern_url:
    threading.Thread(target=register_with_kern, args=(kern_url, NAME, own_url), daemon=True).start()
