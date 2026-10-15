"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import os
import threading
from pathlib import Path

from app.adapters.inbound.api import create_app
from app.adapters.outbound.pdf_text import PypdfText
from app.adapters.outbound.piper_tts import PiperTextToSpeech
from app.adapters.outbound.registration import register_with_kern
from app.application.services import VorleseService

NAME = "vorlesen"

# Deutsches Stimmmodell liegt dem Image bei (siehe Dockerfile) – lokal, kostenlos, kein API-Key.
model_path = os.getenv("PIPER_MODEL") or str(Path(__file__).resolve().parents[1] / "stimme" / "de_DE-thorsten-medium.onnx")
kern_url = os.getenv("KERN_URL")                          # z. B. http://kern:8000, dann meldet sich der Dienst selbst an
own_url = os.getenv("SERVICE_URL") or f"http://{NAME}:8000"

app = create_app(VorleseService(PiperTextToSpeech(model_path), PypdfText()))

if kern_url:
    threading.Thread(target=register_with_kern, args=(kern_url, NAME, own_url), daemon=True).start()
