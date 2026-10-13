"""Kompositionswurzel: hier werden Adapter und Anwendung verdrahtet."""
import os
import threading
from pathlib import Path

from app.adapters.inbound.api import create_app
from app.adapters.outbound.file_repository import FileSystemDateiSpeicher
from app.adapters.outbound.json_repository import JsonVorlageRepository
from app.adapters.outbound.ollama_client import NullTextKI, OllamaClient
from app.adapters.outbound.registration import register_with_kern
from app.adapters.outbound.reportlab_renderer import ReportlabPdfRenderer
from app.application.services import PdfService
from app.domain.standard_vorlage import STANDARD_VORLAGE_ID, standard_vorlage

NAME = "pdfcreator"

data_dir = Path(os.getenv("DATA_DIR") or Path(__file__).resolve().parents[1] / "data")
kern_url = os.getenv("KERN_URL")                          # z. B. http://kern:8000, dann meldet sich der Dienst selbst an
own_url = os.getenv("SERVICE_URL") or f"http://{NAME}:8000"
# Ollama läuft nicht in diesem Compose-Stack, sondern lokal auf dem Mac (eigenes Docker). Ohne OLLAMA_URL
# gibt es für neu hochgeladene Vorlagen einfach keinen KI-Vorschlag (siehe NullTextKI).
ollama_url = os.getenv("OLLAMA_URL")
ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")

vorlagen = JsonVorlageRepository(data_dir / "vorlagen.json")
dateien = FileSystemDateiSpeicher(data_dir / "dateien")
ki = OllamaClient(ollama_url, ollama_model) if ollama_url else NullTextKI()
service = PdfService(vorlagen, dateien, ReportlabPdfRenderer(), ki)

# Die mitgelieferte Vorlage einmalig anlegen (Angaben + Datei), danach bleibt sie unverändert liegen.
if vorlagen.get(STANDARD_VORLAGE_ID) is None:
    standard = standard_vorlage()
    vorlagen.save(standard)
    quelle = Path(__file__).parent / "adapters" / "outbound" / "vorlagen" / standard.dateiname
    dateien.speichere(standard.id, quelle.read_bytes())

app = create_app(service)

if kern_url:
    threading.Thread(target=register_with_kern, args=(kern_url, NAME, own_url), daemon=True).start()
