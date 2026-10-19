"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import os
import threading

from app.adapters.inbound.api import create_app
from app.adapters.outbound.bibel_client import HttpBibelQuelle, NullBibelQuelle
from app.adapters.outbound.ollama_client import OllamaClient
from app.adapters.outbound.registration import register_with_kern
from app.application.services import FragenKiService

NAME = "fragenki"

kern_url = os.getenv("KERN_URL")                          # z. B. http://kern:8000, dann meldet sich der Dienst selbst an
own_url = os.getenv("SERVICE_URL") or f"http://{NAME}:8000"
# Ollama läuft nicht in diesem Compose-Stack, sondern lokal auf dem Mac (eigenes Docker). Ohne OLLAMA_URL
# gibt es keine Fragen-Vorschläge (siehe FragenKiService: dann schlägt /api/generieren mit 422 fehl).
ollama_url = os.getenv("OLLAMA_URL")
ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
# Der Bibel-Dienst läuft im selben Docker-Netz, direkter Aufruf statt über den Kern (der Login verlangt).
bibel_url = os.getenv("BIBEL_URL")

ki = OllamaClient(ollama_url, ollama_model) if ollama_url else None
bibel = HttpBibelQuelle(bibel_url) if bibel_url else NullBibelQuelle()
app = create_app(FragenKiService(bibel, ki))

if kern_url:
    threading.Thread(target=register_with_kern, args=(kern_url, NAME, own_url), daemon=True).start()
