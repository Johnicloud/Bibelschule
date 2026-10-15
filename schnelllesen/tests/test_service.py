import pytest
from app.application.ports import BibelQuelle, EinheitRepository
from app.application.services import SchnelllesenService
from app.domain.errors import InvalidInput, NotFound


class InMemoryRepo(EinheitRepository):
    def __init__(self): self.d = {}
    def list(self): return sorted(self.d.values(), key=lambda e: e.erstellt, reverse=True)
    def get(self, i): return self.d.get(i)
    def save(self, e): self.d[e.id] = e
    def delete(self, i): self.d.pop(i, None)


class FakeBibel(BibelQuelle):
    """Hat nur für Johannes 3 schon Verstext – wie ein Bibel-Dienst, der noch nicht alles eingelesen hat."""
    def kapitel(self, buch_kurz, kapitel):
        if buch_kurz == "Joh" and kapitel == 3:
            return "Es war aber ein Mensch unter den Pharisäern, der hieß Nikodemus."
        return ""


@pytest.fixture
def svc():
    return SchnelllesenService(InMemoryRepo(), FakeBibel())


def test_neue_einheit_holt_text_vom_bibel_dienst(svc):
    e = svc.neue_einheit("Joh", 3)
    assert e.buch == "Joh"
    assert e.buch_name == "Johannes"
    assert e.wortanzahl == 11
    assert e.naechste_runde == 1
    assert not e.fertig


def test_neue_einheit_ohne_verstext(svc):
    with pytest.raises(NotFound):
        svc.neue_einheit("Joh", 4)


def test_unbekanntes_buch_oder_kapitel(svc):
    with pytest.raises(InvalidInput):
        svc.neue_einheit("Xyz", 1)
    with pytest.raises(InvalidInput):
        svc.neue_einheit("Joh", 99)


def test_drei_durchgaenge_mit_sinkender_zielzeit(svc):
    e = svc.neue_einheit("Joh", 3)
    e = svc.durchgang_abschliessen(e.id, 40)
    assert e.durchgaenge[0].runde == 1
    assert e.durchgaenge[0].ziel_sekunden == 180
    assert round(e.wpm(e.durchgaenge[0]), 1) == round(11 / (40 / 60), 1)

    e = svc.durchgang_abschliessen(e.id, 30)
    assert e.durchgaenge[1].ziel_sekunden == 120

    e = svc.durchgang_abschliessen(e.id, 20)
    assert e.durchgaenge[2].ziel_sekunden == 60
    assert e.fertig
    assert e.naechste_runde is None

    with pytest.raises(InvalidInput):
        svc.durchgang_abschliessen(e.id, 15)


def test_ungueltige_zeit(svc):
    e = svc.neue_einheit("Joh", 3)
    with pytest.raises(InvalidInput):
        svc.durchgang_abschliessen(e.id, 0)
    with pytest.raises(InvalidInput):
        svc.durchgang_abschliessen(e.id, -5)


def test_unbekannte_einheit(svc):
    with pytest.raises(NotFound):
        svc.durchgang_abschliessen("nope", 10)
    with pytest.raises(NotFound):
        svc.get("nope")


def test_liste_neueste_zuerst(svc):
    a = svc.neue_einheit("Joh", 3)
    b = svc.neue_einheit("Joh", 3)
    assert [e.id for e in svc.liste()] == [b.id, a.id]


def test_loeschen(svc):
    e = svc.neue_einheit("Joh", 3)
    svc.loeschen(e.id)
    assert svc.liste() == []


