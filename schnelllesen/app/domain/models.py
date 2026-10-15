"""Domäne: reine Python-Objekte, kein Framework, kein Speicher.

3-2-1-Methode: dasselbe Kapitel wird dreimal gelesen, mit sinkender Zielzeit (3, dann 2, dann 1 Minute) –
man übt dadurch, denselben Text immer schneller zu lesen. Fachübergreifend (wie der Bibel-Dienst selbst):
eine Einheit gehört zu keinem Fach."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

ZIEL_SEKUNDEN = (180, 120, 60)   # Runde 1, 2, 3: 3-2-1 Minuten
RUNDEN = len(ZIEL_SEKUNDEN)


def new_id() -> str:
    return uuid4().hex


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Durchgang:
    runde: int           # 1, 2 oder 3
    sekunden: float       # tatsächlich gebrauchte Zeit
    ziel_sekunden: int     # Vorgabe dieser Runde (ZIEL_SEKUNDEN[runde - 1])


@dataclass
class Einheit:
    buch: str             # Kurzname, z. B. "Joh"
    buch_name: str
    kapitel: int
    text: str              # Verstext des Kapitels, vom Bibel-Dienst geholt
    wortanzahl: int
    id: str = field(default_factory=new_id)
    erstellt: str = field(default_factory=_now)
    durchgaenge: list[Durchgang] = field(default_factory=list)

    @property
    def naechste_runde(self) -> int | None:
        return len(self.durchgaenge) + 1 if len(self.durchgaenge) < RUNDEN else None

    @property
    def fertig(self) -> bool:
        return len(self.durchgaenge) >= RUNDEN

    def durchgang_hinzufuegen(self, sekunden: float) -> Durchgang:
        runde = self.naechste_runde
        d = Durchgang(runde=runde, sekunden=sekunden, ziel_sekunden=ZIEL_SEKUNDEN[runde - 1])
        self.durchgaenge.append(d)
        return d

    def wpm(self, d: Durchgang) -> float:
        return round(self.wortanzahl / (d.sekunden / 60), 1) if d.sekunden > 0 else 0.0
