"""Eingehender Adapter: HTTP-API des Kerns. Die Oberfläche spricht nur hier.
Eigene Wege: /api/subjects, /api/services, /api/registry, /api/sync, /api/overview.
Alles andere: /api/<dienst>/... wird an den Dienst weitergereicht (z. B. /api/karteikarten/decks).
Interaktive Doku: /api/docs"""
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from app.application.services import SubjectService
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Subject


class SubjectIn(BaseModel):
    name: str


class RegistryIn(BaseModel):
    name: str
    url: str


def subject_out(s: Subject, synced: dict[str, bool] | None = None) -> dict:
    out = {"id": s.id, "name": s.name}
    if synced is not None:
        out["synced"] = synced   # welcher Dienst das Fach übernommen hat (false = nicht erreichbar, später /api/sync)
    return out


def create_app(service: SubjectService) -> FastAPI:
    app = FastAPI(title="Bibelschule (Kern)", docs_url="/api/docs", openapi_url="/api/openapi.json")
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

    @api.get("/subjects")
    def list_subjects():
        return [subject_out(s) for s in service.list_subjects()]

    @api.post("/subjects", status_code=201)
    def create_subject(body: SubjectIn):
        return subject_out(*service.create_subject(body.name))

    @api.get("/subjects/{subject_id}")
    def get_subject(subject_id: str):
        return subject_out(service.get_subject(subject_id))

    @api.get("/subjects/{subject_id}/overview")
    def subject_overview(subject_id: str):
        """Stand eines Fachs: Status je Dienst, Gesamtfortschritt (progress) und seine Teile (parts)."""
        return service.subject_overview(subject_id)

    @api.put("/subjects/{subject_id}")
    def rename_subject(subject_id: str, body: SubjectIn):
        return subject_out(*service.rename_subject(subject_id, body.name))

    @api.delete("/subjects/{subject_id}", status_code=204)
    def delete_subject(subject_id: str):
        service.delete_subject(subject_id)

    @api.get("/services")
    def services():
        return service.services_status()

    @api.post("/registry", status_code=201)
    def register_service(body: RegistryIn):
        """Ein neuer Dienst meldet sich hier an: {name, url}. Er bekommt sofort alle Fächer (Antwort: synced)."""
        return service.register_service(body.name, body.url)

    @api.post("/sync")
    def sync():
        return service.sync()

    @api.get("/overview")
    def overview():
        return service.overview()

    @api.api_route("/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                   include_in_schema=False)
    async def proxy(service_name: str, path: str, request: Request):
        body = await request.body()
        status, content, content_type = await run_in_threadpool(
            service.forward, service_name, request.method, path, request.url.query, body,
            request.headers.get("content-type"))
        return Response(content=content, status_code=status, media_type=content_type)

    app.include_router(api)
    return app
