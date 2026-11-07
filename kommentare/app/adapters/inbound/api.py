"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
import logging
import threading

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.application.services import KommentarService
from app.domain.bible import BOOKS, find_book
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import KommentarEintrag, Quelle

log = logging.getLogger(__name__)

MATTHEW_HENRY_TITEL = "Matthew Henry, Commentary on the Whole Bible"


class MatthewHenryImportIn(BaseModel):
    buecher: list[str] | None = None   # Kurznamen, z. B. ["Mt", "Mk"] – None/leer = die ganze Bibel


class QuelleIn(BaseModel):
    titel: str
    autor: str = ""
    sprache: str = "de"
    lizenz: str = ""
    quell_url: str = ""
    namensnennung: str = ""


class EintragIn(BaseModel):
    quelle_id: str
    buch: str
    kapitel: int
    vers_von: int
    vers_bis: int
    text: str


class SubjectIn(BaseModel):
    name: str


def quelle_out(q: Quelle) -> dict:
    return {"id": q.id, "titel": q.titel, "autor": q.autor, "sprache": q.sprache, "lizenz": q.lizenz,
            "quell_url": q.quell_url, "namensnennung": q.namensnennung}


def eintrag_out(e: KommentarEintrag, quelle: Quelle | None = None) -> dict:
    return {"id": e.id, "quelle_id": e.quelle_id, "quelle_titel": quelle.titel if quelle else None,
            "quelle_sprache": quelle.sprache if quelle else None, "buch": BOOKS[e.buch_index].short,
            "buch_name": BOOKS[e.buch_index].name, "kapitel": e.kapitel, "vers_von": e.vers_von,
            "vers_bis": e.vers_bis, "text": e.text}


def create_app(service: KommentarService, matthew_henry_import=None) -> FastAPI:
    """`matthew_henry_import`: optionaler Port `(buch_indizes: list[int] | None) -> list[tuple]` (siehe
    matthew_henry.py), lädt die Einträge von der HelloAO-API. Ohne ihn bleibt die Import-Route ohne Wirkung
    (liefert 503) – wie bei anderen optionalen Zusatzfähigkeiten im Projekt (z. B. Ollama bei pdfcreator)."""
    app = FastAPI(title="Kommentare", docs_url="/api/docs", openapi_url="/api/openapi.json")
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
        # Fachübergreifend wie bibel/glossar/predigten: kein `panel`, eigene Oberfläche als globaler Reiter.
        return {"name": "kommentare", "label": "Kommentare", "panel": None, "status": []}

    @api.get("/quellen")
    def quellen_liste():
        return [quelle_out(q) for q in service.quellen_liste()]

    @api.post("/quellen", status_code=201)
    def quelle_anlegen(body: QuelleIn):
        return quelle_out(service.quelle_anlegen(body.titel, body.autor, body.sprache, body.lizenz,
                                                   body.quell_url, body.namensnennung))

    @api.delete("/quellen/{quelle_id}", status_code=204)
    def quelle_loeschen(quelle_id: str):
        service.quelle_loeschen(quelle_id)

    @api.get("/quellen/{quelle_id}/eintraege")
    def eintraege_zu_quelle(quelle_id: str):
        quelle = service.quelle(quelle_id)
        return [eintrag_out(e, quelle) for e in service.eintraege_zu_quelle(quelle_id)]

    @api.get("/eintraege")
    def eintraege_zu_stelle(buch: str, kapitel: int, vers: int):
        treffer = service.zu_stelle(buch, kapitel, vers)
        quellen = {q.id: q for q in service.quellen_liste()}
        return [eintrag_out(e, quellen.get(e.quelle_id)) for e in treffer]

    @api.post("/eintraege", status_code=201)
    def eintrag_anlegen(body: EintragIn):
        return eintrag_out(service.eintrag_anlegen(body.quelle_id, body.buch, body.kapitel, body.vers_von,
                                                     body.vers_bis, body.text))

    @api.delete("/eintraege/{eintrag_id}", status_code=204)
    def eintrag_loeschen(eintrag_id: str):
        service.eintrag_loeschen(eintrag_id)

    @api.post("/import/matthew-henry", status_code=202)
    def matthew_henry_importieren(body: MatthewHenryImportIn):
        if matthew_henry_import is None:
            return JSONResponse({"detail": "Matthew-Henry-Import ist nicht eingerichtet."}, status_code=503)
        buch_indizes = None
        if body.buecher:
            buch_indizes = []
            for kurz in body.buecher:
                buch = find_book(kurz)
                if buch is None:
                    raise InvalidInput(f"Das Bibelbuch „{kurz}“ kenne ich nicht.")
                buch_indizes.append(buch.index)

        def _import_im_hintergrund():
            quelle = next((q for q in service.quellen_liste() if q.autor == "Matthew Henry"), None)
            if quelle is None:
                quelle = service.quelle_anlegen(
                    MATTHEW_HENRY_TITEL, "Matthew Henry", "en", "gemeinfrei (CC Public Domain Mark)",
                    "https://bible.helloao.org",
                    f"{MATTHEW_HENRY_TITEL} (public domain), via bible.helloao.org")
            try:
                eintraege = matthew_henry_import(buch_indizes)
                service.import_teilweise(quelle.id, eintraege)
            except Exception as e:
                log.warning("Matthew-Henry-Import fehlgeschlagen: %s", e)

        threading.Thread(target=_import_im_hintergrund, daemon=True).start()
        return {"status": "gestartet"}

    # Fach-Vertrag: fachübergreifend, trotzdem die drei Pflicht-Endpunkte als No-ops, damit der Kern beim
    # Abgleich keine Ausnahme braucht (wie bei bibel/glossar/predigten/schnelllesen).
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
