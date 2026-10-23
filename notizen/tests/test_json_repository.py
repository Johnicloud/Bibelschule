from pathlib import Path

from app.adapters.outbound.json_repository import JsonKommentarRepository
from app.domain.models import Kommentar


def test_speichert_und_liest_zurueck(tmp_path: Path):
    repo = JsonKommentarRepository(tmp_path / "kommentare.json")
    a = Kommentar(stelle="Joh.3.16", text="Erstens", verweis_id="v1")
    b = Kommentar(stelle="Joh.3.16", text="Zweitens")
    repo.save(a)
    repo.save(b)

    neu = JsonKommentarRepository(tmp_path / "kommentare.json")
    gelesen = neu.list_zu_stelle("Joh.3.16")
    assert [k.text for k in gelesen] == ["Erstens", "Zweitens"]
    assert gelesen[0].verweis_id == "v1"
    assert neu.get(a.id).stelle == "Joh.3.16"

    neu.delete(a.id)
    assert neu.get(a.id) is None
    assert [k.text for k in neu.list_zu_stelle("Joh.3.16")] == ["Zweitens"]
