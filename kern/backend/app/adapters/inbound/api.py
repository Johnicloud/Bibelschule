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
from app.domain.errors import Forbidden, InvalidInput, NotFound, Unauthorized
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


class AufgabePensumIn(BaseModel):
    pensum_id: str | None = None   # Verknüpfung mit einem Lesenachweis-Pensum, oder null zum Lösen


class AktiveDiensteIn(BaseModel):
    dienste: list[str]


class RegistryIn(BaseModel):
    name: str
    url: str


class LoginIn(BaseModel):
    username: str
    password: str


class PasswordIn(BaseModel):
    old_password: str
    new_password: str


class AccountIn(BaseModel):
    username: str
    password: str
    is_admin: bool = False


class ProfileIn(BaseModel):
    vorname: str = ""
    nachname: str = ""
    gemeinde: str = ""


class AdminStatusIn(BaseModel):
    is_admin: bool


def account_out(account) -> dict:
    return {"username": account.username, "is_admin": account.is_admin, "vorname": account.vorname,
            "nachname": account.nachname, "gemeinde": account.gemeinde,
            "muss_passwort_aendern": account.muss_passwort_aendern}


def subject_out(s: Subject, synced: dict[str, bool] | None = None) -> dict:
    out = {"id": s.id, "name": s.name, "se": s.se, "credits": round(s.se * 1.5, 2) if s.se is not None else None,
           "aufgaben": [{"id": a.id, "titel": a.titel, "frist": a.frist, "gewichtung": a.gewichtung,
                         "erledigt": a.erledigt, "pensum_id": a.pensum_id} for a in s.aufgaben],
           "aktive_dienste": s.aktive_dienste}
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

    @app.exception_handler(Forbidden)
    async def _forbidden(_, e):
        return JSONResponse({"detail": str(e)}, status_code=403)

    @api.get("/health")
    def health():
        return {"status": "ok"}

    @api.post("/login")
    def login(body: LoginIn, response: Response):
        token = auth.login(body.username, body.password)
        response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", path="/", max_age=60 * 60 * 24 * 30)
        return account_out(auth.current_account(token))

    @api.post("/logout", status_code=204)
    def logout(request: Request, response: Response):
        token = request.cookies.get(SESSION_COOKIE)
        if token:
            auth.logout(token)
        response.delete_cookie(SESSION_COOKIE, path="/")

    @api.get("/me")
    def me(request: Request):
        return account_out(auth.current_account(request.cookies.get(SESSION_COOKIE)))

    @api.put("/me/password", status_code=204)
    def change_password(request: Request, body: PasswordIn):
        account = auth.current_account(request.cookies.get(SESSION_COOKIE))
        auth.change_password(account.id, body.old_password, body.new_password)

    @api.put("/me")
    def update_profile(request: Request, body: ProfileIn):
        """Vorname/Nachname/Gemeinde fürs eigene Profil – u. a. Vorbelegung beim Lesenachweis-PDF-Export."""
        account = auth.current_account(request.cookies.get(SESSION_COOKIE))
        return account_out(auth.update_profile(account.id, body.vorname, body.nachname, body.gemeinde))

    def _require_admin(request: Request):
        account = auth.current_account(request.cookies.get(SESSION_COOKIE))
        if not account.is_admin:
            raise Forbidden("Nur Admins dürfen das.")

    @api.get("/accounts")
    def list_accounts(request: Request):
        """Nur Admins; nie der Passwort-Hash."""
        _require_admin(request)
        return [{"username": a.username, "is_admin": a.is_admin, "muss_passwort_aendern": a.muss_passwort_aendern}
                for a in auth.list_accounts()]

    @api.post("/accounts", status_code=201)
    def create_account(request: Request, body: AccountIn):
        """Nur Admins dürfen neue Konten (auch neue Admins) anlegen; keine Selbstregistrierung."""
        _require_admin(request)
        account = auth.create_account(body.username, body.password, body.is_admin)
        return {"username": account.username, "is_admin": account.is_admin}

    @api.put("/accounts/{username}/admin")
    def set_account_admin(request: Request, username: str, body: AdminStatusIn):
        """Admin-Recht nachträglich geben/entziehen (wie bei der Finanzapp) – der letzte Admin kann es sich
        nicht selbst nehmen, das prüft der Anwendungsfall."""
        _require_admin(request)
        account = auth.set_is_admin(username, body.is_admin)
        return {"username": account.username, "is_admin": account.is_admin}

    @api.post("/accounts/{username}/reset-password")
    def reset_account_password(request: Request, username: str):
        """Setzt ein zufälliges, temporäres Passwort und meldet das Konto überall ab; es muss sich beim
        nächsten Anmelden selbst ein neues Passwort wählen. Die Antwort zeigt das temporäre Passwort EINMAL –
        der Admin muss es dem Benutzer auf einem anderen Weg mitteilen (z. B. mündlich)."""
        _require_admin(request)
        temp_password = auth.reset_password(username)
        return {"temporaeres_passwort": temp_password}

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

    @api.put("/subjects/{subject_id}/aufgaben/{aufgabe_id}/pensum")
    def set_aufgabe_pensum(subject_id: str, aufgabe_id: str, body: AufgabePensumIn):
        return subject_out(service.set_aufgabe_pensum(subject_id, aufgabe_id, body.pensum_id))

    @api.put("/subjects/{subject_id}/dienste")
    def set_aktive_dienste(subject_id: str, body: AktiveDiensteIn):
        """Welche optionalen Dienste (Register/Karteikarten/Bibelverse/Skripte) für dieses Fach eingeblendet
        sind – steuert sowohl den Reiter in der Fach-Seite als auch die Kachel in der Übersicht."""
        return subject_out(service.set_aktive_dienste(subject_id, body.dienste))

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
