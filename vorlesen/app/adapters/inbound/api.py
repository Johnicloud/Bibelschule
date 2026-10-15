"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
from fastapi import APIRouter, FastAPI, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from app.application.services import VorleseService
from app.domain.errors import InvalidInput


class TextIn(BaseModel):
    text: str


class SubjectIn(BaseModel):
    name: str


def create_app(service: VorleseService) -> FastAPI:
    app = FastAPI(title="Vorlesen", docs_url="/api/docs", openapi_url="/api/openapi.json")
    api = APIRouter(prefix="/api")

    @app.exception_handler(InvalidInput)
    async def _invalid(_, e):
        return JSONResponse({"detail": str(e)}, status_code=422)

    @api.get("/health")
    def health():
        return {"status": "ok"}

    @api.get("/manifest")
    def manifest():
        # Kein panel: der Dienst hat keine Fach-eigene Seite, nur eine API (aus dem Skripte-Reiter einer Datei
        # oder von der globalen Vorlesen-Seite für freien Text aus aufgerufen), wie beim aufgabenleser-Dienst.
        return {"name": "vorlesen", "label": "Vorlesen", "panel": None, "status": []}

    @api.post("/text")
    async def text_vorlesen(body: TextIn):
        # Piper läuft lokal auf der CPU und kann bei längeren Texten einige Sekunden brauchen – im Thread-Pool
        # statt direkt im Event-Loop, sonst blockiert das auch /api/health (siehe aufgabenleser-Dienst).
        audio = await run_in_threadpool(service.text_vorlesen, body.text)
        return Response(content=audio, media_type="audio/wav")

    @api.post("/pdf")
    async def pdf_vorlesen(datei: UploadFile):
        inhalt = await datei.read()
        audio = await run_in_threadpool(service.pdf_vorlesen, inhalt)
        return Response(content=audio, media_type="audio/wav")

    # Fach-Hooks: der Dienst kennt kein einzelnes Fach (liest nur vor, speichert nichts) – nur die
    # Pflicht-Endpunkte, damit der Kern ihn wie jeden anderen Dienst abgleichen kann.
    @api.put("/subjects/{subject_id}", status_code=204)
    def put_subject(subject_id: str, body: SubjectIn):
        pass

    @api.delete("/subjects/{subject_id}", status_code=204)
    def delete_subject(subject_id: str):
        service.discard_subject(subject_id)

    @api.get("/subjects/{subject_id}/status")
    def subject_status(subject_id: str):
        return service.subject_status(subject_id)

    app.include_router(api)
    return app
