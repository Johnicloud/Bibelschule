import tempfile
from datetime import date
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup


def test_atomic_write_replaces_and_leaves_no_temp_files():
    d = Path(tempfile.mkdtemp())
    f = d / "daten.json"
    atomic_write_text(f, "eins")
    atomic_write_text(f, "zwei")
    assert f.read_text("utf-8") == "zwei" and [p.name for p in d.iterdir()] == ["daten.json"]


def test_daily_backup_once_per_day_and_pruned():
    d = Path(tempfile.mkdtemp())
    f = d / "daten.json"
    daily_backup(f, date(2026, 10, 1))                      # noch keine Datei: nichts passiert
    assert not (d / "backups").exists()
    f.write_text("alt", "utf-8")
    daily_backup(f, date(2026, 10, 1))
    f.write_text("neu", "utf-8")
    daily_backup(f, date(2026, 10, 1))                      # am selben Tag nicht nochmal
    assert (d / "backups" / "daten-2026-10-01.json").read_text("utf-8") == "alt"
    for day in range(2, 6):
        daily_backup(f, date(2026, 10, day), keep=3)
    assert [p.name for p in sorted((d / "backups").iterdir())] == [
        "daten-2026-10-03.json", "daten-2026-10-04.json", "daten-2026-10-05.json"]
