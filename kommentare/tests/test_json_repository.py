import tempfile
from pathlib import Path

from app.adapters.outbound.json_repository import JsonEintraegeRepository, JsonQuellenRepository
from app.domain.models import KommentarEintrag, Quelle


def quellen_repo():
    return JsonQuellenRepository(Path(tempfile.mkdtemp()) / "quellen.json")


def eintraege_repo():
    return JsonEintraegeRepository(Path(tempfile.mkdtemp()) / "eintraege.json")


def test_quelle_survives_a_save_and_reload():
    r = quellen_repo()
    q = Quelle(titel="Dächsel, Bibelwerk", autor="Karl August Dächsel", sprache="de", lizenz="gemeinfrei",
               quell_url="https://example.org", namensnennung="Dächsel, gemeinfrei")
    r.save(q)

    geladen = r.get(q.id)
    assert geladen.titel == "Dächsel, Bibelwerk" and geladen.lizenz == "gemeinfrei"


def test_quelle_delete_entfernt_sie():
    r = quellen_repo()
    q = Quelle(titel="Schlatter", autor="Adolf Schlatter", sprache="de", lizenz="gemeinfrei")
    r.save(q)
    r.delete(q.id)
    assert r.get(q.id) is None
    assert r.list() == []


def test_eintrag_mit_versbereich_und_verweis_id_survives_a_save_and_reload():
    r = eintraege_repo()
    e = KommentarEintrag(quelle_id="q1", buch_index=42, kapitel=3, vers_von=16, vers_bis=18,
                         text="Auslegung zu Joh 3,16-18.", verweis_id="v1")
    r.save(e)

    geladen = r.get(e.id)
    assert geladen.vers_von == 16 and geladen.vers_bis == 18 and geladen.verweis_id == "v1"


def test_zu_stelle_findet_nur_eintraege_deren_bereich_den_vers_einschliesst():
    r = eintraege_repo()
    r.save(KommentarEintrag(quelle_id="q1", buch_index=42, kapitel=3, vers_von=16, vers_bis=18, text="A"))
    r.save(KommentarEintrag(quelle_id="q1", buch_index=42, kapitel=3, vers_von=19, vers_bis=19, text="B"))
    treffer = r.zu_stelle(42, 3, 17)
    assert [e.text for e in treffer] == ["A"]


def test_delete_zu_quelle_entfernt_nur_die_eintraege_dieser_quelle_und_gibt_sie_zurueck():
    r = eintraege_repo()
    e1 = KommentarEintrag(quelle_id="q1", buch_index=42, kapitel=3, vers_von=16, vers_bis=16, text="A")
    e2 = KommentarEintrag(quelle_id="q2", buch_index=42, kapitel=3, vers_von=16, vers_bis=16, text="B")
    r.save(e1)
    r.save(e2)
    geloescht = r.delete_zu_quelle("q1")
    assert [e.id for e in geloescht] == [e1.id]
    assert r.get(e1.id) is None
    assert r.get(e2.id) is not None


def test_save_alle_speichert_mehrere_eintraege_auf_einmal():
    r = eintraege_repo()
    eintraege = [KommentarEintrag(quelle_id="q1", buch_index=42, kapitel=3, vers_von=i, vers_bis=i, text=str(i))
                for i in (16, 17, 18)]
    r.save_alle(eintraege)
    assert len(r.zu_quelle("q1")) == 3
