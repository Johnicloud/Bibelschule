"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.application.services import NotizenService
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Kommentar


class KommentarIn(BaseModel):
    stelle: str
    text: str


class SubjectIn(BaseModel):
    name: str


def kommentar_out(k: Kommentar) -> dict:
    return {"id": k.id, "stelle": k.stelle, "text": k.text, "erstellt": k.erstellt.isoformat(),
            "verweis_id": k.verweis_id}


def create_app(service: NotizenService) -> FastAPI:
    app = FastAPI(title="Notizen", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        # Fachübergreifend wie der Bibel-Dienst: ein Kommentar gehört zu keinem Fach, eigener globaler Reiter
        # im Kern-Frontend (braucht ein Stellen-Eingabefeld, mehr als das UI-Kit der Dienst-Vorlage hergibt).
        return {"name": "notizen", "label": "Notizen", "panel": None, "status": []}

    @api.get("/kommentare")
    def kommentare(stelle: str):
        return [kommentar_out(k) for k in service.liste_zu_stelle(stelle)]

    @api.post("/kommentare", status_code=201)
    def kommentar_anlegen(body: KommentarIn):
        return kommentar_out(service.kommentar_anlegen(body.stelle, body.text))

    @api.delete("/kommentare/{kommentar_id}", status_code=204)
    def kommentar_loeschen(kommentar_id: str):
        service.loeschen(kommentar_id)

    # Fach-Hooks: fachübergreifend, trotzdem die drei Pflicht-Endpunkte, damit der Kern beim Abgleich
    # keine Ausnahme braucht (wie bei bibel/pdfcreator/aufgabenleser/schnelllesen).
    @api.put("/subjects/{subject_id}", status_code=204)
    def put_subject(subject_id: str, body: SubjectIn):
        pass

    @api.delete("/subjects/{subject_id}", status_code=204)
    def delete_subject(subject_id: str):
        pass

    @api.get("/subjects/{subject_id}/status")
    def subject_status(subject_id: str):
        return service.subject_status(subject_id)

    app.include_router(api)
    return app
