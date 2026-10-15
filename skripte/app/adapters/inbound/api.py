"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
from pathlib import Path

from fastapi import APIRouter, FastAPI, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

from app.application.services import SkriptService
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Skript


class SubjectIn(BaseModel):
    name: str


def skript_out(s: Skript) -> dict:
    return {"id": s.id, "subject_id": s.subject_id, "dateiname": s.dateiname, "content_type": s.content_type,
            "groesse": s.groesse, "hochgeladen_am": s.hochgeladen_am}


def create_app(service: SkriptService) -> FastAPI:
    app = FastAPI(title="Skripte", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        return {"name": "skripte", "label": "Skripte", "panel": "ui",
                "status": [{"key": "count", "label": "Skripte"}]}

    @api.get("/ui", response_class=HTMLResponse)
    def ui():
        return (Path(__file__).parent / "ui.html").read_text("utf-8")

    @api.get("/skripte")
    def list_skripte(subject_id: str | None = None):
        return [skript_out(s) for s in service.list_skripte(subject_id)]

    @api.get("/suche")
    def suche(text: str, subject_id: str | None = None):
        return service.suche(text, subject_id)

    @api.post("/skripte", status_code=201)
    async def upload(subject_id: str = Form(...), datei: UploadFile = None):
        inhalt = await datei.read()
        return skript_out(service.upload(subject_id, datei.filename or "", datei.content_type, inhalt))

    @api.get("/skripte/{skript_id}/datei")
    def datei(skript_id: str):
        skript, inhalt = service.datei(skript_id)
        dateiname = skript.dateiname.replace('"', "")
        return Response(content=inhalt, media_type=skript.content_type,
                         headers={"Content-Disposition": f'inline; filename="{dateiname}"'})

    @api.delete("/skripte/{skript_id}", status_code=204)
    def delete(skript_id: str):
        service.delete(skript_id)

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
