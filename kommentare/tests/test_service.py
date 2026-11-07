import pytest
from app.application.ports import BibelVerweise, EintraegeRepository, QuellenRepository
from app.application.services import KommentarService
from app.domain.errors import InvalidInput, NotFound


class InMemoryQuellen(QuellenRepository):
    def __init__(self): self.d = {}
    def list(self): return list(self.d.values())
    def get(self, i): return self.d.get(i)
    def save(self, q): self.d[q.id] = q
    def delete(self, i): self.d.pop(i, None)


class InMemoryEintraege(EintraegeRepository):
    def __init__(self): self.d = {}
    def zu_stelle(self, buch_index, kapitel, vers):
        return [e for e in self.d.values() if e.buch_index == buch_index and e.kapitel == kapitel and e.deckt_ab(vers)]
    def zu_quelle(self, quelle_id): return [e for e in self.d.values() if e.quelle_id == quelle_id]
    def get(self, i): return self.d.get(i)
    def save(self, e): self.d[e.id] = e
    def save_alle(self, eintraege):
        for e in eintraege: self.d[e.id] = e
    def delete(self, i): self.d.pop(i, None)
    def delete_zu_quelle(self, quelle_id):
        betroffene = [e for e in self.d.values() if e.quelle_id == quelle_id]
        for e in betroffene: self.d.pop(e.id, None)
        return betroffene


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
    return KommentarService(InMemoryQuellen(), InMemoryEintraege(), verweise)


def _quelle(svc, titel="Dächsel, Bibelwerk"):
    return svc.quelle_anlegen(titel, "Karl August Dächsel", "de", "gemeinfrei", "https://example.org", "Dächsel, gemeinfrei")


def test_quelle_anlegen_und_auflisten(svc):
    q = _quelle(svc)
    assert [x.id for x in svc.quellen_liste()] == [q.id]


def test_quelle_ohne_titel_schlaegt_fehl(svc):
    with pytest.raises(InvalidInput):
        svc.quelle_anlegen("  ", "", "de", "", "", "")


def test_eintrag_anlegen_legt_verweis_beim_ersten_vers_des_bereichs_an(svc, verweise):
    q = _quelle(svc)
    e = svc.eintrag_anlegen(q.id, "Joh", 3, 16, 18, "Auslegung zu Joh 3,16-18.")
    assert e.vers_von == 16 and e.vers_bis == 18
    assert verweise.angelegt == [(e.verweis_id, "Joh.3.16", q.id, "Johannes 3")]


def test_eintrag_anlegen_prueft_buch_und_kapitel(svc):
    q = _quelle(svc)
    with pytest.raises(InvalidInput):
        svc.eintrag_anlegen(q.id, "Xyz", 1, 1, 1, "Text")
    with pytest.raises(InvalidInput):
        svc.eintrag_anlegen(q.id, "Jud", 2, 1, 1, "Text")   # Judas hat nur 1 Kapitel


def test_eintrag_anlegen_prueft_versbereich(svc):
    q = _quelle(svc)
    with pytest.raises(InvalidInput):
        svc.eintrag_anlegen(q.id, "Joh", 3, 18, 16, "Text")   # bis vor von


def test_eintrag_anlegen_ohne_bekannte_quelle_schlaegt_fehl(svc):
    with pytest.raises(NotFound):
        svc.eintrag_anlegen("unbekannt", "Joh", 3, 16, 16, "Text")


def test_zu_stelle_findet_eintrag_dessen_bereich_den_vers_einschliesst(svc):
    q = _quelle(svc)
    svc.eintrag_anlegen(q.id, "Joh", 3, 16, 18, "Auslegung.")
    assert len(svc.zu_stelle("Joh", 3, 17)) == 1
    assert svc.zu_stelle("Joh", 3, 19) == []


def test_quelle_loeschen_entfernt_auch_ihre_eintraege_und_verweise(svc, verweise):
    q = _quelle(svc)
    e = svc.eintrag_anlegen(q.id, "Joh", 3, 16, 16, "Text")
    svc.quelle_loeschen(q.id)
    assert svc.quellen_liste() == []
    assert svc.zu_stelle("Joh", 3, 16) == []
    assert verweise.geloescht == [e.verweis_id]


def test_eintrag_loeschen_raeumt_verweis_auf(svc, verweise):
    q = _quelle(svc)
    e = svc.eintrag_anlegen(q.id, "Joh", 3, 16, 16, "Text")
    svc.eintrag_loeschen(e.id)
    assert svc.zu_stelle("Joh", 3, 16) == []
    assert verweise.geloescht == [e.verweis_id]


def test_eintrag_anlegen_ohne_bibel_dienst_bleibt_trotzdem_gueltig(svc):
    svc2 = KommentarService(InMemoryQuellen(), InMemoryEintraege(), FakeVerweise(scheitert=True))
    q = _quelle(svc2)
    e = svc2.eintrag_anlegen(q.id, "Joh", 3, 16, 16, "Text")
    assert e.verweis_id is None
    assert svc2.zu_stelle("Joh", 3, 16) == [e]


def test_import_ersetzen_tauscht_alle_eintraege_einer_quelle_aus(svc, verweise):
    q = _quelle(svc)
    svc.import_ersetzen(q.id, [("Joh", 3, 16, 16, "Alte Fassung.")])
    alte = svc.eintraege_zu_quelle(q.id)
    assert len(alte) == 1 and alte[0].text == "Alte Fassung."

    svc.import_ersetzen(q.id, [("Joh", 3, 16, 18, "Neue Fassung."), ("Joh", 3, 19, 19, "Noch ein Eintrag.")])
    neue = svc.eintraege_zu_quelle(q.id)
    assert sorted(e.text for e in neue) == ["Neue Fassung.", "Noch ein Eintrag."]
    # Der alte Verweis wurde aufgeräumt, bevor die neuen angelegt wurden.
    assert verweise.geloescht == [alte[0].verweis_id]


def test_import_ersetzen_ueberspringt_ungueltige_eintraege_statt_abzubrechen(svc):
    q = _quelle(svc)
    neue = svc.import_ersetzen(q.id, [("Joh", 3, 16, 16, "Gültig."), ("Xyz", 1, 1, 1, "Unbekanntes Buch.")])
    assert [e.text for e in neue] == ["Gültig."]
