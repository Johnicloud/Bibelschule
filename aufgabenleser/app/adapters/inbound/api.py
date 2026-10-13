"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
from fastapi import APIRouter, FastAPI, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.application.services import AufgabenLeseService
from app.domain.errors import InvalidInput, NotFound


class SubjectIn(BaseModel):
    name: str


def create_app(service: AufgabenLeseService) -> FastAPI:
    app = FastAPI(title="Aufgabenblatt-Leser", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        # Kein panel: der Dienst hat keine Fach-eigene Seite, nur eine API (die Oberfläche ruft sie vom
        # Fach-Reiter „Aufgaben“ aus auf, wie das Füllen einer PDF-Vorlage beim pdfcreator-Dienst).
        return {"name": "aufgabenleser", "label": "Aufgabenblatt-Leser", "panel": None, "status": []}

    @api.post("/lesen")
    async def lesen(datei: UploadFile):
        inhalt = await datei.read()
        return service.lesen(inhalt)

    # Fach-Hooks: der Dienst kennt kein einzelnes Fach (liest nur vor, speichert nichts) – nur die
    # Pflicht-Endpunkte, damit der Kern ihn wie jeden anderen Dienst abgleichen kann.
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
