"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from app.application.services import FragenKiService
from app.domain.bible import BOOKS
from app.domain.errors import InvalidInput, NotFound


class GenerierenIn(BaseModel):
    buch: str
    kapitel: int


class SubjectIn(BaseModel):
    name: str


def create_app(service: FragenKiService) -> FastAPI:
    app = FastAPI(title="Fragen und KI", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        # Kein panel: der Dienst hat keine Fach-eigene Seite, nur eine API (die Oberfläche zeigt ihn als
        # globalen Reiter, wie den Bibel-Dienst, nicht im Fach-Reiter).
        return {"name": "fragenki", "label": "Fragen und KI", "panel": None, "status": []}

    @api.get("/buecher")
    def buecher():
        # Eigene Kopie der Buchliste (siehe domain/bible.py) – nur für die Buch/Kapitel-Auswahl der Oberfläche.
        return [{"index": b.index, "short": b.short, "name": b.name, "kapitel_gesamt": b.chapters} for b in BOOKS]

    @api.post("/generieren")
    async def generieren(body: GenerierenIn):
        # service.generieren() ruft Ollama synchron auf und kann bis zu 180 Sekunden brauchen (siehe
        # OllamaClient). Im Thread-Pool statt direkt im Event-Loop ausführen, sonst blockiert das den
        # ganzen Dienst (auch /api/health) für die Dauer der Anfrage.
        return await run_in_threadpool(service.generieren, body.buch, body.kapitel)

    # Fach-Hooks: der Dienst kennt kein einzelnes Fach (schlägt nur vor, speichert nichts) – nur die
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
