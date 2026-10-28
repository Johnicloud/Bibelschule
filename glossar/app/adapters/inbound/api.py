"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.application.services import GlossarService
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import GlossarEintrag


class EintragIn(BaseModel):
    wort: str
    transliteration: str = ""
    erklaerung: str = ""
    stellen: list[str] = []


class SubjectIn(BaseModel):
    name: str


def eintrag_out(e: GlossarEintrag) -> dict:
    return {"id": e.id, "wort": e.wort, "transliteration": e.transliteration, "erklaerung": e.erklaerung,
            "stellen": [s.stelle for s in e.stellen]}


def create_app(service: GlossarService) -> FastAPI:
    app = FastAPI(title="Glossar", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        """Fachübergreifend wie bibel/bibliothek/schnelllesen: kein `panel` (eigene Oberfläche als globaler
        Reiter im Kern-Frontend, siehe GlossarView.vue), keine `status`-Kennzahlen je Fach."""
        return {"name": "glossar", "label": "Glossar", "panel": None, "status": []}

    @api.get("/eintraege")
    def list_eintraege():
        return [eintrag_out(e) for e in service.list_entries()]

    @api.post("/eintraege", status_code=201)
    def add_eintrag(body: EintragIn):
        return eintrag_out(service.create(body.wort, body.transliteration, body.erklaerung, body.stellen))

    @api.put("/eintraege/{eintrag_id}")
    def update_eintrag(eintrag_id: str, body: EintragIn):
        return eintrag_out(service.update(eintrag_id, body.wort, body.transliteration, body.erklaerung, body.stellen))

    @api.delete("/eintraege/{eintrag_id}", status_code=204)
    def delete_eintrag(eintrag_id: str):
        service.delete(eintrag_id)

    # Fach-Vertrag: fachübergreifend, trotzdem die drei Pflicht-Endpunkte als No-ops, damit der Kern beim
    # Abgleich keine Ausnahme braucht (wie bei pdfcreator/aufgabenleser/bibel/bibliothek/schnelllesen).
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
