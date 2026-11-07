"""Bibelbücher (66, evangelische Reihenfolge), nur Buch + Kapitelzahl – mehr braucht dieser Dienst nicht
(ganze Kapitel, keine einzelnen Verse oder Bereiche). Eigene Kopie des gleichnamigen Moduls im Bibel-Dienst
(Dienste teilen keinen Code, nur die Fach-ID) – Kurznamen und Reihenfolge bewusst identisch gehalten."""
import re
from dataclasses import dataclass

# (Kurzname nach Lutherbibel, ausgeschriebener Name, weitere Schreibweisen, Zahl der Kapitel)
_BOOKS: list[tuple[str, str, list[str], int]] = [
    ("1Mo", "1. Mose", ["Genesis", "Gen", "1 Mose"], 50),
    ("2Mo", "2. Mose", ["Exodus", "Ex", "Exod", "2 Mose"], 40),
    ("3Mo", "3. Mose", ["Levitikus", "Lev", "3 Mose"], 27),
    ("4Mo", "4. Mose", ["Numeri", "Num", "4 Mose"], 36),
    ("5Mo", "5. Mose", ["Deuteronomium", "Dtn", "Deut", "5 Mose"], 34),
    ("Jos", "Josua", [], 24),
    ("Ri", "Richter", [], 21),
    ("Rut", "Rut", ["Ruth", "Rt"], 4),
    ("1Sam", "1. Samuel", [], 31),
    ("2Sam", "2. Samuel", [], 24),
    ("1Kön", "1. Könige", ["1Kö", "1Kg"], 22),
    ("2Kön", "2. Könige", ["2Kö", "2Kg"], 25),
    ("1Chr", "1. Chronik", [], 29),
    ("2Chr", "2. Chronik", [], 36),
    ("Esr", "Esra", [], 10),
    ("Neh", "Nehemia", [], 13),
    ("Est", "Ester", ["Esther"], 10),
    ("Hi", "Hiob", ["Ijob", "Job"], 42),
    ("Ps", "Psalm", ["Psalmen"], 150),
    ("Spr", "Sprüche", ["Sprichwörter"], 31),
    ("Pred", "Prediger", ["Kohelet", "Koh"], 12),
    ("Hld", "Hohelied", ["Hoheslied", "Hl"], 8),
    ("Jes", "Jesaja", [], 66),
    ("Jer", "Jeremia", [], 52),
    ("Klgl", "Klagelieder", ["Kla"], 5),
    ("Hes", "Hesekiel", ["Ezechiel", "Ez"], 48),
    ("Dan", "Daniel", [], 12),
    ("Hos", "Hosea", [], 14),
    ("Joel", "Joel", [], 3),
    ("Am", "Amos", [], 9),
    ("Obd", "Obadja", ["Ob"], 1),
    ("Jon", "Jona", [], 4),
    ("Mi", "Micha", [], 7),
    ("Nah", "Nahum", [], 3),
    ("Hab", "Habakuk", [], 3),
    ("Zef", "Zefanja", ["Zeph"], 3),
    ("Hag", "Haggai", [], 2),
    ("Sach", "Sacharja", [], 14),
    ("Mal", "Maleachi", [], 4),
    ("Mt", "Matthäus", ["Matth", "Matthäusevangelium"], 28),
    ("Mk", "Markus", ["Markusevangelium"], 16),
    ("Lk", "Lukas", ["Lukasevangelium"], 24),
    ("Joh", "Johannes", ["Johannesevangelium"], 21),
    ("Apg", "Apostelgeschichte", [], 28),
    ("Röm", "Römer", ["Römerbrief", "Roe"], 16),
    ("1Kor", "1. Korinther", [], 16),
    ("2Kor", "2. Korinther", [], 13),
    ("Gal", "Galater", [], 6),
    ("Eph", "Epheser", [], 6),
    ("Phil", "Philipper", [], 4),
    ("Kol", "Kolosser", [], 4),
    ("1Thess", "1. Thessalonicher", ["1Th"], 5),
    ("2Thess", "2. Thessalonicher", ["2Th"], 3),
    ("1Tim", "1. Timotheus", [], 6),
    ("2Tim", "2. Timotheus", [], 4),
    ("Tit", "Titus", [], 3),
    ("Phlm", "Philemon", ["Phm"], 1),
    ("Hebr", "Hebräer", ["Heb"], 13),
    ("Jak", "Jakobus", [], 5),
    ("1Petr", "1. Petrus", ["1Pt", "1Pet"], 5),
    ("2Petr", "2. Petrus", ["2Pt", "2Pet"], 3),
    ("1Joh", "1. Johannes", [], 5),
    ("2Joh", "2. Johannes", [], 1),
    ("3Joh", "3. Johannes", [], 1),
    ("Jud", "Judas", [], 1),
    ("Offb", "Offenbarung", ["Offenbarung des Johannes", "Apokalypse", "Off"], 22),
]


def _norm(text: str) -> str:
    """Schreibweise vereinheitlichen: klein, ohne Umlaute, Leerzeichen und Punkte."""
    t = text.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("ë", "e")):
        t = t.replace(a, b)
    return re.sub(r"[\s.\-]", "", t)


@dataclass(frozen=True)
class Book:
    index: int
    short: str
    name: str
    chapters: int
    aliases: tuple[str, ...] = ()


BOOKS = [Book(i, s, n, c, tuple(a)) for i, (s, n, a, c) in enumerate(_BOOKS)]

_LOOKUP: dict[str, int] = {}
for _i, (_short, _name, _aliases, _c) in enumerate(_BOOKS):
    for _alias in [_short, _name, *_aliases]:
        _LOOKUP.setdefault(_norm(_alias), _i)


def find_book(text: str) -> Book | None:
    i = _LOOKUP.get(_norm(text))
    return BOOKS[i] if i is not None else None
