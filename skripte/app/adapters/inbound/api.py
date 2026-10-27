"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json"""
from pathlib import Path
from urllib.parse import quote

import re

from fastapi import APIRouter, FastAPI, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel

from app.application.services import SkriptService
from app.domain.dateitypen import art, kann_fragen, media_type
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Skript


class SubjectIn(BaseModel):
    name: str


class UmbenennenIn(BaseModel):
    dateiname: str


def skript_out(s: Skript, text: dict | None = None) -> dict:
    return {"id": s.id, "subject_id": s.subject_id, "dateiname": s.dateiname, "content_type": s.content_type,
            "groesse": s.groesse, "hochgeladen_am": s.hochgeladen_am,
            "art": art(s.dateiname), "kann_fragen": kann_fragen(s.dateiname),
            "text_status": (text or {}).get("status"), "text_fehler": (text or {}).get("fehler")}


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
        return [skript_out(s, service.text_status(s.id)) for s in service.list_skripte(subject_id)]

    @api.post("/skripte", status_code=201)
    async def upload(subject_id: str = Form(...), datei: UploadFile = None, dateiname: str | None = Form(None)):
        inhalt = await datei.read()
        return skript_out(service.upload(subject_id, datei.filename or "", datei.content_type, inhalt, dateiname))

    @api.get("/skripte/{skript_id}/datei")
    def datei(skript_id: str, request: Request, original: bool = False):
        # HTTP-Kopfzeilen sind Latin-1: Namen mit Sonderzeichen (z. B. unsichtbare Richtungszeichen) gehen nur als
        # filename*= (RFC 5987), dazu ein einfacher Ersatzname für alte Programme.
        def kopf(skript, extra=None):
            name = skript.dateiname.replace('"', "")
            einfach = name.encode("ascii", "ignore").decode() or "datei"
            return {"Content-Disposition": f"inline; filename=\"{einfach}\"; filename*=UTF-8''{quote(name)}",
                    "Accept-Ranges": "bytes", **(extra or {})}

        spanne = re.fullmatch(r"bytes=(\d*)-(\d*)", request.headers.get("range", "").strip())
        if spanne and (spanne.group(1) or spanne.group(2)):
            # Audio/Video (Safari verlangt es): nur das angefragte Stück liefern, Antwort 206
            if spanne.group(1):
                start, ende = int(spanne.group(1)), (int(spanne.group(2)) if spanne.group(2) else None)
            else:      # „die letzten n Bytes“
                gesamt = service.bereich(skript_id, 0, 0, original)[4]
                start, ende = max(gesamt - int(spanne.group(2)), 0), None
            skript, stueck, start, ende, gesamt = service.bereich(skript_id, start, ende, original)
            return Response(content=stueck, status_code=206, media_type=media_type(skript.dateiname, skript.content_type),
                            headers=kopf(skript, {"Content-Range": f"bytes {start}-{ende}/{gesamt}"}))
        skript, inhalt = service.datei(skript_id, original)
        return Response(content=inhalt, media_type=media_type(skript.dateiname, skript.content_type), headers=kopf(skript))

    @api.get("/skripte/{skript_id}/text", response_class=PlainTextResponse)
    def ansichtstext(skript_id: str):
        return PlainTextResponse(service.ansichtstext(skript_id), media_type="text/plain; charset=utf-8")

    @api.put("/skripte/{skript_id}")
    def umbenennen(skript_id: str, body: UmbenennenIn):
        return skript_out(service.umbenennen(skript_id, body.dateiname), service.text_status(skript_id))

    @api.post("/skripte/{skript_id}/text-erkennen", status_code=202)
    def text_erkennen(skript_id: str):
        service.text_erkennen_starten(skript_id)
        return service.text_status(skript_id)

    @api.get("/skripte/{skript_id}/ansicht", response_class=HTMLResponse)
    def ansicht(skript_id: str):
        """Eigene Seite für die Ansicht in einem neuen Tab, wo der Browser die Datei nicht selbst zeigen kann (Word .docx)."""
        service.datei(skript_id)   # 404, wenn es das Skript nicht gibt
        return (Path(__file__).parent / "ansicht.html").read_text("utf-8")

    @api.get("/skripte/{skript_id}/vorschau")
    def vorschau(skript_id: str):
        pdf = service.vorschau_pdf(skript_id)
        if pdf is None:
            raise NotFound("Für diese Datei gibt es keine eigene Vorschau.")
        return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": "inline"})

    @api.get("/skripte/{skript_id}/fragen")
    def fragen(skript_id: str):
        return {"fragen": service.fragen(skript_id)}

    @api.get("/skripte/{skript_id}/karten")
    def karten(skript_id: str):
        return service.karten(skript_id)

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
