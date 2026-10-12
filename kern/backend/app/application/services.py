"""Anwendungsfälle des Kerns. Kennen nur Domäne und Ports."""
import unicodedata
from concurrent.futures import ThreadPoolExecutor

from app.application.ports import ServiceGateway, SubjectRepository
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Subject


def _clean(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise InvalidInput("Der Name darf nicht leer sein.")
    return text


def _sort_key(name: str) -> str:
    """Alphabetisch nach deutscher Regel: Ä wie A, Ö wie O, Ü wie U; Groß/Klein egal."""
    t = unicodedata.normalize("NFKD", name).casefold()
    return "".join(c for c in t if not unicodedata.combining(c))


class SubjectService:
    def __init__(self, subjects: SubjectRepository, gateway: ServiceGateway):
        self.subjects = subjects
        self.gateway = gateway

    def _subject(self, subject_id: str) -> Subject:
        subject = self.subjects.get(subject_id)
        if subject is None:
            raise NotFound("Fach nicht gefunden.")
        return subject

    def _fan_out(self, fn) -> dict[str, bool]:
        names = self.gateway.names()
        with ThreadPoolExecutor(max_workers=max(len(names), 1)) as pool:
            return dict(zip(names, pool.map(fn, names)))

    def _check_unique(self, name: str, own_id: str | None = None) -> None:
        if any(s.name.casefold() == name.casefold() and s.id != own_id for s in self.subjects.list()):
            raise InvalidInput("Dieses Fach gibt es schon.")

    # Fächer
    def list_subjects(self) -> list[Subject]:
        return sorted(self.subjects.list(), key=lambda s: _sort_key(s.name))

    def get_subject(self, subject_id: str) -> Subject:
        return self._subject(subject_id)

    def create_subject(self, name: str) -> tuple[Subject, dict[str, bool]]:
        name = _clean(name)
        self._check_unique(name)
        subject = Subject(name=name)
        self.subjects.save(subject)
        return subject, self._fan_out(lambda s: self.gateway.put_subject(s, subject.id, subject.name))

    def rename_subject(self, subject_id: str, name: str) -> tuple[Subject, dict[str, bool]]:
        subject = self._subject(subject_id)
        name = _clean(name)
        self._check_unique(name, subject.id)
        subject.name = name
        self.subjects.save(subject)
        return subject, self._fan_out(lambda s: self.gateway.put_subject(s, subject.id, subject.name))

    def delete_subject(self, subject_id: str) -> dict[str, bool]:
        subject = self._subject(subject_id)
        self.subjects.delete(subject.id)
        return self._fan_out(lambda s: self.gateway.delete_subject(s, subject.id))

    # Dienstverzeichnis
    def services_status(self) -> list[dict]:
        names = self.gateway.names()
        with ThreadPoolExecutor(max_workers=max(len(names), 1)) as pool:
            online = list(pool.map(self.gateway.online, names))
        return [{"name": n, "online": o} for n, o in zip(names, online)]

    def sync(self) -> dict[str, bool]:
        """Meldet alle Fächer allen Diensten. Gefahrlos mehrfach aufrufbar, z. B. nach einem Neustart."""
        subjects = self.subjects.list()
        return self._fan_out(lambda s: all([self.gateway.put_subject(s, sub.id, sub.name) for sub in subjects]))

    # Übersicht
    def overview(self) -> dict:
        services = self.services_status()
        up = [s["name"] for s in services if s["online"]]
        subjects = self.list_subjects()
        jobs = [(sub, s) for sub in subjects for s in up]
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda job: self.gateway.status(job[1], job[0].id), jobs))
        status = {sub.id: {s["name"]: None for s in services} for sub in subjects}
        for (sub, service), result in zip(jobs, results):
            status[sub.id][service] = result
        return {"services": services,
                "subjects": [{"id": sub.id, "name": sub.name, "status": status[sub.id]} for sub in subjects]}

    # Weiterleitung: die Oberfläche spricht nur mit dem Kern, der Kern mit den Diensten
    def forward(self, service: str, method: str, path: str, query: str, body: bytes,
                content_type: str | None) -> tuple[int, bytes, str]:
        if service not in self.gateway.names():
            raise NotFound(f"Einen Dienst „{service}“ gibt es nicht.")
        return self.gateway.forward(service, method, path, query, body, content_type)
