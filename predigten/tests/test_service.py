import pytest
from app.application.ports import BibelVerweise, DateiSpeicher, PredigtRepository
from app.application.services import PredigtenService
from app.domain.errors import InvalidInput, NotFound


class InMemoryRepo(PredigtRepository):
    def __init__(self): self.d = {}
    def list(self): return list(self.d.values())
    def get(self, i): return self.d.get(i)
    def save(self, predigt): self.d[predigt.id] = predigt
    def delete(self, i): self.d.pop(i, None)


class InMemoryDateien(DateiSpeicher):
    def __init__(self): self._dateien = {}
    def speichere(self, predigt_id, inhalt): self._dateien[predigt_id] = inhalt
    def lies(self, predigt_id): return self._dateien.get(predigt_id)
    def loesche(self, predigt_id): self._dateien.pop(predigt_id, None)


class FakeBibelVerweise(BibelVerweise):
    """Tut so, als wäre der Bibel-Dienst erreichbar: vergibt fortlaufende IDs, merkt sich, was angelegt/
    gelöscht wurde, damit Tests prüfen können, dass predigten den Bibel-Dienst wirklich anspricht."""
    def __init__(self):
        self.angelegt = []       # [(stelle, referenz)]
        self.geloescht = []
        self._zaehler = 0

    def anlegen(self, stelle, referenz):
        self._zaehler += 1
        verweis_id = f"verweis-{self._zaehler}"
        self.angelegt.append((stelle, referenz))
        return verweis_id

    def loeschen(self, verweis_id):
        self.geloescht.append(verweis_id)


@pytest.fixture
def verweise():
    return FakeBibelVerweise()


@pytest.fixture
def svc(verweise):
    return PredigtenService(InMemoryRepo(), InMemoryDateien(), verweise)


def test_add_predigt_requires_a_title(svc):
    with pytest.raises(InvalidInput):
        svc.add_predigt("  ")


def test_add_and_list_sorted_by_date_descending(svc):
    svc.add_predigt("Alte Predigt", datum="2024-01-01")
    svc.add_predigt("Neue Predigt", datum="2025-06-01")
    assert [p.titel for p in svc.list_predigten()] == ["Neue Predigt", "Alte Predigt"]


def test_update_and_delete(svc):
    p = svc.add_predigt("Alter Titel", prediger="Pastor A")
    updated = svc.update_predigt(p.id, "Neuer Titel", "2025-01-05", "Pastor B", "Notiz", [])
    assert updated.titel == "Neuer Titel" and updated.prediger == "Pastor B" and updated.notiz == "Notiz"
    svc.delete_predigt(p.id)
    assert svc.list_predigten() == []
    with pytest.raises(NotFound):
        svc.delete_predigt(p.id)


def test_add_predigt_legt_verweis_je_bibelstelle_an(svc, verweise):
    p = svc.add_predigt("Über Johannes 3", stellen=["Joh 3,16"])
    assert p.stellen == ["Joh.3.16"]
    assert p.verweis_ids == {"Joh.3.16": "verweis-1"}
    assert verweise.angelegt == [("Joh.3.16", p.id)]


def test_stelle_ohne_vers_zeigt_auf_ersten_vers_des_kapitels(svc):
    p = svc.add_predigt("Über Psalm 23", stellen=["Ps 23"])
    assert p.stellen == ["Ps.23.1"]


def test_doppelt_genannte_stelle_bleibt_einmal(svc):
    p = svc.add_predigt("Doppelt", stellen=["Joh 3,16", "Joh 3,16"])
    assert p.stellen == ["Joh.3.16"]


def test_unbekannte_stelle_lehnt_ab(svc):
    with pytest.raises(InvalidInput):
        svc.add_predigt("Predigt", stellen=["Nirgendwo 1,1"])


def test_update_entfernt_verweis_fuer_gestrichene_stelle_und_legt_neuen_an(svc, verweise):
    p = svc.add_predigt("Predigt", stellen=["Joh 3,16"])
    updated = svc.update_predigt(p.id, "Predigt", None, None, None, ["Röm 8,28"])
    assert updated.stellen == ["Röm.8.28"]
    assert verweise.geloescht == ["verweis-1"]
    assert updated.verweis_ids == {"Röm.8.28": "verweis-2"}


def test_update_behaelt_unveraenderte_stelle_ohne_neuen_verweis(svc, verweise):
    p = svc.add_predigt("Predigt", stellen=["Joh 3,16"])
    svc.update_predigt(p.id, "Predigt", None, None, None, ["Joh 3,16", "Röm 8,28"])
    assert len(verweise.angelegt) == 2   # Joh.3.16 nur einmal, dazu neu Röm.8.28
    assert verweise.geloescht == []


def test_delete_predigt_entfernt_alle_verweise(svc, verweise):
    p = svc.add_predigt("Predigt", stellen=["Joh 3,16", "Röm 8,28"])
    svc.delete_predigt(p.id)
    assert sorted(verweise.geloescht) == ["verweis-1", "verweis-2"]


def test_verweis_fehler_bricht_das_anlegen_nicht_ab():
    class KaputteVerweise(BibelVerweise):
        def anlegen(self, stelle, referenz): return None   # wie bei nicht erreichbarem Bibel-Dienst
        def loeschen(self, verweis_id): pass

    svc = PredigtenService(InMemoryRepo(), verweise=KaputteVerweise())
    p = svc.add_predigt("Predigt", stellen=["Joh 3,16"])
    assert p.stellen == ["Joh.3.16"]
    assert p.verweis_ids == {}


def test_ohne_verdrahteten_bibel_dienst_bleibt_stelle_trotzdem_gespeichert():
    svc = PredigtenService(InMemoryRepo())   # kein verweise-Adapter
    p = svc.add_predigt("Predigt", stellen=["Joh 3,16"])
    assert p.stellen == ["Joh.3.16"]
    assert p.verweis_ids == {}


# Fach-Hooks: fachübergreifend, reine No-ops
def test_discard_subject_und_subject_status_sind_no_ops(svc):
    svc.discard_subject("fach-1")   # darf nicht knallen
    assert svc.subject_status("fach-1") == {}


def test_datei_hochladen_speichert_und_markiert_die_predigt(svc):
    p = svc.add_predigt("Predigt mit Datei")
    assert p.hat_datei is False
    p = svc.datei_hochladen(p.id, b"%PDF-fake")
    assert p.hat_datei is True
    assert svc.datei(p.id) == b"%PDF-fake"


def test_datei_hochladen_rejects_empty_file(svc):
    p = svc.add_predigt("Predigt")
    with pytest.raises(InvalidInput):
        svc.datei_hochladen(p.id, b"")


def test_datei_ohne_wiring_meldet_nicht_verfuegbar():
    svc = PredigtenService(InMemoryRepo())   # keine Datei-Ablage verdrahtet
    p = svc.add_predigt("Predigt")
    with pytest.raises(InvalidInput):
        svc.datei_hochladen(p.id, b"%PDF-fake")
    assert svc.datei(p.id) is None
