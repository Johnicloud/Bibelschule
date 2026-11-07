from app.adapters.outbound.matthew_henry import alle_eintraege, eintraege_aus_kapitel, usfm


def _kapitel_json(eintraege):
    return {"chapter": {"content": [{"type": "verse", "number": n, "content": [t]} for n, t in eintraege]}}


def test_eintrag_deckt_bis_ausschliesslich_zum_naechsten_ab():
    daten = _kapitel_json([(1, "Zu Vers 1 bis 21."), (22, "Zu Vers 22 bis Ende.")])
    assert eintraege_aus_kapitel(daten) == [(1, 21, "Zu Vers 1 bis 21."), (22, 22, "Zu Vers 22 bis Ende.")]


def test_einziger_eintrag_deckt_nur_sich_selbst_ab():
    daten = _kapitel_json([(5, "Nur zu Vers 5.")])
    assert eintraege_aus_kapitel(daten) == [(5, 5, "Nur zu Vers 5.")]


def test_mehrzeiliger_content_wird_zusammengefuegt():
    daten = {"chapter": {"content": [{"type": "verse", "number": 1, "content": ["Erster Absatz.", "Zweiter Absatz."]}]}}
    assert eintraege_aus_kapitel(daten) == [(1, 1, "Erster Absatz.\nZweiter Absatz.")]


def test_leere_eintraege_fallen_weg():
    daten = _kapitel_json([(1, "   ")])
    assert eintraege_aus_kapitel(daten) == []


def test_andere_content_typen_als_vers_werden_ignoriert():
    daten = {"chapter": {"content": [{"type": "heading", "content": ["Überschrift"]},
                                      {"type": "verse", "number": 1, "content": ["Text."]}]}}
    assert eintraege_aus_kapitel(daten) == [(1, 1, "Text.")]


def test_usfm_codes_fuer_bekannte_buecher():
    assert usfm(42) == "JHN"    # Johannes
    assert usfm(0) == "GEN"     # 1. Mose
    assert usfm(65) == "REV"    # Offenbarung


class FakeKlient:
    """Tut so, als gäbe es nur für bestimmte (Buch, Kapitel) einen Henry-Kommentar."""
    def __init__(self, vorhanden: dict):
        self.vorhanden = vorhanden
        self.aufrufe = []

    def kapitel(self, buch_usfm, kapitel):
        self.aufrufe.append((buch_usfm, kapitel))
        return self.vorhanden.get((buch_usfm, kapitel))


def test_alle_eintraege_ueberspringt_kapitel_ohne_kommentar():
    klient = FakeKlient({("JON", 1): _kapitel_json([(1, "Zu Jona 1,1 ff.")])})
    ergebnisse = alle_eintraege(klient, buecher=[31], wartezeit=0)   # Jona
    assert ergebnisse == [("Jon", 1, 1, 1, "Zu Jona 1,1 ff.")]


def test_alle_eintraege_ruft_jedes_kapitel_des_buches_ab():
    klient = FakeKlient({})
    alle_eintraege(klient, buecher=[65], wartezeit=0)   # Offenbarung, 22 Kapitel
    assert klient.aufrufe == [("REV", n) for n in range(1, 23)]
