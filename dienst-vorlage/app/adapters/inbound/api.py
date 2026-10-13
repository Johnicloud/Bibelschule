"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from app.application.services import ItemService
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Item


class ItemIn(BaseModel):
    subject_id: str
    text: str


class SubjectIn(BaseModel):
    name: str


def item_out(i: Item) -> dict:
    return {"id": i.id, "subject_id": i.subject_id, "text": i.text}


def create_app(service: ItemService) -> FastAPI:
    app = FastAPI(title="__LABEL__", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        """Steckbrief für den Kern. panel="ui" = die Oberfläche zeigt einen Reiter mit der Seite /api/ui.
        status = welche Kennzahlen aus /subjects/{id}/status auf der Startseite erscheinen."""
        return {"name": "__NAME__", "label": "__LABEL__", "panel": "ui",
                "status": [{"key": "count", "label": "Einträge"}]}

    @api.get("/ui", response_class=HTMLResponse)
    def ui():
        return (Path(__file__).parent / "ui.html").read_text("utf-8")

    @api.get("/items")
    def list_items(subject_id: str | None = None):
        return [item_out(i) for i in service.list_items(subject_id)]

    @api.post("/items", status_code=201)
    def add_item(body: ItemIn):
        return item_out(service.add_item(body.subject_id, body.text))

    @api.delete("/items/{item_id}", status_code=204)
    def delete_item(item_id: str):
        service.delete_item(item_id)

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
