import tempfile
from pathlib import Path

from app.adapters.outbound.json_repository import JsonGlossarRepository
from app.domain.models import GlossarEintrag, Stellenverweis


def repo():
    return JsonGlossarRepository(Path(tempfile.mkdtemp()) / "eintraege.json")


def test_eintrag_mit_stellen_und_verweis_id_survives_a_save_and_reload():
    r = repo()
    e = GlossarEintrag(wort="λόγος", transliteration="logos", erklaerung="Wort",
                        stellen=[Stellenverweis("Joh.1.1", "v1"), Stellenverweis("Joh.1.14", None)])
    r.save(e)

    geladen = r.get(e.id)
    assert geladen.wort == "λόγος"
    assert [(s.stelle, s.verweis_id) for s in geladen.stellen] == [("Joh.1.1", "v1"), ("Joh.1.14", None)]


def test_delete_entfernt_den_eintrag():
    r = repo()
    e = GlossarEintrag(wort="πνεῦμα", transliteration="pneuma", erklaerung="Geist")
    r.save(e)
    r.delete(e.id)
    assert r.get(e.id) is None
    assert r.list() == []
