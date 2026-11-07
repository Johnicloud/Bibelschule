"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import os
import threading
from pathlib import Path

from app.adapters.inbound.api import create_app
from app.adapters.outbound.bild_extraktor import PypdfBildExtraktor
from app.adapters.outbound.file_repository import FileSystemDateiSpeicher
from app.adapters.outbound.json_repository import JsonBuchRepository
from app.adapters.outbound.ollama_vision import NullOcrKI, OllamaOcrKI
from app.adapters.outbound.registration import register_with_kern
from app.adapters.outbound.text_pdf_bauer import ReportlabTextPdfBauer
from app.application.services import BibliothekService

NAME = "bibliothek"

data_dir = Path(os.getenv("DATA_DIR") or Path(__file__).resolve().parents[1] / "data")
kern_url = os.getenv("KERN_URL")                          # z. B. http://kern:8000, dann meldet sich der Dienst selbst an
own_url = os.getenv("SERVICE_URL") or f"http://{NAME}:8000"
# Ollama läuft nicht in diesem Compose-Stack, sondern lokal auf dem Mac (eigenes Docker), wie bei pdfcreator/
# aufgabenleser. Für die Text-Erkennung braucht es ein Vision-Modell (Bildverständnis), darum ein eigener
# Modell-Name statt des Text-Modells der anderen Dienste – ohne OLLAMA_URL gibt es einfach keine Text-Erkennung.
ollama_url = os.getenv("OLLAMA_URL")
ollama_vision_model = os.getenv("OLLAMA_VISION_MODEL", "llama3.2-vision")

repo = JsonBuchRepository(data_dir / "buecher.json")
dateien = FileSystemDateiSpeicher(data_dir / "dateien")
ocr = OllamaOcrKI(ollama_url, ollama_vision_model) if ollama_url else NullOcrKI()
service = BibliothekService(repo, dateien, PypdfBildExtraktor(), ocr, ReportlabTextPdfBauer())
app = create_app(service)

if kern_url:
    threading.Thread(target=register_with_kern, args=(kern_url, NAME, own_url), daemon=True).start()
