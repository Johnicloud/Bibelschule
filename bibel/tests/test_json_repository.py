from app.adapters.outbound.json_repository import JsonVersRepository
from app.domain.models import Vers


def test_suche_findet_gespeicherte_verse_nach_dem_neu_laden(tmp_path):
    repo = JsonVersRepository(tmp_path / "verse.json")
    repo.ersetze_alle([
        Vers(buch_index=0, kapitel=1, vers=1, text="Im Anfang schuf Gott die Himmel und die Erde.", id="1Mo.1.1"),
        Vers(buch_index=0, kapitel=1, vers=2, text="Die Erde aber war wüst und leer.", id="1Mo.1.2"),
        Vers(buch_index=42, kapitel=3, vers=16, text="Denn also hat Gott die Welt geliebt.", id="Joh.3.16"),
    ])
    treffer = repo.suche("erde")
    assert {v.id for v in treffer} == {"1Mo.1.1", "1Mo.1.2"}


def test_suche_ist_case_insensitive(tmp_path):
    repo = JsonVersRepository(tmp_path / "verse.json")
    repo.ersetze_alle([Vers(buch_index=0, kapitel=1, vers=1, text="Im Anfang", id="1Mo.1.1")])
    assert len(repo.suche("ANFANG")) == 1


def test_suche_ohne_datei_ist_leer(tmp_path):
    repo = JsonVersRepository(tmp_path / "fehlt.json")
    assert repo.suche("egal") == []
