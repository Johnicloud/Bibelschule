"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json (auch für übergeordnete Services nutzbar)."""
from typing import Literal

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.adapters.inbound.exports import entries_table, passages_table, to_csv, to_text
from app.application.services import RegisterService
from app.domain.bible import BOOKS, BibleRef
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Register, RegisterEntry


class RegisterIn(BaseModel):
    subject_id: str
    name: str


class RegisterRename(BaseModel):
    name: str


class EntryIn(BaseModel):
    register_id: str
    name: str
    refs: list[str] = Field(default_factory=list)   # z. B. ["1Mo 12,1-3", "Hebr 11,8"] oder "Joh 3,16; Joh 4,5"
    lat: float | None = None   # Koordinaten, von Hand eingetragen; optional, nicht nur für Orte-Register
    lon: float | None = None


class LocationIn(BaseModel):
    lat: float | None = None
    lon: float | None = None


class SubjectIn(BaseModel):
    name: str


def ref_out(r: BibleRef) -> dict:
    return {"text": r.format(), "book": r.book, "book_name": BOOKS[r.book].name, "chapter": r.chapter,
            "verse": r.verse, "chapter_end": r.chapter_end, "verse_end": r.verse_end}


def register_out(r: Register, count: int) -> dict:
    return {"id": r.id, "subject_id": r.subject_id, "name": r.name, "entry_count": count}


def entry_out(e: RegisterEntry) -> dict:
    return {"id": e.id, "subject_id": e.subject_id, "register_id": e.register_id, "name": e.name,
            "lat": e.lat, "lon": e.lon, "refs": [ref_out(r) for r in e.refs]}


def create_app(service: RegisterService) -> FastAPI:
    app = FastAPI(title="Register", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        """Steckbrief für den Kern: so zeigt die Oberfläche diesen Dienst an."""
        return {"name": "register", "label": "Register", "panel": None,
                "status": [{"key": "registers", "label": "Register"}, {"key": "entries", "label": "Einträge"}]}

    @api.get("/books")
    def books():
        return [{"index": b.index, "short": b.short, "name": b.name} for b in BOOKS]

    @api.get("/registers")
    def list_registers(subject_id: str):
        return [register_out(r, n) for r, n in service.list_registers(subject_id)]

    @api.post("/registers", status_code=201)
    def create_register(body: RegisterIn):
        return register_out(service.create_register(body.subject_id, body.name), 0)

    @api.put("/registers/{register_id}")
    def rename_register(register_id: str, body: RegisterRename):
        r = service.rename_register(register_id, body.name)
        return register_out(r, len(service.list_entries(register_id=r.id)))

    @api.delete("/registers/{register_id}", status_code=204)
    def delete_register(register_id: str):
        service.delete_register(register_id)

    @api.get("/entries")
    def list_entries(subject_id: str | None = None, register_id: str | None = None,
                     sort: Literal["name", "bibel"] = "name"):
        return [entry_out(e) for e in service.list_entries(subject_id, register_id, sort)]

    @api.post("/entries", status_code=201)
    def add_entry(body: EntryIn):
        return entry_out(service.add_entry(body.register_id, body.name, body.refs, body.lat, body.lon))

    @api.delete("/entries/{entry_id}", status_code=204)
    def delete_entry(entry_id: str):
        service.delete_entry(entry_id)

    @api.put("/entries/{entry_id}/location")
    def set_location(entry_id: str, body: LocationIn):
        return entry_out(service.set_location(entry_id, body.lat, body.lon))

    @api.get("/passages")
    def passages(subject_id: str | None = None, register_id: str | None = None):
        return [{**ref_out(ref), "entries": [{"id": e.id, "register_id": e.register_id, "name": e.name} for e in entries]}
                for ref, entries in service.by_passage(subject_id, register_id)]

    @api.get("/export")
    def export(subject_id: str | None = None, register_id: str | None = None,
               sort: Literal["name", "bibel", "stellen"] = "name", format: Literal["csv", "txt"] = "csv"):
        """Liste zum Herunterladen. sort=stellen ergibt das Bibelstellenregister (Stelle -> Einträge)."""
        names = service.register_names()
        if sort == "stellen":
            header, rows = passages_table(service.by_passage(subject_id, register_id), names)
        else:
            header, rows = entries_table(service.list_entries(subject_id, register_id, sort), names, mit_register=register_id is None)
        if format == "csv":
            body = to_csv(header, rows).encode("utf-8-sig")   # mit BOM, damit Excel Umlaute richtig liest
            media = "text/csv; charset=utf-8"
        else:
            body, media = to_text(rows).encode("utf-8"), "text/plain; charset=utf-8"
        return Response(body, media_type=media,
                        headers={"Content-Disposition": f'attachment; filename="register-{sort}.{format}"'})

    # Fach-Hooks: so hängt sich dieser Dienst an die zentrale Fächerverwaltung des Kerns.
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
