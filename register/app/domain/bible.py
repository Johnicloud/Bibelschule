"""Bibelbücher (66, evangelische Reihenfolge) und Bibelstellen: erkennen, normieren, sortieren."""
import re
import unicodedata
from dataclasses import dataclass

from app.domain.errors import InvalidInput

# (Kurzname nach Lutherbibel, ausgeschriebener Name, weitere Schreibweisen)
_BOOKS: list[tuple[str, str, list[str]]] = [
    ("1Mo", "1. Mose", ["Genesis", "Gen", "1 Mose"]),
    ("2Mo", "2. Mose", ["Exodus", "Ex", "Exod", "2 Mose"]),
    ("3Mo", "3. Mose", ["Levitikus", "Lev", "3 Mose"]),
    ("4Mo", "4. Mose", ["Numeri", "Num", "4 Mose"]),
    ("5Mo", "5. Mose", ["Deuteronomium", "Dtn", "Deut", "5 Mose"]),
    ("Jos", "Josua", []),
    ("Ri", "Richter", []),
    ("Rut", "Rut", ["Ruth"]),
    ("1Sam", "1. Samuel", []),
    ("2Sam", "2. Samuel", []),
    ("1Kön", "1. Könige", ["1Kö", "1Kg"]),
    ("2Kön", "2. Könige", ["2Kö", "2Kg"]),
    ("1Chr", "1. Chronik", []),
    ("2Chr", "2. Chronik", []),
    ("Esr", "Esra", []),
    ("Neh", "Nehemia", []),
    ("Est", "Ester", ["Esther"]),
    ("Hi", "Hiob", ["Ijob", "Job"]),
    ("Ps", "Psalm", ["Psalmen"]),
    ("Spr", "Sprüche", ["Sprichwörter"]),
    ("Pred", "Prediger", ["Kohelet", "Koh"]),
    ("Hld", "Hohelied", ["Hoheslied", "Hl"]),
    ("Jes", "Jesaja", []),
    ("Jer", "Jeremia", []),
    ("Klgl", "Klagelieder", ["Kla"]),
    ("Hes", "Hesekiel", ["Ezechiel", "Ez"]),
    ("Dan", "Daniel", []),
    ("Hos", "Hosea", []),
    ("Joel", "Joel", []),
    ("Am", "Amos", []),
    ("Obd", "Obadja", ["Ob"]),
    ("Jon", "Jona", []),
    ("Mi", "Micha", []),
    ("Nah", "Nahum", []),
    ("Hab", "Habakuk", []),
    ("Zef", "Zefanja", ["Zeph"]),
    ("Hag", "Haggai", []),
    ("Sach", "Sacharja", []),
    ("Mal", "Maleachi", []),
    ("Mt", "Matthäus", ["Matth", "Matthäusevangelium"]),
    ("Mk", "Markus", ["Markusevangelium"]),
    ("Lk", "Lukas", ["Lukasevangelium"]),
    ("Joh", "Johannes", ["Johannesevangelium"]),
    ("Apg", "Apostelgeschichte", []),
    ("Röm", "Römer", ["Röm", "Römerbrief", "Roe"]),
    ("1Kor", "1. Korinther", []),
    ("2Kor", "2. Korinther", []),
    ("Gal", "Galater", []),
    ("Eph", "Epheser", []),
    ("Phil", "Philipper", []),
    ("Kol", "Kolosser", []),
    ("1Thess", "1. Thessalonicher", ["1Th"]),
    ("2Thess", "2. Thessalonicher", ["2Th"]),
    ("1Tim", "1. Timotheus", []),
    ("2Tim", "2. Timotheus", []),
    ("Tit", "Titus", []),
    ("Phlm", "Philemon", ["Phm"]),
    ("Hebr", "Hebräer", ["Heb"]),
    ("Jak", "Jakobus", []),
    ("1Petr", "1. Petrus", ["1Pt", "1Pet"]),
    ("2Petr", "2. Petrus", ["2Pt", "2Pet"]),
    ("1Joh", "1. Johannes", []),
    ("2Joh", "2. Johannes", []),
    ("3Joh", "3. Johannes", []),
    ("Jud", "Judas", []),
    ("Offb", "Offenbarung", ["Offenbarung des Johannes", "Apokalypse", "Off"]),
]

# Bücher mit nur einem Kapitel: "Jud 5" meint Vers 5
SINGLE_CHAPTER = {"Obd", "Phlm", "2Joh", "3Joh", "Jud"}


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


BOOKS = [Book(i, s, n) for i, (s, n, _) in enumerate(_BOOKS)]

_LOOKUP: dict[str, int] = {}
for _i, (_short, _name, _aliases) in enumerate(_BOOKS):
    for _alias in [_short, _name, *_aliases]:
        _LOOKUP.setdefault(_norm(_alias), _i)


def find_book(text: str) -> Book | None:
    i = _LOOKUP.get(_norm(text))
    return BOOKS[i] if i is not None else None


@dataclass(frozen=True)
class BibleRef:
    """Eine Bibelstelle: ganze Kapitel (verse=None), ein Vers oder ein Bereich (auch über Kapitel)."""
    book: int
    chapter: int
    verse: int | None
    chapter_end: int
    verse_end: int | None

    @property
    def sort_key(self) -> tuple:
        return (self.book, self.chapter, self.verse or 0, self.chapter_end, self.verse_end or 0)

    def format(self) -> str:
        short = BOOKS[self.book].short
        if self.verse is None:
            span = f"{self.chapter}" if self.chapter_end == self.chapter else f"{self.chapter}-{self.chapter_end}"
            return f"{short} {span}"
        if self.chapter_end == self.chapter:
            span = f"{self.verse}" if self.verse_end == self.verse else f"{self.verse}-{self.verse_end}"
            return f"{short} {self.chapter},{span}"
        return f"{short} {self.chapter},{self.verse}-{self.chapter_end},{self.verse_end}"


_REF = re.compile(r"""^\s*
    (?P<book>(?:[1-3]\s*\.?\s*)?[^\W\d_][^\d,:;\-–—]*?)
    \s*(?P<n1>\d+)
    (?:\s*[,:]\s*(?P<n2>\d+))?
    (?:\s*[-–—]\s*(?P<n3>\d+)(?:\s*[,:]\s*(?P<n4>\d+))?)?
    \s*(?P<f>ff?\.?)?\s*$""", re.X)


def parse_ref(text: str) -> BibleRef:
    """'Joh 3,16-18', '1. Mose 12,1', 'Ps 23', 'Mt 5-7', 'Röm 8,28-9,5', 'Jud 5', '1Kor 13,4f'."""
    m = _REF.match(text or "")
    if not m:
        raise InvalidInput(f"Die Bibelstelle „{(text or '').strip()}“ habe ich nicht verstanden.")
    book = find_book(m["book"])
    if book is None:
        raise InvalidInput(f"Das Bibelbuch „{m['book'].strip()}“ kenne ich nicht („{text.strip()}“).")
    n1, n2, n3, n4 = (int(m[k]) if m[k] else None for k in ("n1", "n2", "n3", "n4"))
    f = (m["f"] or "").rstrip(".")

    if n2 is None and book.short in SINGLE_CHAPTER:   # "Jud 5" = Vers 5, "Jud 3-5" = Verse 3-5
        chapter, verse, chapter_end, verse_end = 1, n1, 1, n3 or n1
        if n4 is not None:
            raise InvalidInput(f"Die Bibelstelle „{text.strip()}“ habe ich nicht verstanden.")
    elif n2 is None:                                  # ganzes Kapitel oder Kapitelbereich
        if n4 is not None:
            raise InvalidInput(f"Die Bibelstelle „{text.strip()}“ habe ich nicht verstanden.")
        chapter, verse, chapter_end, verse_end = n1, None, n3 or n1, None
    elif n3 is None:                                  # ein Vers
        chapter, verse, chapter_end, verse_end = n1, n2, n1, n2
    elif n4 is None:                                  # Versbereich im Kapitel
        chapter, verse, chapter_end, verse_end = n1, n2, n1, n3
    else:                                             # Bereich über Kapitelgrenzen
        chapter, verse, chapter_end, verse_end = n1, n2, n3, n4

    if f == "f":                                      # "3,16f" = 3,16-17
        if verse is None:
            chapter_end = chapter + 1
        else:
            verse_end = verse_end + 1

    if min(x for x in (chapter, verse, chapter_end, verse_end) if x is not None) < 1:
        raise InvalidInput(f"Kapitel und Verse beginnen bei 1 („{text.strip()}“).")
    if (chapter_end, verse_end or 0) < (chapter, verse or 0):
        raise InvalidInput(f"Die Stelle „{text.strip()}“ endet vor ihrem Anfang.")
    return BibleRef(book.index, chapter, verse, chapter_end, verse_end)


def split_refs(items: list[str]) -> list[str]:
    """Trennt Eingaben wie 'Joh 3,16; Joh 4,5' oder Zeilenumbrüche in einzelne Stellen."""
    parts = []
    for item in items or []:
        parts += [p.strip() for p in re.split(r"[;\n]", item or "") if p.strip()]
    return parts


def name_sort_key(name: str) -> str:
    """Alphabetisch nach deutscher Regel: Ä wie A, Ö wie O, Ü wie U, ß wie ss; Groß/Klein egal."""
    t = unicodedata.normalize("NFKD", name.strip()).casefold()
    return "".join(c for c in t if not unicodedata.combining(c))
