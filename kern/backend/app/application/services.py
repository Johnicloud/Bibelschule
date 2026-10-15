"""Anwendungsfälle des Kerns. Kennen nur Domäne und Ports."""
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor

from app.application.ports import ServiceGateway, SubjectRepository
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Aufgabe, Subject


# Diese Namen gehören dem Kern selbst und dürfen kein Dienst sein.
RESERVED = {"subjects", "services", "sync", "overview", "registry", "health", "docs", "openapi.json", "redoc", "noten"}
SERVICE_NAME = re.compile(r"^[a-z][a-z0-9-]{1,30}$")


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

    def create_subject(self, name: str, aufgaben: list[str] = (), se: float | None = None) -> tuple[Subject, dict[str, bool]]:
        name = _clean(name)
        self._check_unique(name)
        titel = [_clean(t) for t in aufgaben if (t or "").strip()]
        subject = Subject(name=name, aufgaben=[Aufgabe(titel=t) for t in titel], se=se)
        self.subjects.save(subject)
        return subject, self._fan_out(lambda s: self.gateway.put_subject(s, subject.id, subject.name))

    def rename_subject(self, subject_id: str, name: str) -> tuple[Subject, dict[str, bool]]:
        subject = self._subject(subject_id)
        name = _clean(name)
        self._check_unique(name, subject.id)
        subject.name = name
        self.subjects.save(subject)
        return subject, self._fan_out(lambda s: self.gateway.put_subject(s, subject.id, subject.name))

    def set_se(self, subject_id: str, se: float | None) -> Subject:
        """Studieneinheiten (SE) des Fachs; Credits = se * 1.5 (neues System) werden nur angezeigt, nicht gespeichert."""
        subject = self._subject(subject_id)
        subject.se = se
        self.subjects.save(subject)
        return subject

    def set_note(self, subject_id: str, note: float | None) -> Subject:
        """Abschlussnote des Fachs, deutsche Notenskala 1,0 (sehr gut) bis 5,0 (nicht ausreichend)."""
        if note is not None and not 1.0 <= note <= 5.0:
            raise InvalidInput("Die Note liegt zwischen 1,0 und 5,0.")
        subject = self._subject(subject_id)
        subject.note = note
        self.subjects.save(subject)
        return subject

    def notenuebersicht(self) -> dict:
        """Allgemeine Auswertung aller benoteten Fächer: Durchschnitt gewichtet nach Studieneinheiten (SE);
        Fächer ohne SE zählen dabei wie ein Fach mit einer SE (gleiches Vorgehen wie bei der Aufgaben-Gewichtung:
        vorhandene Gewichte zählen entsprechend mehr, fehlende wie ein normaler Anteil)."""
        benotet = [s for s in self.subjects.list() if s.note is not None]
        gewicht = lambda s: s.se if s.se else 1
        summe_gewicht = sum(gewicht(s) for s in benotet)
        durchschnitt = round(sum(s.note * gewicht(s) for s in benotet) / summe_gewicht, 2) if benotet else None
        faecher = sorted(({"id": s.id, "name": s.name, "note": s.note, "se": s.se} for s in benotet),
                         key=lambda f: _sort_key(f["name"]))
        return {"durchschnitt": durchschnitt, "anzahl": len(benotet), "faecher": faecher}

    def delete_subject(self, subject_id: str) -> dict[str, bool]:
        subject = self._subject(subject_id)
        self.subjects.delete(subject.id)
        return self._fan_out(lambda s: self.gateway.delete_subject(s, subject.id))

    # Aufgaben: der Umfang eines Fachs (z. B. aus dem Aufgabenblatt)
    def _aufgabe(self, subject: Subject, aufgabe_id: str) -> Aufgabe:
        for a in subject.aufgaben:
            if a.id == aufgabe_id:
                return a
        raise NotFound("Aufgabe nicht gefunden.")

    def add_aufgabe(self, subject_id: str, titel: str, frist: str | None = None,
                     gewichtung: float | None = None) -> Subject:
        subject = self._subject(subject_id)
        subject.aufgaben.append(Aufgabe(titel=_clean(titel), frist=frist or None, gewichtung=gewichtung))
        self.subjects.save(subject)
        return subject

    def set_aufgabe_erledigt(self, subject_id: str, aufgabe_id: str, erledigt: bool) -> Subject:
        subject = self._subject(subject_id)
        self._aufgabe(subject, aufgabe_id).erledigt = erledigt
        self.subjects.save(subject)
        return subject

    def delete_aufgabe(self, subject_id: str, aufgabe_id: str) -> Subject:
        subject = self._subject(subject_id)
        self._aufgabe(subject, aufgabe_id)
        subject.aufgaben = [a for a in subject.aufgaben if a.id != aufgabe_id]
        self.subjects.save(subject)
        return subject

    def set_aufgabe_pensum(self, subject_id: str, aufgabe_id: str, pensum_id: str | None) -> Subject:
        """Verknüpft eine Aufgabe mit einem Pensum des Lesenachweis-Diensts (oder löst die Verknüpfung, pensum_id=None).
        Die Übersicht zeigt dann für diese Aufgabe den echten Lesestatus statt eines einfachen Häkchens."""
        subject = self._subject(subject_id)
        self._aufgabe(subject, aufgabe_id).pensum_id = pensum_id or None
        self.subjects.save(subject)
        return subject

    def set_aktive_dienste(self, subject_id: str, dienste: list[str]) -> Subject:
        subject = self._subject(subject_id)
        subject.aktive_dienste = list(dict.fromkeys(dienste))   # doppelte raus, Reihenfolge bleibt
        self.subjects.save(subject)
        return subject

    # Dienstverzeichnis
    def register_service(self, name: str, url: str) -> dict:
        """Ein Dienst meldet sich an (Plug-in). Er bekommt sofort alle Fächer; seine eigenen werden übernommen."""
        if not SERVICE_NAME.match(name or "") or name in RESERVED:
            raise InvalidInput("Der Dienstname besteht aus Kleinbuchstaben, Ziffern und Bindestrich (2 bis 31 Zeichen).")
        if not re.match(r"^https?://[^\s/]+", url or ""):
            raise InvalidInput("Die Adresse des Dienstes muss mit http:// oder https:// beginnen.")
        self.gateway.register(name, url.rstrip("/"))
        synced = self.sync().get(name, False)
        return {**next(s for s in self.services_status() if s["name"] == name), "synced": synced}

    def services_status(self) -> list[dict]:
        names = self.gateway.names()

        def info(name: str) -> dict:
            online = self.gateway.online(name)
            m = self.gateway.manifest(name, live=online)
            return {"name": name, "online": online, "label": m.get("label") or name.capitalize(),
                    "panel": m.get("panel"), "fields": m.get("status") or []}
        with ThreadPoolExecutor(max_workers=max(len(names), 1)) as pool:
            return list(pool.map(info, names))

    def _adopt(self) -> None:
        """Fächer, die ein Dienst schon hat (z. B. alte Karteikarten), werden Fächer des Kerns: Daten gehen nicht verloren."""
        found = self._fan_out(self.gateway.list_subjects)
        for name in self.gateway.names():
            for item in found.get(name) or []:
                if self.subjects.get(item["id"]) is None:
                    self.subjects.save(Subject(id=item["id"], name=self._free_name(item.get("name") or "Fach")))

    def _free_name(self, name: str) -> str:
        taken = {s.name.casefold() for s in self.subjects.list()}
        candidate, n = name, 1
        while candidate.casefold() in taken:
            n += 1
            candidate = f"{name} ({n})"
        return candidate

    def sync(self) -> dict[str, bool]:
        """Übernimmt vorhandene Fächer der Dienste und meldet alle Fächer allen Diensten.
        Gefahrlos mehrfach aufrufbar, z. B. nach einem Neustart."""
        self._adopt()
        subjects = self.subjects.list()
        return self._fan_out(lambda s: all([self.gateway.put_subject(s, sub.id, sub.name) for sub in subjects]))

    # Übersicht
    def _collect(self, subjects: list[Subject], services: list[dict]) -> dict[str, dict]:
        """Fragt jeden erreichbaren Dienst nach dem Stand jedes Fachs (parallel)."""
        up = [s["name"] for s in services if s["online"]]
        jobs = [(sub, s) for sub in subjects for s in up]
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda job: self.gateway.status(job[1], job[0].id), jobs))
        status = {sub.id: {s["name"]: None for s in services} for sub in subjects}
        for (sub, service), result in zip(jobs, results):
            status[sub.id][service] = result
        return status

    @staticmethod
    def _progress(status: dict, services: list[dict]) -> tuple[int | None, list[dict]]:
        """Gesamtfortschritt eines Fachs: Mittel aller Dienste, die im Status ein `progress` (0 bis 100) melden.
        Neue Dienste zählen automatisch mit, sobald sie `progress` liefern."""
        parts = []
        for s in services:
            st = status.get(s["name"])
            value = st.get("progress") if isinstance(st, dict) else None
            ok = isinstance(value, (int, float)) and not isinstance(value, bool)
            parts.append({"service": s["name"], "label": s["label"], "online": s["online"],
                          "progress": value if ok else None})
        values = [p["progress"] for p in parts if p["progress"] is not None]
        return (int(sum(values) / len(values) + 0.5) if values else None), parts

    @staticmethod
    def _aufgaben_part(subject: Subject) -> tuple[dict, dict]:
        """Umfang des Fachs als eigener Teil des Fortschritts: Anteil erledigter Aufgaben.
        Hat eine Aufgabe eine Gewichtung (wie die „Anteilige Bewertung“ im Aufgabenblatt), zählt sie entsprechend
        mehr oder weniger; ohne Gewichtung zählt jede Aufgabe gleich viel."""
        total = len(subject.aufgaben)
        done = sum(1 for a in subject.aufgaben if a.erledigt)
        weight = sum(a.gewichtung for a in subject.aufgaben if a.gewichtung)
        if weight:
            done_weight = sum(a.gewichtung for a in subject.aufgaben if a.erledigt and a.gewichtung)
            progress = max(0, min(100, int(done_weight / weight * 100 + 0.5)))
        elif total:
            progress = int(done / total * 100 + 0.5)
        else:
            progress = None
        return ({"service": "aufgaben", "label": "Aufgaben", "online": True, "progress": progress},
                {"count": total, "done": done})

    @staticmethod
    def _fach_status(subject: Subject, progress: int | None) -> str:
        """Fünf Stufen, aus dem Gesamtfortschritt und den Aufgaben hergeleitet – keine eigene Pflege nötig.
        Ist nur noch eine Aufgabe offen, deren Titel „Klausur“ enthält, bekommt das Fach eine eigene Stufe
        dafür (wie im Aufgabenblatt: die Klausur steht meist am Ende, mit eigenem Termin)."""
        offene = [a for a in subject.aufgaben if not a.erledigt]
        klausur_offen = [a for a in offene if "klausur" in a.titel.casefold()]
        sonst_offen = [a for a in offene if a not in klausur_offen]
        if klausur_offen and not sonst_offen and progress is not None and progress < 100:
            return "klausur_offen"
        if progress is None or progress == 0:
            return "angelegt"
        if progress < 50:
            return "begonnen"
        if progress < 100:
            return "in_arbeit"
        return "abgeschlossen"

    def _row(self, sub: Subject, status: dict, services: list[dict]) -> dict:
        aufgaben_part, aufgaben_status = self._aufgaben_part(sub)
        _, service_parts = self._progress(status, services)
        parts = [aufgaben_part, *service_parts]
        values = [p["progress"] for p in parts if p["progress"] is not None]
        progress = int(sum(values) / len(values) + 0.5) if values else None
        return {"id": sub.id, "name": sub.name, "status": {**status, "aufgaben": aufgaben_status},
                "progress": progress, "stufe": self._fach_status(sub, progress), "parts": parts}

    def overview(self) -> dict:
        services = self.services_status()
        subjects = self.list_subjects()
        status = self._collect(subjects, services)
        return {"services": services, "subjects": [self._row(sub, status[sub.id], services) for sub in subjects]}

    def subject_overview(self, subject_id: str) -> dict:
        """Stand eines einzelnen Fachs inklusive Gesamtfortschritt."""
        subject = self._subject(subject_id)
        services = self.services_status()
        return self._row(subject, self._collect([subject], services)[subject.id], services)

    # Weiterleitung: die Oberfläche spricht nur mit dem Kern, der Kern mit den Diensten
    def forward(self, service: str, method: str, path: str, query: str, body: bytes,
                content_type: str | None) -> tuple[int, bytes, str]:
        if service not in self.gateway.names():
            raise NotFound(f"Einen Dienst „{service}“ gibt es nicht.")
        return self.gateway.forward(service, method, path, query, body, content_type)
