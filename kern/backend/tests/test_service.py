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
    assert o["subjects"] == [{"id": subject.id, "name": "Dogmatik", "progress": None,
                              "status": {"karteikarten": {"n": 1}, "register": None},
                              "parts": [{"service": "karteikarten", "label": "Karteikarten", "online": True, "progress": None},
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
    assert row["progress"] == 50 and [p["progress"] for p in row["parts"]] == [50, None]
    gw.status = lambda s, i: {"progress": {"karteikarten": 50, "register": 100}[s]}
    assert svc.overview()["subjects"][0]["progress"] == 75
    gw.down.add("register")                                        # ein Dienst fällt aus: es zählen nur die erreichbaren
    assert svc.subject_overview(subject.id)["progress"] == 50


def test_subject_overview_unknown_subject(svc):
    import pytest
    from app.domain.errors import NotFound
    with pytest.raises(NotFound):
        svc.subject_overview("gibt-es-nicht")
