import json
import tempfile
from datetime import date
from pathlib import Path

from app.adapters.outbound.json_repository import JsonReadingRepository
from app.domain.models import Buch, ReadingEntry, ReadingTask


def repo():
    return JsonReadingRepository(Path(tempfile.mkdtemp()) / "tasks.json")


def test_entry_buch_id_survives_a_save_and_reload():
    """Bug: buch_id fehlte in _to_dict/_from_dict, ging beim Speichern spurlos verloren – ein Eintrag landete
    nach dem nächsten Laden immer bei „ohne Buch zugeordnet“, egal welches Buch beim Eintragen gewählt wurde."""
    r = repo()
    buch = Buch(title="Edition C Ap Teil 1", total=251)
    task = ReadingTask(subject_id="f1", title="Pflichtlektüre", unit="Seiten", total=251, buecher=[buch])
    task.entries.append(ReadingEntry(day=date(2026, 10, 14), amount=5, buch_id=buch.id))
    r.save(task)

    geladen = r.get(task.id)
    assert geladen.entries[0].buch_id == buch.id
    assert geladen.buch_done(buch.id) == 5


def test_entry_without_buch_id_stays_none_after_reload():
    r = repo()
    task = ReadingTask(subject_id="f1", title="Einfaches Pensum", unit="Seiten", total=100)
    task.entries.append(ReadingEntry(day=date(2026, 10, 14), amount=10))
    r.save(task)

    geladen = r.get(task.id)
    assert geladen.entries[0].buch_id is None


def test_entry_durchlauf_survives_a_save_and_reload():
    r = repo()
    task = ReadingTask(subject_id="f1", title="Apostelgeschichte", unit="Seiten", total=10, passes=3)
    task.entries.append(ReadingEntry(day=date(2026, 10, 14), amount=5, durchlauf=1))
    task.entries.append(ReadingEntry(day=date(2026, 10, 14), amount=7, durchlauf=2))
    r.save(task)

    geladen = r.get(task.id)
    assert geladen.durchlauf_done(1) == 5 and geladen.durchlauf_done(2) == 7 and geladen.durchlauf_done(3) == 0


def test_entry_without_durchlauf_defaults_to_1_after_reload():
    """Alte Einträge von vor dieser Funktion haben kein durchlauf-Feld in der Datei – zählen zum ersten Durchgang."""
    r = repo()
    task = ReadingTask(subject_id="f1", title="Buch", unit="Seiten", total=10, passes=2)
    task.entries.append(ReadingEntry(day=date(2026, 10, 14), amount=4))
    r.save(task)
    # Datei von Hand auf den alten Stand ohne "durchlauf" zurückstutzen, wie bei echten Altdaten
    data = json.loads(r.path.read_text("utf-8"))
    del data[0]["entries"][0]["durchlauf"]
    r.path.write_text(json.dumps(data), "utf-8")

    geladen = r.get(task.id)
    assert geladen.entries[0].durchlauf == 1
