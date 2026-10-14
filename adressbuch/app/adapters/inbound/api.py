"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from app.application.services import DozentService
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Dozent


class DozentIn(BaseModel):
    name: str
    email: str | None = None
    telefon: str | None = None
    adresse: str | None = None   # altes Freitext-Feld, für ältere Daten
    strasse: str | None = None
    plz: str | None = None
    ort: str | None = None
    notiz: str | None = None


class SubjectIn(BaseModel):
    name: str


def dozent_out(d: Dozent) -> dict:
    return {"id": d.id, "name": d.name, "email": d.email, "telefon": d.telefon, "adresse": d.adresse,
            "strasse": d.strasse, "plz": d.plz, "ort": d.ort, "notiz": d.notiz, "faecher": d.faecher}


def create_app(service: DozentService) -> FastAPI:
    app = FastAPI(title="Adressbuch", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        return {"name": "adressbuch", "label": "Adressbuch", "panel": "ui",
                "status": [{"key": "count", "label": "Dozenten"}]}

    @api.get("/ui", response_class=HTMLResponse)
    def ui():
        return (Path(__file__).parent / "ui.html").read_text("utf-8")

    @api.get("/dozenten")
    def list_dozenten():
        return [dozent_out(d) for d in service.list_dozenten()]

    @api.post("/dozenten", status_code=201)
    def add_dozent(body: DozentIn):
        return dozent_out(service.add_dozent(body.name, body.email, body.telefon, body.adresse,
                                              body.strasse, body.plz, body.ort, body.notiz))

    @api.put("/dozenten/{dozent_id}")
    def update_dozent(dozent_id: str, body: DozentIn):
        return dozent_out(service.update_dozent(dozent_id, body.name, body.email, body.telefon, body.adresse,
                                                 body.strasse, body.plz, body.ort, body.notiz))

    @api.delete("/dozenten/{dozent_id}", status_code=204)
    def delete_dozent(dozent_id: str):
        service.delete_dozent(dozent_id)

    @api.post("/dozenten/{dozent_id}/faecher/{subject_id}", status_code=201)
    def assign(dozent_id: str, subject_id: str):
        return dozent_out(service.assign(dozent_id, subject_id))

    @api.delete("/dozenten/{dozent_id}/faecher/{subject_id}", status_code=204)
    def unassign(dozent_id: str, subject_id: str):
        service.unassign(dozent_id, subject_id)

    # Fach-Hooks: so hängt sich der Dienst an die Fächer des Kerns.
    @api.put("/subjects/{subject_id}", status_code=204)
    def put_subject(subject_id: str, body: SubjectIn):
        pass  # Fachnamen führt der Kern; dieser Dienst kennt nur die Fach-ID

    @api.delete("/subjects/{subject_id}", status_code=204)
    def delete_subject(subject_id: str):
        service.discard_subject(subject_id)

    @api.get("/subjects/{subject_id}/status")
    def subject_status(subject_id: str):
        return service.subject_status(subject_id)

    app.include_router(api)
    return app
