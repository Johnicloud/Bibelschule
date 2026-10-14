"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
from pathlib import Path

from fastapi import APIRouter, FastAPI, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from app.application.services import PdfService
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Vorlage


class BuchIn(BaseModel):
    titel: str
    seiten: int | str = ""


class FuellenIn(BaseModel):
    werte: dict[str, str] = {}
    buecher: list[BuchIn] = []


class SubjectIn(BaseModel):
    name: str


def vorlage_out(v: Vorlage) -> dict:
    return {"id": v.id, "name": v.name, "dateiname": v.dateiname,
            "felder": [f.schluessel for f in v.felder], "ki_vorschlag": v.ki_vorschlag}


def create_app(service: PdfService) -> FastAPI:
    app = FastAPI(title="PDF-Vorlagen", docs_url="/api/docs", openapi_url="/api/openapi.json")
    api = APIRouter(prefix="/api")

    @app.exception_handler(NotFound)
    async def _not_found(_, e):
        return JSONResponse({"detail": str(e)}, status_code=404)

    @app.exception_handler(InvalidInput)
    async def _invalid(_, e):
        return JSONResponse({"detail": str(e)}, status_code=422)

    @api.get("/health")
    def health():
        return {"status": "ok"}

    @api.get("/manifest")
    def manifest():
        # Kein panel: der Dienst hat keine Fach-eigene Seite (Vorlagen sind fachübergreifend), nur eine API.
        return {"name": "pdfcreator", "label": "PDF-Vorlagen", "panel": None, "status": []}

    @api.get("/vorlagen")
    def list_vorlagen():
        return [vorlage_out(v) for v in service.list_vorlagen()]

    @api.post("/vorlagen", status_code=201)
    async def hochladen(name: str = Form(...), datei: UploadFile = None):
        # service.hochladen() kann Ollama synchron befragen (bis zu 180 Sekunden, siehe OllamaClient) – im
        # Thread-Pool ausführen, sonst blockiert das den ganzen Dienst (auch /api/health) solange.
        inhalt = await datei.read()
        return vorlage_out(await run_in_threadpool(service.hochladen, name, datei.filename or "", inhalt))

    @api.delete("/vorlagen/{vorlage_id}", status_code=204)
    def delete(vorlage_id: str):
        service.delete(vorlage_id)

    @api.post("/vorlagen/{vorlage_id}/fuellen")
    def fuellen(vorlage_id: str, body: FuellenIn):
        buecher = [{"titel": b.titel, "seiten": b.seiten} for b in body.buecher]
        pdf = service.fuellen(vorlage_id, body.werte, buecher)
        return Response(content=pdf, media_type="application/pdf",
                         headers={"Content-Disposition": 'inline; filename="ausgefuellt.pdf"'})

    # Fach-Hooks: Vorlagen sind fachübergreifend, dieser Dienst kennt kein einzelnes Fach – nur Pflicht-Endpunkte,
    # damit der Kern ihn wie jeden anderen Dienst abgleichen kann, ohne eine Ausnahme zu brauchen.
    @api.put("/subjects/{subject_id}", status_code=204)
    def put_subject(subject_id: str, body: SubjectIn):
        pass

    @api.delete("/subjects/{subject_id}", status_code=204)
    def delete_subject(subject_id: str):
        pass

    @api.get("/subjects/{subject_id}/status")
    def subject_status(subject_id: str):
        return {}

    app.include_router(api)
    return app
