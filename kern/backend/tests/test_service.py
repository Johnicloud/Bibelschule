import pytest
from app.application.ports import ServiceGateway, SubjectRepository
from app.application.services import SubjectService
from app.domain.errors import InvalidInput, NotFound


class InMemoryRepo(SubjectRepository):
    def __init__(self): self.d = {}
    def list(self): return list(self.d.values())
    def get(self, i): return self.d.get(i)
    def save(self, s): self.d[s.id] = s
    def delete(self, i): self.d.pop(i, None)


class FakeGateway(ServiceGateway):
    """Zwei Dienste im Speicher; 'down' simuliert einen ausgefallenen Dienst."""
    def __init__(self, names=("karteikarten", "register")):
        self._names, self.down, self.known, self.deleted = list(names), set(), {n: {} for n in names}, []
        self.manifests = {n: {"label": n.capitalize(), "panel": None, "status": []} for n in names}

    def register(self, name, url):
        if name not in self._names:
            self._names.append(name)
            self.known[name], self.manifests[name] = {}, {"label": "Neu", "panel": "ui", "status": [{"key": "n", "label": "Einträge"}]}

    def manifest(self, service, live=True): return self.manifests[service]

    def list_subjects(self, service):
        """karteikarten kennt noch Fächer aus alter Zeit; register bietet keine Liste an."""
        if service in self.down or service != "karteikarten": return None
        return [{"id": i, "name": n} for i, n in self.known[service].items()]

    def names(self): return self._names
    def online(self, s): return s not in self.down

    def put_subject(self, s, i, name):
        if s in self.down: return False
        self.known[s][i] = name
        return True

    def delete_subject(self, s, i):
        if s in self.down: return False
        self.known[s].pop(i, None)
        self.deleted.append((s, i))
        return True

    def status(self, s, i): return {"n": len(self.known[s])} if i in self.known[s] else {"n": 0}
    def forward(self, service, method, path, query, body, content_type): return 200, b"{}", "application/json"


@pytest.fixture
def gw():
    return FakeGateway()


@pytest.fixture
def svc(gw):
    return SubjectService(InMemoryRepo(), gw)


def test_create_subject_reaches_all_services(svc, gw):
    subject, synced = svc.create_subject("  Dogmatik ")
    assert subject.name == "Dogmatik" and synced == {"karteikarten": True, "register": True}
    assert all(known[subject.id] == "Dogmatik" for known in gw.known.values())


def test_names_must_be_unique_and_not_empty(svc):
    svc.create_subject("Dogmatik")
    with pytest.raises(InvalidInput):
        svc.create_subject("dogmatik")
    with pytest.raises(InvalidInput):
        svc.create_subject("  ")


def test_rename_and_delete(svc, gw):
    subject, _ = svc.create_subject("Dogmatik")
    other, _ = svc.create_subject("Ethik")
    with pytest.raises(InvalidInput):
        svc.rename_subject(other.id, "Dogmatik")
    renamed, _ = svc.rename_subject(subject.id, "Dogmatik I")
    assert gw.known["register"][subject.id] == "Dogmatik I"
    assert svc.delete_subject(subject.id) == {"karteikarten": True, "register": True}
    assert [s.name for s in svc.list_subjects()] == ["Ethik"]
    with pytest.raises(NotFound):
        svc.delete_subject(subject.id)


def test_subject_is_kept_when_a_service_is_down_and_sync_repairs_it(svc, gw):
    gw.down.add("register")
    subject, synced = svc.create_subject("Dogmatik")
    assert synced == {"karteikarten": True, "register": False}
    assert svc.sync() == {"karteikarten": True, "register": False}
    gw.down.clear()
    assert svc.sync() == {"karteikarten": True, "register": True}
    assert gw.known["register"][subject.id] == "Dogmatik"


def test_overview_skips_offline_services(svc, gw):
    subject, _ = svc.create_subject("Dogmatik")
    gw.down.add("register")
    o = svc.overview()
    assert [(x["name"], x["online"]) for x in o["services"]] == [("karteikarten", True), ("register", False)]
    assert o["subjects"] == [{"id": subject.id, "name": "Dogmatik", "progress": None, "stufe": "angelegt",
                              "status": {"karteikarten": {"n": 1}, "register": None, "aufgaben": {"count": 0, "done": 0}},
                              "parts": [{"service": "aufgaben", "label": "Aufgaben", "online": True, "progress": None},
                                        {"service": "karteikarten", "label": "Karteikarten", "online": True, "progress": None},
                                        {"service": "register", "label": "Register", "online": False, "progress": None}]}]


def test_forward_only_known_services(svc):
    assert svc.forward("register", "GET", "entries", "", b"", None)[0] == 200
    with pytest.raises(NotFound):
        svc.forward("gibtesnicht", "GET", "x", "", b"", None)


def test_subjects_sorted_by_name(svc):
    for n in ("Zeitgeschichte", "ägyptisch", "Bibelkunde"):
        svc.create_subject(n)
    assert [s.name for s in svc.list_subjects()] == ["ägyptisch", "Bibelkunde", "Zeitgeschichte"]


def test_service_registers_itself_and_gets_all_subjects(svc, gw):
    subject, _ = svc.create_subject("Dogmatik")
    info = svc.register_service("vokabeln", "http://vokabeln:8000/")
    assert info["name"] == "vokabeln" and info["label"] == "Neu" and info["panel"] == "ui" and info["synced"] is True
    assert gw.known["vokabeln"][subject.id] == "Dogmatik"
    assert [s["name"] for s in svc.services_status()] == ["karteikarten", "register", "vokabeln"]


def test_register_service_rejects_bad_names_and_urls(svc):
    for bad in ("", "A", "Gross", "subjects", "mit leer", "1abc", "x" * 40):
        with pytest.raises(InvalidInput):
            svc.register_service(bad, "http://x:8000")
    with pytest.raises(InvalidInput):
        svc.register_service("vokabeln", "ftp://x")


def test_existing_subjects_of_a_service_are_adopted_not_lost(svc, gw):
    gw.known["karteikarten"] = {"alt1": "Biologie", "alt2": "Dogmatik"}   # Karten aus der Zeit vor dem Kern
    svc.create_subject("Dogmatik")                                       # Name schon vergeben im Kern
    svc.sync()
    names = sorted(s.name for s in svc.list_subjects())
    assert names == ["Biologie", "Dogmatik", "Dogmatik (2)"]
    assert svc.get_subject("alt1").name == "Biologie"                    # gleiche ID wie im Dienst: die Karten hängen dran
    assert gw.known["register"]["alt1"] == "Biologie"                    # und die anderen Dienste kennen es jetzt auch
    svc.sync()
    assert len(svc.list_subjects()) == 3                                 # zweiter Abgleich legt nichts doppelt an


def test_overview_services_carry_manifest(svc):
    first = svc.services_status()[0]
    assert first == {"name": "karteikarten", "online": True, "label": "Karteikarten", "panel": None, "fields": []}


def test_overall_progress_is_mean_of_services_that_report_one(svc, gw):
    subject, _ = svc.create_subject("Dogmatik")
    gw.status = lambda s, i: {"progress": {"karteikarten": 50, "register": None}[s]}
    row = svc.subject_overview(subject.id)
    assert row["progress"] == 50 and [p["progress"] for p in row["parts"]] == [None, 50, None]
    gw.status = lambda s, i: {"progress": {"karteikarten": 50, "register": 100}[s]}
    assert svc.overview()["subjects"][0]["progress"] == 75
    gw.down.add("register")                                        # ein Dienst fällt aus: es zählen nur die erreichbaren
    assert svc.subject_overview(subject.id)["progress"] == 50


def test_subject_overview_unknown_subject(svc):
    import pytest
    from app.domain.errors import NotFound
    with pytest.raises(NotFound):
        svc.subject_overview("gibt-es-nicht")


def test_create_subject_with_initial_aufgaben(svc):
    """Beim Anlegen kann man gleich den Umfang als Aufgaben mitgeben; leere Titel werden übersprungen."""
    subject, _ = svc.create_subject("Dogmatik", ["Exegese Kapitel 3", "  ", "Essay einreichen"])
    assert [a.titel for a in subject.aufgaben] == ["Exegese Kapitel 3", "Essay einreichen"]
    assert all(not a.erledigt for a in subject.aufgaben)


def test_add_set_and_delete_aufgabe(svc):
    subject, _ = svc.create_subject("Dogmatik")
    subject = svc.add_aufgabe(subject.id, "Exegese Kapitel 3", "2026-11-20")
    aufgabe = subject.aufgaben[0]
    assert aufgabe.titel == "Exegese Kapitel 3" and aufgabe.frist == "2026-11-20" and not aufgabe.erledigt

    subject = svc.set_aufgabe_erledigt(subject.id, aufgabe.id, True)
    assert subject.aufgaben[0].erledigt is True

    subject = svc.delete_aufgabe(subject.id, aufgabe.id)
    assert subject.aufgaben == []
    with pytest.raises(NotFound):
        svc.delete_aufgabe(subject.id, aufgabe.id)
    with pytest.raises(NotFound):
        svc.set_aufgabe_erledigt(subject.id, "gibt-es-nicht", True)


def test_set_aufgabe_pensum_links_and_unlinks(svc):
    """Verknüpft eine Aufgabe mit einem Lesenachweis-Pensum (per Id) – die Übersicht zeigt dann dessen Lesestatus."""
    subject, _ = svc.create_subject("Dogmatik")
    aufgabe = svc.add_aufgabe(subject.id, "Lesen der Pflicht-Lektüre + Lesenachweis").aufgaben[0]

    subject = svc.set_aufgabe_pensum(subject.id, aufgabe.id, "pensum-123")
    assert subject.aufgaben[0].pensum_id == "pensum-123"

    subject = svc.set_aufgabe_pensum(subject.id, aufgabe.id, None)
    assert subject.aufgaben[0].pensum_id is None


def test_set_aktive_dienste_speichert_liste_ohne_duplikate(svc):
    subject, _ = svc.create_subject("Dogmatik")
    assert subject.aktive_dienste == []

    subject = svc.set_aktive_dienste(subject.id, ["register", "karteikarten", "register"])
    assert subject.aktive_dienste == ["register", "karteikarten"]

    subject = svc.set_aktive_dienste(subject.id, [])
    assert subject.aktive_dienste == []


def test_aufgaben_progress_counts_towards_overall_progress(svc, gw):
    """Der Umfang eines Fachs zählt wie jeder Dienst zum Gesamtfortschritt mit (Anteil erledigter Aufgaben)."""
    subject, _ = svc.create_subject("Dogmatik")
    svc.add_aufgabe(subject.id, "Eins")
    zwei = svc.add_aufgabe(subject.id, "Zwei").aufgaben[1]
    svc.set_aufgabe_erledigt(subject.id, zwei.id, True)
    gw.status = lambda s, i: {"progress": None}

    row = svc.subject_overview(subject.id)
    assert row["status"]["aufgaben"] == {"count": 2, "done": 1}
    aufgaben_part = next(p for p in row["parts"] if p["service"] == "aufgaben")
    assert aufgaben_part == {"service": "aufgaben", "label": "Aufgaben", "online": True, "progress": 50}
    assert row["progress"] == 50


def test_aufgaben_progress_uses_gewichtung_like_the_aufgabenblatt(svc, gw):
    """Wie im echten Aufgabenblatt: Aufgaben zählen nach ihrer anteiligen Bewertung, nicht nach Stückzahl."""
    subject, _ = svc.create_subject("Apostelgeschichte")
    svc.add_aufgabe(subject.id, "Anwesenheit", gewichtung=10)
    klausur = svc.add_aufgabe(subject.id, "Klausur", gewichtung=50).aufgaben[-1]
    svc.add_aufgabe(subject.id, "Register", gewichtung=10)
    svc.add_aufgabe(subject.id, "Lesen", gewichtung=30)
    subject = svc.set_aufgabe_erledigt(subject.id, klausur.id, True)

    aufgaben_part, _ = svc._aufgaben_part(subject)
    assert aufgaben_part["progress"] == 50   # 50 von 100 Gewichtungspunkten (10+50+10+30) erledigt


def test_se_is_stored_on_the_subject(svc):
    subject, _ = svc.create_subject("Pädagogik I", se=2)
    assert subject.se == 2
    subject = svc.set_se(subject.id, 3.5)
    assert subject.se == 3.5 and svc.get_subject(subject.id).se == 3.5


def test_aufgaben_progress_falls_back_to_count_without_gewichtung(svc):
    subject, _ = svc.create_subject("Dogmatik", ["Eins", "Zwei", "Drei", "Vier"])
    for a in subject.aufgaben[:1]:
        subject = svc.set_aufgabe_erledigt(subject.id, a.id, True)
    aufgaben_part, _ = svc._aufgaben_part(subject)
    assert aufgaben_part["progress"] == 25


def test_fach_status_five_stages(svc, gw):
    """Die fünf Stufen ergeben sich von selbst aus dem Fortschritt, ohne eigene Pflege."""
    gw.status = lambda s, i: {"progress": None}   # Dienste melden hier nichts: nur die Aufgaben zählen
    subject, _ = svc.create_subject("Dogmatik")
    assert svc.subject_overview(subject.id)["stufe"] == "angelegt"   # frisch angelegt, keine Aufgabe

    eins = svc.add_aufgabe(subject.id, "Eins", gewichtung=25).aufgaben[-1]
    svc.add_aufgabe(subject.id, "Zwei", gewichtung=25)
    svc.add_aufgabe(subject.id, "Drei", gewichtung=25)
    klausur = svc.add_aufgabe(subject.id, "Klausur", gewichtung=25).aufgaben[-1]
    assert svc.subject_overview(subject.id)["stufe"] == "angelegt"   # 0 % erledigt

    svc.set_aufgabe_erledigt(subject.id, eins.id, True)
    assert svc.subject_overview(subject.id)["stufe"] == "begonnen"   # 25 %

    zwei = subject.aufgaben[1]
    svc.set_aufgabe_erledigt(subject.id, zwei.id, True)
    assert svc.subject_overview(subject.id)["stufe"] == "in_arbeit"   # 50 %

    drei = subject.aufgaben[2]
    svc.set_aufgabe_erledigt(subject.id, drei.id, True)
    assert svc.subject_overview(subject.id)["stufe"] == "klausur_offen"   # 75 %, nur noch die Klausur offen

    svc.set_aufgabe_erledigt(subject.id, klausur.id, True)
    assert svc.subject_overview(subject.id)["stufe"] == "abgeschlossen"   # 100 %
