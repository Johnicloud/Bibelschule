import pytest
from app.application.ports import BibelVerweise, GlossarRepository
from app.application.services import GlossarService
from app.domain.errors import InvalidInput, NotFound


class InMemoryRepo(GlossarRepository):
    def __init__(self): self.d = {}
    def list(self): return list(self.d.values())
    def get(self, i): return self.d.get(i)
    def save(self, e): self.d[e.id] = e
    def delete(self, i): self.d.pop(i, None)


class FakeVerweise(BibelVerweise):
    """Merkt sich jeden angelegten/gelöschten Verweis, statt den Bibel-Dienst wirklich zu rufen."""
    def __init__(self, scheitert: bool = False):
        self.angelegt = []
        self.geloescht = []
        self.scheitert = scheitert
        self._next = 0

    def anlegen(self, stelle, referenz, titel):
        if self.scheitert:
            raise RuntimeError("Bibel-Dienst nicht erreichbar.")
        self._next += 1
        vid = f"v{self._next}"
        self.angelegt.append((vid, stelle, referenz, titel))
        return vid

    def loeschen(self, verweis_id):
        if self.scheitert:
            raise RuntimeError("Bibel-Dienst nicht erreichbar.")
        self.geloescht.append(verweis_id)


@pytest.fixture
def verweise():
    return FakeVerweise()


@pytest.fixture
def svc(verweise):
    return GlossarService(InMemoryRepo(), verweise)


def test_create_legt_verweis_je_stelle_an(svc, verweise):
    e = svc.create("ἀγάπη", "agapē", "selbstlose Liebe", ["Joh 3,16", "1Kor 13,4"])
    assert [s.stelle for s in e.stellen] == ["Joh.3.16", "1Kor.13.4"]
    assert [v[1] for v in verweise.angelegt] == ["Joh.3.16", "1Kor.13.4"]
    assert all(v[2] == e.id and v[3] == "ἀγάπη" for v in verweise.angelegt)


def test_create_ohne_wort_schlaegt_fehl(svc):
    with pytest.raises(InvalidInput):
        svc.create("  ", "", "", [])


def test_create_braucht_einen_vers_nicht_nur_ein_kapitel(svc):
    with pytest.raises(InvalidInput):
        svc.create("λόγος", "logos", "Wort", ["Joh 1"])


def test_create_ohne_bibel_dienst_bleibt_stelle_trotzdem_erhalten():
    svc = GlossarService(InMemoryRepo(), FakeVerweise(scheitert=True))
    e = svc.create("χάρις", "charis", "Gnade", ["Eph 2,8"])
    assert [s.stelle for s in e.stellen] == ["Eph.2.8"]
    assert e.stellen[0].verweis_id is None


def test_doppelte_stellen_werden_nur_einmal_angelegt(svc, verweise):
    e = svc.create("πίστις", "pistis", "Glaube", ["Hebr 11,1", "Hebr 11,1"])
    assert [s.stelle for s in e.stellen] == ["Hebr.11.1"]
    assert len(verweise.angelegt) == 1


def test_list_entries_ist_alphabetisch(svc):
    svc.create("ω", "", "", [])
    svc.create("α", "", "", [])
    assert [e.wort for e in svc.list_entries()] == ["α", "ω"]


def test_update_entfernt_nicht_mehr_genannte_stellen_und_laesst_gebliebene_in_ruhe(svc, verweise):
    e = svc.create("ἐλπίς", "elpis", "Hoffnung", ["Röm 8,24", "1Kor 13,13"])
    behaltene_id = e.stellen[0].verweis_id

    updated = svc.update(e.id, "ἐλπίς", "elpis", "Hoffnung (überarbeitet)", ["Röm 8,24", "Hebr 11,1"])

    assert sorted(s.stelle for s in updated.stellen) == ["Hebr.11.1", "Röm.8.24"]
    behaltener = next(s for s in updated.stellen if s.stelle == "Röm.8.24")
    assert behaltener.verweis_id == behaltene_id          # nicht erneut angelegt
    assert verweise.geloescht == [next(v[0] for v in verweise.angelegt if v[1] == "1Kor.13.13")]


def test_update_unbekannter_eintrag_wirft_not_found(svc):
    with pytest.raises(NotFound):
        svc.update("nope", "x", "", "", [])


def test_delete_raeumt_alle_verweise_auf(svc, verweise):
    e = svc.create("σάρξ", "sarx", "Fleisch", ["Röm 8,5", "Gal 5,17"])
    svc.delete(e.id)
    assert sorted(verweise.geloescht) == sorted(v[0] for v in verweise.angelegt)
    with pytest.raises(NotFound):
        svc.get(e.id)


def test_delete_unbekannter_eintrag_wirft_not_found(svc):
    with pytest.raises(NotFound):
        svc.delete("nope")
