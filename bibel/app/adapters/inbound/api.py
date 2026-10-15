"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
import threading

from fastapi import APIRouter, FastAPI, Form, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from app.application.services import BibelService
from app.domain.bible import BOOKS
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Bibelindex, Verweis


class SeiteIn(BaseModel):
    seite: int | None = None


class SubjectIn(BaseModel):
    name: str


class VerweisIn(BaseModel):
    stelle: str            # kanonische Adresse, z. B. "Joh.3.16" oder "Joh.3.16.5" (Wort 5)
    art: str                # frei, z. B. "register-eintrag", "notiz", "frage" – keine feste Liste
    referenz: str           # eine ID oder Kurzbeschreibung des verweisenden Dings
    titel: str | None = None


def verweis_out(v: Verweis) -> dict:
    return {"id": v.id, "stelle": v.stelle, "art": v.art, "referenz": v.referenz, "titel": v.titel}


def index_out(index: Bibelindex, hat_verse: bool = False) -> dict:
    return {"dateiname": index.dateiname, "hat_verse": hat_verse,
            "buecher": [{"index": b.buch_index, "short": BOOKS[b.buch_index].short, "name": BOOKS[b.buch_index].name,
                         "seite": b.seite, "erkannt": b.erkannt}
                        for b in sorted(index.buchseiten, key=lambda x: x.buch_index)]}


def create_app(service: BibelService) -> FastAPI:
    app = FastAPI(title="Bibel", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        # Fachübergreifend wie pdfcreator/aufgabenleser: eine einzige, gemeinsame Bibel, kein Fach-Bezug.
        return {"name": "bibel", "label": "Bibel", "panel": None, "status": []}

    @api.get("/index")
    def index():
        return index_out(service.index(), service.hat_verse())

    @api.post("/hochladen", status_code=201)
    async def hochladen(name: str = Form(...), datei: UploadFile = None):
        # Seiten-Erkennung dauert wenige Sekunden – im Thread-Pool, sonst blockiert das den ganzen Dienst (auch
        # /api/health) solange. Das Herauslesen der Verse selbst dauert bei einer ganzen Bibel 1-2 Minuten, zu
        # lang für eine Antwort (Proxy-Timeouts) – läuft als eigener, nicht abgewarteter Hintergrund-Thread.
        inhalt = await datei.read()
        ergebnis = await run_in_threadpool(service.hochladen, name, inhalt)
        threading.Thread(target=service.verse_im_hintergrund_einlesen, daemon=True).start()
        return index_out(ergebnis)

    @api.put("/buecher/{buch_index}")
    def seite_setzen(buch_index: int, body: SeiteIn):
        return index_out(service.seite_setzen(buch_index, body.seite))

    @api.get("/datei")
    def datei():
        inhalt = service.datei()
        if inhalt is None:
            raise NotFound("Es ist noch keine Bibel hinterlegt.")
        return Response(content=inhalt, media_type="application/pdf",
                         headers={"Content-Disposition": 'inline; filename="bibel.pdf"'})

    @api.get("/stelle")
    def stelle(text: str):
        return service.stelle(text)

    @api.get("/kapitel")
    def kapitel(buch: str, nummer: int):
        return service.kapitel(buch, nummer)

    @api.get("/wort")
    def wort(stelle: str):
        return service.wort(stelle)

    @api.post("/verweise", status_code=201)
    def verweis_anlegen(body: VerweisIn):
        return verweis_out(service.verweis_anlegen(body.stelle, body.art, body.referenz, body.titel))

    @api.get("/verweise")
    def verweise(stelle: str):
        return [verweis_out(v) for v in service.verweise_zu(stelle)]

    @api.delete("/verweise/{verweis_id}", status_code=204)
    def verweis_loeschen(verweis_id: str):
        service.verweis_loeschen(verweis_id)

    # Fach-Hooks: fachübergreifend, trotzdem die drei Pflicht-Endpunkte, damit der Kern beim Abgleich
    # keine Ausnahme braucht (wie bei pdfcreator/aufgabenleser).
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
