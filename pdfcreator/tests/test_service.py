import pytest
from app.application.ports import DateiSpeicher, PdfRenderer, TextKI, VorlageRepository
from app.application.services import PdfService
from app.domain.errors import InvalidInput, NotFound
from app.domain.standard_vorlage import STANDARD_VORLAGE_ID, standard_vorlage


class InMemoryVorlagen(VorlageRepository):
    def __init__(self): self.d = {}
    def list(self): return list(self.d.values())
    def get(self, i): return self.d.get(i)
    def save(self, v): self.d[v.id] = v
    def delete(self, i): self.d.pop(i, None)


class InMemoryDateien(DateiSpeicher):
    def __init__(self): self.d = {}
    def speichere(self, i, inhalt): self.d[i] = inhalt
    def lies(self, i): return self.d.get(i)
    def loesche(self, i): self.d.pop(i, None)


class FakeRenderer(PdfRenderer):
    """Statt echtem PDF: merkt sich nur, womit es aufgerufen wurde."""
    def __init__(self): self.letzter_aufruf = None
    def fuelle(self, vorlage_pdf, werte, felder):
        self.letzter_aufruf = (vorlage_pdf, werte, felder)
        return b"%PDF-ausgefuellt"
    def text_auslesen(self, pdf):
        return "Fach: ___  Name: ___"


class FakeKI(TextKI):
    def frage(self, prompt): return "- Fach\n- Name\n- Gemeinde"


@pytest.fixture
def vorlagen():
    repo = InMemoryVorlagen()
    repo.save(standard_vorlage())
    return repo


@pytest.fixture
def dateien():
    d = InMemoryDateien()
    d.speichere(STANDARD_VORLAGE_ID, b"%PDF-vorlage")
    return d


@pytest.fixture
def renderer():
    return FakeRenderer()


@pytest.fixture
def svc(vorlagen, dateien, renderer):
    return PdfService(vorlagen, dateien, renderer, ki=FakeKI())


def test_fuellen_merges_buecher_into_werte(svc, renderer):
    pdf = svc.fuellen(STANDARD_VORLAGE_ID, {"fach": "Apostelgeschichte", "name": "Johannes Löwen"},
                       buecher=[{"titel": "Die Apostelgeschichte", "seiten": 200}])
    assert pdf == b"%PDF-ausgefuellt"
    _, werte, felder = renderer.letzter_aufruf
    assert werte["fach"] == "Apostelgeschichte" and werte["buch_0_titel"] == "Die Apostelgeschichte"
    assert werte["buch_0_seiten"] == "200"
    assert any(f.schluessel == "buch_0_titel" for f in felder)


def test_fuellen_rejects_too_many_buecher(svc):
    with pytest.raises(InvalidInput):
        svc.fuellen(STANDARD_VORLAGE_ID, {}, buecher=[{"titel": f"B{i}", "seiten": 1} for i in range(7)])


def test_fuellen_unknown_vorlage_raises_not_found(svc):
    with pytest.raises(NotFound):
        svc.fuellen("gibt-es-nicht", {})


def test_hochladen_speichert_datei_und_ki_vorschlag(svc, dateien):
    vorlage = svc.hochladen("Mein Formular", "formular.pdf", b"%PDF-neu")
    assert vorlage.felder == []   # Positionen trägt man von Hand ein
    assert vorlage.ki_vorschlag == "- Fach\n- Name\n- Gemeinde"
    assert dateien.lies(vorlage.id) == b"%PDF-neu"


def test_hochladen_requires_name(svc):
    with pytest.raises(InvalidInput):
        svc.hochladen(" ", "x.pdf", b"%PDF")


def test_standard_vorlage_kann_nicht_geloescht_werden(svc):
    with pytest.raises(InvalidInput):
        svc.delete(STANDARD_VORLAGE_ID)


def test_delete_entfernt_vorlage_und_datei(svc, dateien):
    vorlage = svc.hochladen("Weg damit", "x.pdf", b"%PDF")
    svc.delete(vorlage.id)
    assert svc.vorlagen.get(vorlage.id) is None
    assert dateien.lies(vorlage.id) is None
    with pytest.raises(NotFound):
        svc.delete(vorlage.id)
