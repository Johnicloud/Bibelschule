"""Bibelbücher (66, evangelische Reihenfolge) und Bibelstellen: erkennen, normieren.
Eigene Kopie des gleichnamigen Moduls im Bibel-Dienst (Dienste teilen keinen Code, nur die Fach-ID) –
Kurznamen und Reihenfolge bewusst identisch gehalten, damit eine Bibelstelle in allen Diensten gleich aussieht.
`parse_ref` liest die freie Eingabe beim Anlegen einer Predigt ("Joh 3,16" oder nur "Ps 23"), `parse_stelle`/
`Stelle.format()` die kanonische Adresse, die der Bibel-Dienst für einen Verweis erwartet (siehe bibel_client.py)."""
import re
from dataclasses import dataclass

from app.domain.errors import InvalidInput

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


# Bücher mit nur einem Kapitel: "Jud 5" meint Vers 5, Kapitel ist immer 1.
SINGLE_CHAPTER = {"Obd", "Phlm", "2Joh", "3Joh", "Jud"}


@dataclass(frozen=True)
class BibleRef:
    """`verse` ist der erste genannte Vers (z. B. 16 bei 'Joh 3,16-18'), None wenn nur das Kapitel genannt
    wurde (z. B. 'Ps 23') – für das Markieren eines Verses beim Nachschlagen (siehe Service `nachschlagen`)."""
    book: int
    chapter: int
    verse: int | None = None


_REF = re.compile(r"""^\s*
    (?P<book>(?:[1-3]\s*\.?\s*)?[^\W\d_][^\d,:;\-–—]*?)
    \s*(?P<n1>\d+)
    (?:\s*[,:]\s*(?P<n2>\d+))?
    (?:\s*[-–—]\s*\d+(?:\s*[,:]\s*\d+)?)?
    \s*(?:ff?\.?)?\s*$""", re.X)


def parse_ref(text: str) -> BibleRef:
    """Buch, Kapitel und (falls genannt) erster Vers einer Stelle wie 'Joh 3,16-18' oder '1. Mose 12,1'.
    Bei Büchern mit nur einem Kapitel (`SINGLE_CHAPTER`) meint die einzige Zahl den Vers, nicht das Kapitel
    (z. B. 'Jud 5' = Vers 5)."""
    m = _REF.match(text or "")
    if not m:
        raise InvalidInput(f"Die Bibelstelle „{(text or '').strip()}“ habe ich nicht verstanden.")
    book = find_book(m["book"])
    if book is None:
        raise InvalidInput(f"Das Bibelbuch „{m['book'].strip()}“ kenne ich nicht („{text.strip()}“).")
    if book.short in SINGLE_CHAPTER:
        chapter, verse = 1, int(m["n1"])
    else:
        chapter, verse = int(m["n1"]), (int(m["n2"]) if m["n2"] else None)
    if not 1 <= chapter <= book.chapters:
        raise InvalidInput(f"{book.name} hat nur {book.chapters} Kapitel („{text.strip()}“).")
    return BibleRef(book.index, chapter, verse)


@dataclass(frozen=True)
class Stelle:
    """Eine genaue, stabile Adresse bis auf Wortebene – die Grundlage, an die alles Mögliche anknüpfen kann
    (Register, Notizen, Fragen, Wortstudien, …), siehe Projektnotizen. `wort` ist das 1-basierte Wort
    innerhalb des Verses, None = der ganze Vers ist gemeint."""
    book: int
    chapter: int
    verse: int
    word: int | None = None

    def format(self) -> str:
        teile = [BOOKS[self.book].short, str(self.chapter), str(self.verse)]
        if self.word is not None:
            teile.append(str(self.word))
        return ".".join(teile)


_STELLE = re.compile(r"^\s*(?P<book>[^.]+)\.(?P<chapter>\d+)\.(?P<verse>\d+)(?:\.(?P<word>\d+))?\s*$")


def parse_stelle(text: str) -> Stelle:
    """Die kanonische, maschinenlesbare Adress-Schreibweise 'Joh.3.16' (Vers) oder 'Joh.3.16.5' (5. Wort
    dieses Verses) – anders als `parse_ref` (freie Texteingabe wie 'Joh 3,16-18') IMMER mit Vers, nie ein
    Bereich: eine Stelle, an die man etwas anknüpft, ist immer genau eine Stelle."""
    m = _STELLE.match(text or "")
    if not m:
        raise InvalidInput(f"Die Stelle „{(text or '').strip()}“ habe ich nicht verstanden (erwartet z. B. „Joh.3.16“).")
    book = find_book(m["book"])
    if book is None:
        raise InvalidInput(f"Das Bibelbuch „{m['book'].strip()}“ kenne ich nicht („{text.strip()}“).")
    chapter, verse = int(m["chapter"]), int(m["verse"])
    word = int(m["word"]) if m["word"] else None
    if not 1 <= chapter <= book.chapters:
        raise InvalidInput(f"{book.name} hat nur {book.chapters} Kapitel („{text.strip()}“).")
    if verse < 1:
        raise InvalidInput(f"Verse beginnen bei 1 („{text.strip()}“).")
    if word is not None and word < 1:
        raise InvalidInput(f"Wörter beginnen bei 1 („{text.strip()}“).")
    return Stelle(book.index, chapter, verse, word)
