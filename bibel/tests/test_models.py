from app.domain.models import Vers, woerter


def test_woerter_splits_on_whitespace():
    assert woerter("Im Anfang schuf Gott die Himmel und die Erde.") == [
        "Im", "Anfang", "schuf", "Gott", "die", "Himmel", "und", "die", "Erde."]


def test_woerter_is_stable_for_empty_text():
    assert woerter("") == []
    assert woerter(None) == []


def test_vers_wort_is_one_based_and_bounds_checked():
    v = Vers(buch_index=0, kapitel=1, vers=1, text="Im Anfang schuf Gott.", id="1Mo.1.1")
    assert v.wort(1) == "Im"
    assert v.wort(4) == "Gott."
    assert v.wort(0) is None
    assert v.wort(5) is None
