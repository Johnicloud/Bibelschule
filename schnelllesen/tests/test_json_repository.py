from app.adapters.outbound.json_repository import JsonEinheitRepository
from app.domain.models import Einheit


def test_speichern_und_laden_mit_durchgaengen(tmp_path):
    repo = JsonEinheitRepository(tmp_path / "einheiten.json")
    e = Einheit(buch="Joh", buch_name="Johannes", kapitel=3, text="Ein kurzer Text zum Lesen.", wortanzahl=5)
    e.durchgang_hinzufuegen(90, 3)   # Runde 1: in 90s bis Wort 3 gekommen
    e.durchgang_hinzufuegen(70, 3)   # Runde 2: derselbe Abschnitt (3 Wörter)
    repo.save(e)

    wieder = JsonEinheitRepository(tmp_path / "einheiten.json").get(e.id)
    assert wieder.buch == "Joh"
    assert wieder.kapitel == 3
    assert wieder.wortanzahl == 5
    assert wieder.segment_woerter == 3
    assert [(d.runde, d.sekunden, d.ziel_sekunden, d.woerter) for d in wieder.durchgaenge] == [
        (1, 90, 180, 3), (2, 70, 120, 3)]
    assert not wieder.fertig


def test_delete(tmp_path):
    repo = JsonEinheitRepository(tmp_path / "einheiten.json")
    e = Einheit(buch="Joh", buch_name="Johannes", kapitel=3, text="x", wortanzahl=1)
    repo.save(e)
    repo.delete(e.id)
    assert repo.get(e.id) is None
    assert repo.list() == []
