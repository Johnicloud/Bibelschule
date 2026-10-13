"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json (auch für übergeordnete Services nutzbar)."""
from datetime import date
from typing import Literal

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.application.services import ReadingService
from app.domain.errors import InvalidInput, NotFound
from app.domain.forecast import Forecast
from app.domain.models import ReadingTask


class TaskIn(BaseModel):
    subject_id: str
    title: str
    unit: Literal["Seiten", "Kapitel"] = "Seiten"
    total: int
    passes: int = 1
    start: date | None = None
    deadline: date | None = None


class EntryIn(BaseModel):
    amount: int
    day: date | None = None   # leer = heute
    note: str = ""


class SubjectIn(BaseModel):
    name: str


def _round(x: float | None) -> float | None:
    return None if x is None else round(x, 1)


def forecast_out(f: Forecast) -> dict:
    return {"target": f.target, "done": f.done, "remaining": f.remaining, "percent": round(f.percent, 1),
            "days_left": f.days_left, "needed_per_day": _round(f.needed_per_day),
            "pace_per_day": _round(f.pace_per_day), "plan_per_day": _round(f.plan_per_day),
            "projected_finish": f.projected_finish.isoformat() if f.projected_finish else None,
            "status": f.status}


def create_app(service: ReadingService) -> FastAPI:
    app = FastAPI(title="Lesenachweis", docs_url="/api/docs", openapi_url="/api/openapi.json")
    api = APIRouter(prefix="/api")

    def task_out(t: ReadingTask) -> dict:
        entries = sorted(t.entries, key=lambda e: (e.day, e.id), reverse=True)
        return {"id": t.id, "subject_id": t.subject_id, "title": t.title, "unit": t.unit,
                "total": t.total, "passes": t.passes,
                "start": t.start.isoformat() if t.start else None,
                "deadline": t.deadline.isoformat() if t.deadline else None,
                "entries": [{"id": e.id, "day": e.day.isoformat(), "amount": e.amount, "note": e.note}
                            for e in entries],
                "forecast": forecast_out(service.forecast_for(t))}

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
        return {"name": "lesenachweis", "label": "Lesenachweis", "panel": None,
                "status": [{"key": "percent", "label": "% gelesen"}]}

    @api.get("/tasks")
    def list_tasks(subject_id: str | None = None):
        return [task_out(t) for t in service.list_tasks(subject_id)]

    @api.post("/tasks", status_code=201)
    def add_task(body: TaskIn):
        return task_out(service.add_task(body.subject_id, body.title, body.unit, body.total,
                                         body.passes, body.start, body.deadline))

    @api.get("/tasks/{task_id}")
    def get_task(task_id: str):
        return task_out(service.get_task(task_id))

    @api.delete("/tasks/{task_id}", status_code=204)
    def delete_task(task_id: str):
        service.delete_task(task_id)

    @api.post("/tasks/{task_id}/entries", status_code=201)
    def log_reading(task_id: str, body: EntryIn):
        return task_out(service.log_reading(task_id, body.amount, body.day, body.note))

    @api.delete("/tasks/{task_id}/entries/{entry_id}")
    def delete_entry(task_id: str, entry_id: str):
        return task_out(service.delete_entry(task_id, entry_id))

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
