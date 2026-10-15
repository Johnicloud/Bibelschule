import pytest
from app.domain.bible import BOOKS, find_book, parse_ref
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
    assert BOOKS[ref.book].short == "Jud" and ref.chapter == 1


def test_parse_ref_rejects_unknown_book():
    with pytest.raises(InvalidInput):
        parse_ref("Xyz 1,1")


def test_parse_ref_rejects_chapter_beyond_the_book():
    with pytest.raises(InvalidInput):
        parse_ref("Joh 22")    # Johannes hat nur 21 Kapitel


def test_all_66_books_present_in_evangelical_order():
    assert len(BOOKS) == 66
    assert BOOKS[0].short == "1Mo" and BOOKS[65].short == "Offb"
