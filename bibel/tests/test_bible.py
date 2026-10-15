import pytest
from app.domain.bible import BOOKS, Stelle, find_book, parse_ref, parse_stelle
from app.domain.errors import InvalidInput


def test_find_book_by_short_name_and_alias():
    assert find_book("Joh").short == "Joh"
    assert find_book("Genesis").short == "1Mo"
    assert find_book("1 Mose").short == "1Mo"
    assert find_book("nichtvorhanden") is None


def test_parse_ref_reads_book_and_chapter():
    ref = parse_ref("Joh 3,16")
    assert BOOKS[ref.book].short == "Joh" and ref.chapter == 3


def test_parse_ref_whole_chapter():
    ref = parse_ref("Ps 23")
    assert BOOKS[ref.book].short == "Ps" and ref.chapter == 23


def test_parse_ref_single_chapter_book_means_chapter_one():
    ref = parse_ref("Jud 5")   # Judas hat nur 1 Kapitel, "Jud 5" meint Vers 5
    assert BOOKS[ref.book].short == "Jud" and ref.chapter == 1 and ref.verse == 5


def test_parse_ref_reads_the_first_verse_when_given():
    ref = parse_ref("Joh 3,16")
    assert ref.chapter == 3 and ref.verse == 16
    ref = parse_ref("Joh 3,16-18")   # Bereich: nur der erste Vers wird zum Markieren übernommen
    assert ref.verse == 16


def test_parse_ref_whole_chapter_has_no_verse():
    ref = parse_ref("Ps 23")
    assert ref.verse is None


def test_parse_ref_rejects_unknown_book():
    with pytest.raises(InvalidInput):
        parse_ref("Xyz 1,1")


def test_parse_ref_rejects_chapter_beyond_the_book():
    with pytest.raises(InvalidInput):
        parse_ref("Joh 22")    # Johannes hat nur 21 Kapitel


def test_all_66_books_present_in_evangelical_order():
    assert len(BOOKS) == 66
    assert BOOKS[0].short == "1Mo" and BOOKS[65].short == "Offb"


def test_stelle_format_roundtrip():
    joh = find_book("Joh")
    assert Stelle(joh.index, 3, 16).format() == "Joh.3.16"
    assert Stelle(joh.index, 3, 16, word=5).format() == "Joh.3.16.5"


def test_parse_stelle_reads_verse_and_optional_word():
    s = parse_stelle("Joh.3.16")
    assert BOOKS[s.book].short == "Joh" and s.chapter == 3 and s.verse == 16 and s.word is None
    s = parse_stelle("Joh.3.16.5")
    assert s.word == 5


def test_parse_stelle_rejects_bad_input():
    with pytest.raises(InvalidInput):
        parse_stelle("Joh 3,16")          # kein Punkt-Format
    with pytest.raises(InvalidInput):
        parse_stelle("Xyz.1.1")           # unbekanntes Buch
    with pytest.raises(InvalidInput):
        parse_stelle("Joh.99.1")          # Johannes hat nur 21 Kapitel
    with pytest.raises(InvalidInput):
        parse_stelle("Joh.3.0")           # Verse beginnen bei 1
    with pytest.raises(InvalidInput):
        parse_stelle("Joh.3.16.0")        # Wörter beginnen bei 1
