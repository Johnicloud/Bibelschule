import pytest
from app.domain.bible import BOOKS, find_book, name_sort_key, parse_ref, split_refs
from app.domain.errors import InvalidInput


def fmt(text):
    return parse_ref(text).format()


def test_66_books_in_order():
    assert len(BOOKS) == 66
    assert BOOKS[0].name == "1. Mose" and BOOKS[39].name == "Matthäus" and BOOKS[65].name == "Offenbarung"
    assert len({b.short for b in BOOKS}) == 66


def test_book_spellings():
    for text in ("1. Mose", "1Mo", "1 Mose", "Genesis", "gen"):
        assert find_book(text).short == "1Mo"
    assert find_book("Römer").short == "Röm" and find_book("roemer").short == "Röm"
    assert find_book("1. Könige").short == "1Kön" and find_book("Offenbarung des Johannes").short == "Offb"
    assert find_book("Unsinn") is None


def test_single_verse_range_and_chapter():
    assert fmt("Joh 3,16") == "Joh 3,16"
    assert fmt("Johannes 3:16-18") == "Joh 3,16-18"
    assert fmt("1. Mose 12,1") == "1Mo 12,1"
    assert fmt("Ps 23") == "Ps 23"
    assert fmt("Mt 5-7") == "Mt 5-7"
    assert fmt("Röm 8,28-9,5") == "Röm 8,28-9,5"


def test_f_ff_and_single_chapter_books():
    assert fmt("1Kor 13,4f") == "1Kor 13,4-5"
    assert fmt("Joh 3,16ff") == "Joh 3,16"
    assert fmt("Jud 5") == "Jud 1,5"
    assert fmt("Phlm 10-12") == "Phlm 1,10-12"
    assert fmt("Jud 1,5") == "Jud 1,5"


def test_invalid_refs():
    for bad in ("", "Joh", "Joh 3 16", "Xyz 3,16", "Joh 0,5", "Joh 3,16-10", "Joh 5-3", "Mt 5-7,3"):
        with pytest.raises(InvalidInput):
            parse_ref(bad)


def test_sorting_in_bible_order():
    refs = [parse_ref(t) for t in ("Joh 3,16", "1Mo 12,1", "Ps 23", "1Mo 3,15", "Offb 1,1", "1Mo 3")]
    assert [r.format() for r in sorted(refs, key=lambda r: r.sort_key)] == [
        "1Mo 3", "1Mo 3,15", "1Mo 12,1", "Ps 23", "Joh 3,16", "Offb 1,1"]


def test_split_refs_and_name_sort():
    assert split_refs(["Joh 3,16; Joh 4,5", "Ps 23\nPs 24", " "]) == ["Joh 3,16", "Joh 4,5", "Ps 23", "Ps 24"]
    names = ["Zebedäus", "Ägypten", "Abraham", "Ur", "Östlich", "Aaron"]
    assert sorted(names, key=name_sort_key) == ["Aaron", "Abraham", "Ägypten", "Östlich", "Ur", "Zebedäus"]
