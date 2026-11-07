import pytest
from app.application.ports import BibelVerweise, KommentarRepository
from app.application.services import NotizenService
from app.domain.errors import InvalidInput, NotFound


class InMemoryRepo(KommentarRepository):
    def __init__(self):
        self.d = {}

    def list_zu_stelle(self, stelle):
        return [k for k in self.d.values() if k.stelle == stelle]

    def get(self, kommentar_id):
        return self.d.get(kommentar_id)

    def save(self, kommentar):
        self.d[kommentar.id] = kommentar

    def delete(self, kommentar_id):
        self.d.pop(kommentar_id, None)


class FakeBibelVerweise(BibelVerweise):
    """Verhält sich wie der echte Bibel-Dienst: wirft InvalidInput bei einer unbekannten Stelle, sonst eine ID."""
    def __init__(self):
        self.angelegt = []
        self.geloescht = []
        self.erreichbar = True

    def anlegen(self, stelle, referenz, titel):
        if not self.erreichbar:
            return None
        if stelle == "Unsinn.1.1":
            raise InvalidInput("Diese Bibelstelle kenne ich nicht.")
        verweis_id = f"verweis-{referenz}"
        self.angelegt.append((stelle, referenz, titel))
        return verweis_id

    def loeschen(self, verweis_id):
        self.geloescht.append(verweis_id)


@pytest.fixture
def verweise():
    return FakeBibelVerweise()


@pytest.fixture
def svc(verweise):
    return NotizenService(InMemoryRepo(), verweise)


def test_anlegen_meldet_verweis_an(svc, verweise):
    k = svc.kommentar_anlegen("Joh.3.16", " Gott hat die Welt so sehr geliebt. ")
    assert k.text == "Gott hat die Welt so sehr geliebt."
    assert k.verweis_id == f"verweis-{k.id}"
    assert verweise.angelegt == [("Joh.3.16", k.id, "Gott hat die Welt so sehr geliebt.")]


def test_anlegen_ohne_text_oder_stelle(svc):
    with pytest.raises(InvalidInput):
        svc.kommentar_anlegen("Joh.3.16", "   ")
    with pytest.raises(InvalidInput):
        svc.kommentar_anlegen("  ", "Text")


def test_anlegen_mit_ungueltiger_stelle_wird_nicht_gespeichert(svc):
    with pytest.raises(InvalidInput):
        svc.kommentar_anlegen("Unsinn.1.1", "Text")
    assert svc.liste_zu_stelle("Unsinn.1.1") == []


def test_anlegen_ohne_erreichbaren_bibel_dienst(svc, verweise):
    verweise.erreichbar = False
    k = svc.kommentar_anlegen("Joh.3.16", "Text")
    assert k.verweis_id is None


def test_liste_und_loeschen(svc, verweise):
    a = svc.kommentar_anlegen("Joh.3.16", "Erstens")
    svc.kommentar_anlegen("Joh.3.17", "Anderswo")
    assert [k.text for k in svc.liste_zu_stelle("Joh.3.16")] == ["Erstens"]
    svc.loeschen(a.id)
    assert svc.liste_zu_stelle("Joh.3.16") == []
    assert verweise.geloescht == [a.verweis_id]
    with pytest.raises(NotFound):
        svc.loeschen(a.id)


def test_liste_ohne_stelle(svc):
    with pytest.raises(InvalidInput):
        svc.liste_zu_stelle("")
