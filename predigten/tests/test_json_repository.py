"""Regressionstest fürs echte Repository (nicht nur den In-Memory-Fake aus test_service.py) – vor allem für
`stellen`/`verweis_ids`, die eine ähnliche Falle wie `buch_id` beim Lesenachweis sind (JSON kennt keine
Dict-Keys außer Strings, und ein vergessenes Feld beim Lesen/Schreiben fällt nur beim echten Hin-und-Zurück
auf, nie mit einem Fake, der das Domänen-Objekt einfach im Speicher behält)."""
from app.adapters.outbound.json_repository import JsonPredigtRepository
from app.domain.models import Predigt


def test_speichern_und_laden_behaelt_stellen_und_verweis_ids(tmp_path):
    repo = JsonPredigtRepository(tmp_path / "predigten.json")
    predigt = Predigt(titel="Über Johannes 3", datum="2025-01-05", prediger="Pastor A", notiz="Notiz",
                      stellen=["Joh.3.16", "Röm.8.28"],
                      verweis_ids={"Joh.3.16": "verweis-1", "Röm.8.28": "verweis-2"}, hat_datei=True)
    repo.save(predigt)

    neu_geladen = JsonPredigtRepository(tmp_path / "predigten.json")
    geladen = neu_geladen.get(predigt.id)

    assert geladen.titel == "Über Johannes 3"
    assert geladen.stellen == ["Joh.3.16", "Röm.8.28"]
    assert geladen.verweis_ids == {"Joh.3.16": "verweis-1", "Röm.8.28": "verweis-2"}
    assert geladen.hat_datei is True


def test_predigt_ohne_stellen_laedt_leere_listen_statt_zu_knallen(tmp_path):
    repo = JsonPredigtRepository(tmp_path / "predigten.json")
    repo.save(Predigt(titel="Predigt ohne Bibelstelle"))

    geladen = JsonPredigtRepository(tmp_path / "predigten.json").get(repo.list()[0].id)
    assert geladen.stellen == []
    assert geladen.verweis_ids == {}
