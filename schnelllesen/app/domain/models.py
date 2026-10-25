"""Domäne: reine Python-Objekte, kein Framework, kein Speicher.

3-2-1-Methode, wie sie tatsächlich geübt wird: in Runde 1 wird 3 Minuten lang im ganzen Kapitel gelesen,
danach markiert man, wie weit man gekommen ist – dieser Abschnitt (`segment_woerter`) ist dann in Runde 2
(2 Minuten) und Runde 3 (1 Minute) der GANZE Text, den es zu lesen gibt. Man liest also denselben, schon
bekannten Abschnitt noch zweimal, in immer weniger Zeit – das trainiert das Tempo, nicht das Durchhalten.
Fachübergreifend (wie der Bibel-Dienst selbst): eine Einheit gehört zu keinem Fach."""
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
    woerter: int           # Wortzahl des in dieser Runde gelesenen Textes (Runde 1: wie weit gekommen,
                            # Runde 2/3: die ganze Länge des Abschnitts aus Runde 1)


@dataclass
class Einheit:
    buch: str             # Kurzname, z. B. "Joh"
    buch_name: str
    kapitel: int
    text: str              # Verstext des ganzen Kapitels, vom Bibel-Dienst geholt
    wortanzahl: int         # Wortzahl des ganzen Kapitels (nur für Runde 1 relevant)
    id: str = field(default_factory=new_id)
    erstellt: str = field(default_factory=_now)
    durchgaenge: list[Durchgang] = field(default_factory=list)
    segment_woerter: int | None = None   # ab Runde 2 gesetzt: wie weit man in Runde 1 gekommen ist

    @property
    def naechste_runde(self) -> int | None:
        return len(self.durchgaenge) + 1 if len(self.durchgaenge) < RUNDEN else None

    @property
    def fertig(self) -> bool:
        return len(self.durchgaenge) >= RUNDEN

    def text_fuer_runde(self, runde: int) -> str:
        """Runde 1: das ganze Kapitel (man weiß ja noch nicht, wie weit man kommt). Ab Runde 2: nur noch
        der Abschnitt aus Runde 1 – derselbe Text, den man schon einmal gelesen hat, jetzt mit weniger Zeit."""
        if runde == 1 or self.segment_woerter is None:
            return self.text
        return " ".join(self.text.split()[: self.segment_woerter])

    def durchgang_hinzufuegen(self, sekunden: float, woerter: int) -> Durchgang:
        runde = self.naechste_runde
        d = Durchgang(runde=runde, sekunden=sekunden, ziel_sekunden=ZIEL_SEKUNDEN[runde - 1], woerter=woerter)
        self.durchgaenge.append(d)
        if runde == 1:
            self.segment_woerter = woerter
        return d

    def wpm(self, d: Durchgang) -> float:
        return round(d.woerter / (d.sekunden / 60), 1) if d.sekunden > 0 else 0.0
