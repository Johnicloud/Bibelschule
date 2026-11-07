from app.domain.models import Vers, kontextsatz, woerter


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


def test_kontextsatz_returns_the_sentence_containing_the_match():
    text = "Im Anfang schuf Gott die Himmel und die Erde. Die Erde aber war wüst und leer."
    assert kontextsatz(text, "wüst") == "Die Erde aber war wüst und leer."


def test_kontextsatz_ignores_case():
    text = "Im Anfang schuf Gott die Himmel und die Erde. Die Erde aber war wüst und leer."
    assert kontextsatz(text, "GOTT") == "Im Anfang schuf Gott die Himmel und die Erde."


def test_kontextsatz_falls_back_to_the_whole_text_without_sentence_boundaries():
    assert kontextsatz("ein einziger Satz ohne Punkt", "Satz") == "ein einziger Satz ohne Punkt"
