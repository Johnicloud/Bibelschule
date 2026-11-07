"""Ausgehender Adapter: speichert die Buch-Seiten-Zuordnung (nicht die PDF-Datei selbst) in einer JSON-Datei."""
import json
import threading
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.application.ports import IndexRepository, VersRepository, VerweisRepository
from app.domain.models import Bibelindex, Buchseite, Vers, Verweis


class JsonIndexRepository(IndexRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def get(self) -> Bibelindex | None:
        with self._lock:
            if not self.path.exists():
                return None
            d = json.loads(self.path.read_text("utf-8"))
            return Bibelindex(
                dateiname=d.get("dateiname"),
                buchseiten=[Buchseite(buch_index=b["buch_index"], seite=b.get("seite"), erkannt=b.get("erkannt", False))
                            for b in d.get("buchseiten", [])])

    def save(self, index: Bibelindex) -> None:
        with self._lock:
            daily_backup(self.path)
            data = {"dateiname": index.dateiname,
                    "buchseiten": [{"buch_index": b.buch_index, "seite": b.seite, "erkannt": b.erkannt}
                                   for b in index.buchseiten]}
            atomic_write_text(self.path, json.dumps(data, ensure_ascii=False, indent=2))


class JsonVersRepository(VersRepository):
    """Eine Datei mit allen Versen (die ganze Bibel passt gut in eine JSON-Datei). Tägliche Sicherung bewusst
    weg gelassen wie beim Dateiinhalt selbst – ein erneutes Hochladen baut den Bestand ohnehin neu auf."""
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _lesen(self) -> list[Vers]:
        if not self.path.exists():
            return []
        d = json.loads(self.path.read_text("utf-8"))
        return [Vers(buch_index=v["buch_index"], kapitel=v["kapitel"], vers=v["vers"], text=v["text"],
                     id=v.get("id", "")) for v in d]

    def ersetze_alle(self, verse: list[Vers]) -> None:
        with self._lock:
            data = [{"buch_index": v.buch_index, "kapitel": v.kapitel, "vers": v.vers, "text": v.text, "id": v.id}
                    for v in verse]
            atomic_write_text(self.path, json.dumps(data, ensure_ascii=False, indent=2))

    def kapitel(self, buch_index: int, kapitel: int) -> list[Vers]:
        with self._lock:
            verse = [v for v in self._lesen() if v.buch_index == buch_index and v.kapitel == kapitel]
        return sorted(verse, key=lambda v: v.vers)

    def vers(self, buch_index: int, kapitel: int, vers: int) -> Vers | None:
        with self._lock:
            return next((v for v in self._lesen() if v.buch_index == buch_index and v.kapitel == kapitel
                        and v.vers == vers), None)

    def alle(self) -> list[Vers]:
        with self._lock:
            return sorted(self._lesen(), key=lambda v: (v.buch_index, v.kapitel, v.vers))

    def hat_verse(self) -> bool:
        with self._lock:
            return self.path.exists() and self.path.stat().st_size > 2


class JsonVerweisRepository(VerweisRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _lesen(self) -> list[Verweis]:
        if not self.path.exists():
            return []
        d = json.loads(self.path.read_text("utf-8"))
        return [Verweis(id=v["id"], stelle=v["stelle"], art=v["art"], referenz=v["referenz"], titel=v.get("titel"))
                for v in d]

    def _schreiben(self, verweise: list[Verweis]) -> None:
        daily_backup(self.path)
        data = [{"id": v.id, "stelle": v.stelle, "art": v.art, "referenz": v.referenz, "titel": v.titel}
                for v in verweise]
        atomic_write_text(self.path, json.dumps(data, ensure_ascii=False, indent=2))

    def speichere(self, verweis: Verweis) -> None:
        with self._lock:
            verweise = [v for v in self._lesen() if v.id != verweis.id]
            verweise.append(verweis)
            self._schreiben(verweise)

    def zu_stelle(self, stelle: str) -> list[Verweis]:
        with self._lock:
            return [v for v in self._lesen() if v.stelle == stelle]

    def loesche(self, verweis_id: str) -> None:
        with self._lock:
            self._schreiben([v for v in self._lesen() if v.id != verweis_id])
