from app.adapters.inbound.exports import entries_table, passages_table, to_csv, to_text
from app.application.services import RegisterService
from tests.test_service import InMemoryRepo


def filled():
    svc = RegisterService(InMemoryRepo())
    namen, orte = svc.create_register("f", "Namen"), svc.create_register("f", "Orte")
    svc.add_entry(namen.id, "Abraham", ["Hebr 11,8", "1Mo 12,1-3"])
    svc.add_entry(orte.id, "Haran", ["1Mo 12,4"])
    return svc


def test_entries_csv_and_text():
    svc = filled()
    header, rows = entries_table(svc.list_entries("f"), svc.register_names())
    assert to_csv(header, rows) == (
        "Name;Register;Bibelstellen\r\n"
        'Abraham;Namen;"1Mo 12,1-3; Hebr 11,8"\r\n'
        "Haran;Orte;1Mo 12,4\r\n")
    assert to_text(rows) == "Abraham (Namen): 1Mo 12,1-3; Hebr 11,8\nHaran (Orte): 1Mo 12,4\n"


def test_passages_csv_and_text():
    svc = filled()
    header, rows = passages_table(svc.by_passage("f"), svc.register_names())
    assert header == ["Bibelstelle", "Einträge"]
    assert to_text(rows) == "1Mo 12,1-3: Abraham (Namen)\n1Mo 12,4: Haran (Orte)\nHebr 11,8: Abraham (Namen)\n"


def test_csv_quotes_special_characters_and_empty_register():
    assert to_csv(["A"], [['sag "hallo"; ok']]) == 'A\r\n"sag ""hallo""; ok"\r\n'
    assert to_text([]) == "" and to_csv(*entries_table([], {})) == "Name;Register;Bibelstellen\r\n"
