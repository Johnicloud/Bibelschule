"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from app.application.services import VersService
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Vers


class VersIn(BaseModel):
    referenz: str
    text: str
    subject_id: str | None = None


class ReviewIn(BaseModel):
    correct: bool


class SubjectIn(BaseModel):
    name: str


def vers_out(v: Vers) -> dict:
    return {"id": v.id, "referenz": v.referenz, "text": v.text, "subject_id": v.subject_id,
            "box": v.box, "due": v.due.isoformat(), "faellig": v.is_due()}


def create_app(service: VersService) -> FastAPI:
    app = FastAPI(title="Bibelverse", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        return {"name": "bibelverse", "label": "Bibelverse", "panel": "ui",
                "status": [{"key": "faellig", "label": "fällig"}, {"key": "count", "label": "Verse"}]}

    @api.get("/ui", response_class=HTMLResponse)
    def ui():
        return (Path(__file__).parent / "ui.html").read_text("utf-8")

    @api.get("/verse")
    def list_verse(subject_id: str | None = None, allgemein: bool = False):
        return [vers_out(v) for v in service.list_verse(subject_id, allgemein)]

    @api.get("/verse/faellig")
    def faellig(subject_id: str):
        return [vers_out(v) for v in service.due_verse(subject_id)]

    @api.post("/verse", status_code=201)
    def add_vers(body: VersIn):
        return vers_out(service.add_vers(body.referenz, body.text, body.subject_id))

    @api.put("/verse/{vers_id}")
    def update_vers(vers_id: str, body: VersIn):
        return vers_out(service.update_vers(vers_id, body.referenz, body.text, body.subject_id))

    @api.post("/verse/{vers_id}/review")
    def review(vers_id: str, body: ReviewIn):
        return vers_out(service.review(vers_id, body.correct))

    @api.delete("/verse/{vers_id}", status_code=204)
    def delete(vers_id: str):
        service.delete(vers_id)

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
