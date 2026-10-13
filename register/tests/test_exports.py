from app.adapters.inbound.exports import entries_table, passages_table, to_csv, to_text
from app.application.services import RegisterService
from tests.test_service import InMemoryRepo


def filled():
    svc = RegisterService(InMemoryRepo())
    svc.add_entry("f", "person", "Abraham", ["Hebr 11,8", "1Mo 12,1-3"])
    svc.add_entry("f", "place", "Haran", ["1Mo 12,4"])
    return svc


def test_entries_csv_and_text():
    header, rows = entries_table(filled().list_entries("f"))
    assert to_csv(header, rows) == (
        "Name;Art;Bibelstellen\r\n"
        'Abraham;Name;"1Mo 12,1-3; Hebr 11,8"\r\n'
        "Haran;Ort;1Mo 12,4\r\n")
    assert to_text(rows) == "Abraham (Name): 1Mo 12,1-3; Hebr 11,8\nHaran (Ort): 1Mo 12,4\n"


def test_passages_csv_and_text():
    header, rows = passages_table(filled().by_passage("f"))
    assert header == ["Bibelstelle", "Namen und Orte"]
    assert to_text(rows) == "1Mo 12,1-3: Abraham (Name)\n1Mo 12,4: Haran (Ort)\nHebr 11,8: Abraham (Name)\n"


def test_csv_quotes_special_characters_and_empty_register():
    assert to_csv(["A"], [['sag "hallo"; ok']]) == 'A\r\n"sag ""hallo""; ok"\r\n'
    assert to_text([]) == "" and to_csv(*entries_table([])) == "Name;Art;Bibelstellen\r\n"
