"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import os
import threading

from app.adapters.inbound.api import create_app
from app.adapters.outbound.ollama_client import OllamaClient
from app.adapters.outbound.pdf_text import PypdfText
from app.adapters.outbound.registration import register_with_kern
from app.application.services import AufgabenLeseService

NAME = "aufgabenleser"

kern_url = os.getenv("KERN_URL")                          # z. B. http://kern:8000, dann meldet sich der Dienst selbst an
own_url = os.getenv("SERVICE_URL") or f"http://{NAME}:8000"
# Ollama läuft nicht in diesem Compose-Stack, sondern lokal auf dem Mac (eigenes Docker). Ohne OLLAMA_URL
# gibt es keine Aufgaben-Vorschläge (siehe AufgabenLeseService: dann schlägt /api/lesen mit 422 fehl).
ollama_url = os.getenv("OLLAMA_URL")
ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")

ki = OllamaClient(ollama_url, ollama_model) if ollama_url else None
app = create_app(AufgabenLeseService(PypdfText(), ki))

if kern_url:
    threading.Thread(target=register_with_kern, args=(kern_url, NAME, own_url), daemon=True).start()
