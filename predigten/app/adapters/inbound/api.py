"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
from fastapi import APIRouter, FastAPI, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app.application.services import PredigtenService
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Predigt


class PredigtIn(BaseModel):
    titel: str
    datum: str | None = None
    prediger: str | None = None
    notiz: str | None = None
    stellen: list[str] = []


class SubjectIn(BaseModel):
    name: str


def predigt_out(p: Predigt) -> dict:
    return {"id": p.id, "titel": p.titel, "datum": p.datum, "prediger": p.prediger, "notiz": p.notiz,
            "stellen": p.stellen, "hat_datei": p.hat_datei}


def create_app(service: PredigtenService) -> FastAPI:
    app = FastAPI(title="Predigten", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        # Fachübergreifend wie der Bibel-Dienst: eine Predigt gehört zu keinem Fach, eigene Oberfläche
        # (Liste + Formular mit Datei-Upload und Bibelstellen braucht mehr Interaktion, als das UI-Kit der
        # Dienst-Vorlage hergibt).
        return {"name": "predigten", "label": "Predigten", "panel": None, "status": []}

    @api.get("/predigten")
    def list_predigten():
        return [predigt_out(p) for p in service.list_predigten()]

    @api.post("/predigten", status_code=201)
    def add_predigt(body: PredigtIn):
        return predigt_out(service.add_predigt(body.titel, body.datum, body.prediger, body.notiz, body.stellen))

    @api.put("/predigten/{predigt_id}")
    def update_predigt(predigt_id: str, body: PredigtIn):
        return predigt_out(service.update_predigt(predigt_id, body.titel, body.datum, body.prediger,
                                                   body.notiz, body.stellen))

    @api.delete("/predigten/{predigt_id}", status_code=204)
    def delete_predigt(predigt_id: str):
        service.delete_predigt(predigt_id)

    # Datei (z. B. die gehaltene Predigt als PDF) – wie beim Skripte-/Bibliothek-Dienst
    @api.post("/predigten/{predigt_id}/datei", status_code=201)
    async def datei_hochladen(predigt_id: str, datei: UploadFile):
        inhalt = await datei.read()
        return predigt_out(service.datei_hochladen(predigt_id, inhalt))

    @api.get("/predigten/{predigt_id}/datei")
    def datei(predigt_id: str):
        inhalt = service.datei(predigt_id)
        if inhalt is None:
            raise NotFound("Für diese Predigt ist noch keine Datei hinterlegt.")
        return Response(content=inhalt, media_type="application/pdf",
                         headers={"Content-Disposition": 'inline; filename="predigt.pdf"'})

    # Fach-Hooks: fachübergreifend, darum reine No-ops (siehe Fach-Vertrag in CLAUDE.md).
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
