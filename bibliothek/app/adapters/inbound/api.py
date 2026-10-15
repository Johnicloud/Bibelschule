"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
import threading

from fastapi import APIRouter, FastAPI, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from app.application.services import BibliothekService
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Buch


class BuchIn(BaseModel):
    titel: str
    autor: str | None = None
    verlag: str | None = None
    jahr: int | None = None
    isbn: str | None = None
    standort: str | None = None
    notiz: str | None = None


class AusleihenIn(BaseModel):
    an: str


class SubjectIn(BaseModel):
    name: str


def buch_out(b: Buch) -> dict:
    return {"id": b.id, "titel": b.titel, "autor": b.autor, "verlag": b.verlag, "jahr": b.jahr, "isbn": b.isbn,
            "standort": b.standort, "notiz": b.notiz, "ausgeliehen_an": b.ausgeliehen_an,
            "hat_datei": b.hat_datei, "text_erkannt": b.text_erkannt, "faecher": b.faecher}


def create_app(service: BibliothekService) -> FastAPI:
    app = FastAPI(title="Bibliothek", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        return {"name": "bibliothek", "label": "Bibliothek", "panel": None,
                "status": [{"key": "count", "label": "Bücher"}]}

    @api.get("/buecher")
    def list_buecher():
        return [buch_out(b) for b in service.list_buecher()]

    @api.get("/suche")
    def suche(text: str):
        return service.suche(text)

    @api.post("/buecher", status_code=201)
    def add_buch(body: BuchIn):
        return buch_out(service.add_buch(body.titel, body.autor, body.verlag, body.jahr, body.isbn,
                                         body.standort, body.notiz))

    @api.put("/buecher/{buch_id}")
    def update_buch(buch_id: str, body: BuchIn):
        return buch_out(service.update_buch(buch_id, body.titel, body.autor, body.verlag, body.jahr,
                                            body.isbn, body.standort, body.notiz))

    @api.delete("/buecher/{buch_id}", status_code=204)
    def delete_buch(buch_id: str):
        service.delete_buch(buch_id)

    @api.post("/buecher/{buch_id}/ausleihen")
    def ausleihen(buch_id: str, body: AusleihenIn):
        return buch_out(service.ausleihen(buch_id, body.an))

    @api.post("/buecher/{buch_id}/zurueckgeben")
    def zurueckgeben(buch_id: str):
        return buch_out(service.zurueckgeben(buch_id))

    @api.post("/buecher/{buch_id}/faecher/{subject_id}", status_code=201)
    def assign(buch_id: str, subject_id: str):
        return buch_out(service.assign(buch_id, subject_id))

    @api.delete("/buecher/{buch_id}/faecher/{subject_id}", status_code=204)
    def unassign(buch_id: str, subject_id: str):
        service.unassign(buch_id, subject_id)

    # Datei (gescanntes Buch) und Text-Erkennung (Ollama, Vision-Modell)
    @api.post("/buecher/{buch_id}/datei", status_code=201)
    async def datei_hochladen(buch_id: str, datei: UploadFile):
        inhalt = await datei.read()
        return buch_out(await run_in_threadpool(service.datei_hochladen, buch_id, inhalt))

    @api.get("/buecher/{buch_id}/datei")
    def original_datei(buch_id: str):
        inhalt = service.original_datei(buch_id)
        if inhalt is None:
            raise NotFound("Für dieses Buch ist noch keine Datei hinterlegt.")
        return Response(content=inhalt, media_type="application/pdf",
                         headers={"Content-Disposition": 'inline; filename="original.pdf"'})

    @api.get("/buecher/{buch_id}/text-datei")
    def text_datei(buch_id: str):
        inhalt = service.text_datei(buch_id)
        if inhalt is None:
            raise NotFound("Für dieses Buch ist noch keine Text-Erkennung fertig.")
        return Response(content=inhalt, media_type="application/pdf",
                         headers={"Content-Disposition": 'inline; filename="text.pdf"'})

    @api.post("/buecher/{buch_id}/text-erkennen", status_code=202)
    def text_erkennen(buch_id: str):
        # Ein KI-Aufruf je Seite, dauert bei einem ganzen Buch mehrere Minuten – zu lang für eine Antwort
        # (Proxy-Timeouts), läuft darum als eigener, nicht abgewarteter Hintergrund-Thread (wie beim
        # Verse-Einlesen des bibel-Diensts). service.original_datei wirft NotFound, falls das Buch nicht
        # existiert – das soll die Anfrage selbst noch melden, darum hier (nicht im Thread) einmal geprüft.
        if service.original_datei(buch_id) is None:
            raise NotFound("Für dieses Buch ist noch keine Datei hinterlegt.")
        threading.Thread(target=service.text_erkennen, args=(buch_id,), daemon=True).start()
        return {"status": "läuft"}

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
