"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.application.services import SchnelllesenService
from app.domain.bible import BOOKS
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Durchgang, Einheit


class EinheitIn(BaseModel):
    buch: str
    kapitel: int


class DurchgangIn(BaseModel):
    sekunden: float


class SubjectIn(BaseModel):
    name: str


def durchgang_out(e: Einheit, d: Durchgang) -> dict:
    return {"runde": d.runde, "sekunden": d.sekunden, "ziel_sekunden": d.ziel_sekunden, "wpm": e.wpm(d)}


def einheit_out(e: Einheit, mit_text: bool = False) -> dict:
    d = {"id": e.id, "buch": e.buch, "buch_name": e.buch_name, "kapitel": e.kapitel,
         "wortanzahl": e.wortanzahl, "erstellt": e.erstellt, "fertig": e.fertig,
         "naechste_runde": e.naechste_runde, "durchgaenge": [durchgang_out(e, x) for x in e.durchgaenge]}
    if mit_text:
        d["text"] = e.text
    return d


def create_app(service: SchnelllesenService) -> FastAPI:
    app = FastAPI(title="Schnelllesen", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        # Fachübergreifend wie der Bibel-Dienst: ein Training gehört zu keinem Fach, eigene Oberfläche
        # (Reiter braucht einen laufenden Timer – mehr Interaktion, als das UI-Kit der Dienst-Vorlage hergibt).
        return {"name": "schnelllesen", "label": "Schnelllesen", "panel": None, "status": []}

    @api.get("/buecher")
    def buecher():
        # Eigene Kopie der Buchliste (siehe domain/bible.py) – nur für die Buch/Kapitel-Auswahl der Oberfläche.
        return [{"index": b.index, "short": b.short, "name": b.name, "kapitel_gesamt": b.chapters} for b in BOOKS]

    @api.get("/einheiten")
    def liste():
        return [einheit_out(e) for e in service.liste()]

    @api.get("/einheiten/{einheit_id}")
    def get_einheit(einheit_id: str):
        return einheit_out(service.get(einheit_id), mit_text=True)

    @api.post("/einheiten", status_code=201)
    def neue_einheit(body: EinheitIn):
        return einheit_out(service.neue_einheit(body.buch, body.kapitel), mit_text=True)

    @api.post("/einheiten/{einheit_id}/durchgaenge", status_code=201)
    def durchgang_abschliessen(einheit_id: str, body: DurchgangIn):
        return einheit_out(service.durchgang_abschliessen(einheit_id, body.sekunden), mit_text=True)

    @api.delete("/einheiten/{einheit_id}", status_code=204)
    def loeschen(einheit_id: str):
        service.loeschen(einheit_id)

    # Fach-Hooks: fachübergreifend, trotzdem die drei Pflicht-Endpunkte, damit der Kern beim Abgleich
    # keine Ausnahme braucht (wie bei bibel/pdfcreator/aufgabenleser).
    @api.put("/subjects/{subject_id}", status_code=204)
    def put_subject(subject_id: str, body: SubjectIn):
        pass

    @api.delete("/subjects/{subject_id}", status_code=204)
    def delete_subject(subject_id: str):
        pass

    @api.get("/subjects/{subject_id}/status")
    def subject_status(subject_id: str):
        return service.subject_status(subject_id)

    app.include_router(api)
    return app
