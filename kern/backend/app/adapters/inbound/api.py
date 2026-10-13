"""Eingehender Adapter: HTTP-API des Kerns. Die Oberfläche spricht nur hier.
Eigene Wege: /api/subjects, /api/services, /api/registry, /api/sync, /api/overview.
Alles andere: /api/<dienst>/... wird an den Dienst weitergereicht (z. B. /api/karteikarten/decks).
Interaktive Doku: /api/docs"""
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from app.application.auth_service import AuthService
from app.application.services import SubjectService
from app.domain.errors import InvalidInput, NotFound, Unauthorized
from app.domain.models import Subject

SESSION_COOKIE = "session"
# Ohne Anmeldung erreichbar: Gesundheitscheck, Selbstanmeldung der Dienste (interner Docker-Verkehr,
# kommt nicht vom Browser) und die Anmeldung selbst.
PUBLIC_PATHS = {"/api/health", "/api/registry", "/api/login"}


class SubjectIn(BaseModel):
    name: str
    aufgaben: list[str] = []   # Umfang des Fachs, gleich bei der Anlage: Titel der ersten Aufgaben
    se: float | None = None    # Studieneinheiten (alt); Credits = se * 1.5 (neues System)


class SeIn(BaseModel):
    se: float | None = None


class AufgabeIn(BaseModel):
    titel: str
    frist: str | None = None
    gewichtung: float | None = None   # anteilige Bewertung in Prozent, wie im Aufgabenblatt


class AufgabeStatusIn(BaseModel):
    erledigt: bool


class RegistryIn(BaseModel):
    name: str
    url: str


class LoginIn(BaseModel):
    username: str
    password: str


class PasswordIn(BaseModel):
    old_password: str
    new_password: str


def subject_out(s: Subject, synced: dict[str, bool] | None = None) -> dict:
    out = {"id": s.id, "name": s.name, "se": s.se, "credits": round(s.se * 1.5, 2) if s.se is not None else None,
           "aufgaben": [{"id": a.id, "titel": a.titel, "frist": a.frist, "gewichtung": a.gewichtung,
                         "erledigt": a.erledigt} for a in s.aufgaben]}
    if synced is not None:
        out["synced"] = synced   # welcher Dienst das Fach übernommen hat (false = nicht erreichbar, später /api/sync)
    return out


def create_app(service: SubjectService, auth: AuthService) -> FastAPI:
    app = FastAPI(title="Bibelschule (Kern)", docs_url="/api/docs", openapi_url="/api/openapi.json")
    api = APIRouter(prefix="/api")

    @app.middleware("http")
    async def require_login(request: Request, call_next):
        """Alles außer PUBLIC_PATHS braucht eine gültige Sitzung (Cookie). Konten legt man per Skript an
        (./neues-konto.sh), keine Selbstregistrierung. Schützt damit auch jeden weitergereichten Dienst
        (/api/<dienst>/…), da die Oberfläche nur über den Kern spricht."""
        if request.url.path not in PUBLIC_PATHS:
            token = request.cookies.get(SESSION_COOKIE)
            if auth.current_account(token) is None:
                return JSONResponse({"detail": "Bitte anmelden."}, status_code=401)
        return await call_next(request)

    @app.exception_handler(NotFound)
    async def _not_found(_, e):
        return JSONResponse({"detail": str(e)}, status_code=404)

    @app.exception_handler(InvalidInput)
    async def _invalid(_, e):
        return JSONResponse({"detail": str(e)}, status_code=422)

    @app.exception_handler(Unauthorized)
    async def _unauthorized(_, e):
        return JSONResponse({"detail": str(e)}, status_code=401)

    @api.get("/health")
    def health():
        return {"status": "ok"}

    @api.post("/login")
    def login(body: LoginIn, response: Response):
        token = auth.login(body.username, body.password)
        response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", path="/", max_age=60 * 60 * 24 * 30)
        return {"username": body.username.strip()}

    @api.post("/logout", status_code=204)
    def logout(request: Request, response: Response):
        token = request.cookies.get(SESSION_COOKIE)
        if token:
            auth.logout(token)
        response.delete_cookie(SESSION_COOKIE, path="/")

    @api.get("/me")
    def me(request: Request):
        account = auth.current_account(request.cookies.get(SESSION_COOKIE))
        return {"username": account.username}

    @api.put("/me/password", status_code=204)
    def change_password(request: Request, body: PasswordIn):
        account = auth.current_account(request.cookies.get(SESSION_COOKIE))
        auth.change_password(account.id, body.old_password, body.new_password)

    @api.get("/accounts")
    def list_accounts():
        """Nur die Benutzernamen, nie der Passwort-Hash."""
        return [{"username": a.username} for a in auth.list_accounts()]

    @api.post("/accounts", status_code=201)
    def create_account(body: LoginIn):
        """Ein schon angemeldetes Konto darf weitere Konten anlegen (eingeladene Personen); keine Selbstregistrierung."""
        return {"username": auth.create_account(body.username, body.password).username}

    @api.get("/subjects")
    def list_subjects():
        return [subject_out(s) for s in service.list_subjects()]

    @api.post("/subjects", status_code=201)
    def create_subject(body: SubjectIn):
        return subject_out(*service.create_subject(body.name, body.aufgaben, body.se))

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

    @api.post("/subjects/{subject_id}/aufgaben", status_code=201)
    def add_aufgabe(subject_id: str, body: AufgabeIn):
        return subject_out(service.add_aufgabe(subject_id, body.titel, body.frist, body.gewichtung))

    @api.put("/subjects/{subject_id}/aufgaben/{aufgabe_id}")
    def set_aufgabe_erledigt(subject_id: str, aufgabe_id: str, body: AufgabeStatusIn):
        return subject_out(service.set_aufgabe_erledigt(subject_id, aufgabe_id, body.erledigt))

    @api.delete("/subjects/{subject_id}/aufgaben/{aufgabe_id}", status_code=204)
    def delete_aufgabe(subject_id: str, aufgabe_id: str):
        service.delete_aufgabe(subject_id, aufgabe_id)

    @api.put("/subjects/{subject_id}/se")
    def set_se(subject_id: str, body: SeIn):
        return subject_out(service.set_se(subject_id, body.se))

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
