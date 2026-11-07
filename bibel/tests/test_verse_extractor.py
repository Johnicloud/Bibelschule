import io

from app.adapters.outbound.verse_extractor import PyMuPdfVerseExtractor

_SEITENBREITE, _SEITENHOEHE = 400, 500
_KOERPER = "Helvetica"
_FETT = "Helvetica-Bold"
_KURSIV = "Helvetica-Oblique"
_KOERPERGROESSE = 8


def _zeile(c, y, teile, luecke=2):
    """teile: [(text, schriftart, groesse), ...] – zeichnet sie nebeneinander auf derselben Grundlinie.
    `luecke` ist der sichtbare Abstand zwischen den Stücken (0 für direkt aneinandergeklebten Text, wie ein
    Fußnotenzeichen mitten im Wort im echten Druck)."""
    x = 50
    for text, font, size in teile:
        c.setFont(font, size)
        c.drawString(x, y, text)
        x += c.stringWidth(text, font, size) + luecke


def _kopfzeile(c, text):
    """Die Buch/Kapitel-Kopfzeile ganz oben auf der Seite (kleiner PyMuPDF-y-Wert, siehe `_KOPF_Y`)."""
    c.setFont(_KOERPER, 10)
    c.drawString(150, _SEITENHOEHE - 10, text)


def _baue_pdf(seiten: list[list[tuple]]) -> bytes:
    """`seiten`: je Seite eine Liste von Zeilen (siehe `_zeile`), optional vorangestellt eine Kopfzeile über
    `("KOPF", text)`."""
    from reportlab.pdfgen import canvas
    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(_SEITENBREITE, _SEITENHOEHE))
    for zeilen in seiten:
        y = _SEITENHOEHE - 60
        for zeile in zeilen:
            if zeile[0] == "KOPF":
                _kopfzeile(c, zeile[1])
                continue
            _zeile(c, y, zeile)
            y -= 20
        c.showPage()
    c.save()
    return puffer.getvalue()


def _vers(nummer: int) -> tuple:
    return (f"{nummer}", _FETT, _KOERPERGROESSE * 0.9)


def _text(stueck: str) -> tuple:
    return (stueck, _KOERPER, _KOERPERGROESSE)


def test_verszahl_wird_ueber_schrift_erkannt_nicht_ueber_regel():
    pdf = _baue_pdf([[
        [_text("Im Anfang war das Wort,")],
        [_vers(2), _text("Dieses war im Anfang bei Gott.")],
        [_vers(3), _text("Alles ist durch dasselbe entstanden.")],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert verse == [
        (1, 1, "Im Anfang war das Wort,"),
        (1, 2, "Dieses war im Anfang bei Gott."),
        (1, 3, "Alles ist durch dasselbe entstanden."),
    ]


def test_fussnotenzeichen_und_fussnotentext_fallen_weg():
    # Im echten Druck klebt das Fußnotenzeichen ohne sichtbaren Abstand am Wort ("Welt" + hochgestelltes "b") –
    # darum hier mit `luecke=0` gebaut statt über `_baue_pdf` (dessen Standardabstand das nicht abbilden würde).
    from reportlab.pdfgen import canvas
    klein = _KOERPERGROESSE * 0.6
    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(_SEITENBREITE, _SEITENHOEHE))
    _zeile(c, _SEITENHOEHE - 60, [_text("Er war in der Welt"), ("b", _KURSIV, klein),
                                   _text(", und die Welt erkannte ihn nicht.")], luecke=0)
    _zeile(c, _SEITENHOEHE - 80, [("b", _KURSIV, klein), (" (1,10) irgendein Hinweis in Kleinschrift.", _KOERPER, klein)], luecke=0)
    c.showPage()
    c.save()
    verse = PyMuPdfVerseExtractor().buch_verse(puffer.getvalue(), 1, None)
    assert verse == [(1, 1, "Er war in der Welt, und die Welt erkannte ihn nicht.")]


def test_kapitaelchen_rest_des_gottesnamens_bleibt_erhalten():
    # "HERR" steht in dieser Ausgabe als großes "H" + kleines, NICHT kursives "ERR" (Kapitälchen) – das darf
    # nicht wie ein Fußnotenzeichen verschwinden, obwohl es genauso klein ist (siehe Modul-Docstring).
    from reportlab.pdfgen import canvas
    klein = _KOERPERGROESSE * 0.69
    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(_SEITENBREITE, _SEITENHOEHE))
    _zeile(c, _SEITENHOEHE - 60, [_text("Erhebe dich, "), ("H", _KOERPER, _KOERPERGROESSE),
                                   ("ERR", _KOERPER, klein), _text(", in deiner Kraft,")], luecke=0)
    c.showPage()
    c.save()
    verse = PyMuPdfVerseExtractor().buch_verse(puffer.getvalue(), 1, None)
    assert verse == [(1, 1, "Erhebe dich, HERR, in deiner Kraft,")]


def test_kapitaelchen_rest_bleibt_auch_in_kursiver_psalm_ueberschrift_erhalten():
    # Psalm-Überschriften stehen ganz in Kursivschrift – auch dort ist "ERR" ein Kapitälchen-Rest und kein
    # einzelnes Fußnotenzeichen (das ist immer nur EIN Zeichen, siehe Modul-Docstring), fällt also nicht weg.
    from reportlab.pdfgen import canvas
    klein = _KOERPERGROESSE * 0.69
    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(_SEITENBREITE, _SEITENHOEHE))
    _zeile(c, _SEITENHOEHE - 60, [("Ein Klagelied Davids, das er dem ", _KURSIV, _KOERPERGROESSE),
                                   ("H", _KURSIV, _KOERPERGROESSE), ("ERR", _KURSIV, klein),
                                   (" sang.", _KURSIV, _KOERPERGROESSE)], luecke=0)
    c.showPage()
    c.save()
    verse = PyMuPdfVerseExtractor().buch_verse(puffer.getvalue(), 1, None)
    assert verse == [(1, 1, "Ein Klagelied Davids, das er dem HERR sang.")]


def test_ganze_fussnotenzeile_ohne_koerpertext_faellt_weiterhin_komplett_weg():
    # Der Fließtext braucht hier mehr Zeichen als die Fußnote, sonst hielte die (nach Zeichenzahl gewichtete)
    # Körpergröße-Schätzung selbst die Fußnote für den Fließtext (siehe `_koerpergroesse`).
    klein = _KOERPERGROESSE * 0.69
    pdf = _baue_pdf([[
        [_text("Ein ganz normal langer, großer Vers mit genug Zeichen, damit er als Fließtext zählt.")],
        [("Kurze Fußnote.", _KOERPER, klein)],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert verse == [(1, 1, "Ein ganz normal langer, großer Vers mit genug Zeichen, damit er als Fließtext zählt.")]


def test_doppeltes_leerzeichen_nach_uebersprungenem_fussnotenzeichen_wird_zusammengezogen():
    klein = _KOERPERGROESSE * 0.6
    pdf = _baue_pdf([[
        [_text("Er war in der Welt"), ("b", _KURSIV, klein), _text(" , und die Welt erkannte ihn nicht.")],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert verse == [(1, 1, "Er war in der Welt , und die Welt erkannte ihn nicht.")]


def test_zwischenueberschrift_und_bibelstellen_zeile_fallen_weg():
    pdf = _baue_pdf([[
        [("Die ersten Jünger", _KURSIV, _KOERPERGROESSE)],
        [("Joh 17,6; 6,44-45", _KOERPER, _KOERPERGROESSE)],
        [_vers(2), _text("Und die beiden Jünger hörten ihn reden.")],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert verse == [(1, 2, "Und die beiden Jünger hörten ihn reden.")]


def test_zweizeilige_zwischenueberschrift_faellt_komplett_weg():
    pdf = _baue_pdf([[
        [("Jesus und Nikodemus.", _KURSIV, _KOERPERGROESSE)],
        [("Die Notwendigkeit der Wiedergeburt", _KURSIV, _KOERPERGROESSE)],
        [("Joh 1,12-13; 2Kor 5,17", _KOERPER, _KOERPERGROESSE)],
        [_vers(2), _text("Zweiter Vers nach der zweizeiligen Überschrift.")],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert verse == [(1, 2, "Zweiter Vers nach der zweizeiligen Überschrift.")]


def test_buchtitel_faellt_weg():
    # Der Fließtext muss in diesem Mini-Beispiel mehr Zeichen haben als der Titel, sonst hielte die (nach
    # Zeichenzahl gewichtete) Körpergröße-Schätzung selbst den Titel für den Fließtext (siehe `_koerpergroesse`).
    gross = _KOERPERGROESSE * 2
    pdf = _baue_pdf([[
        [("Das Evangelium nach Johannes", _FETT, gross)],
        [_text("Im Anfang war das Wort, und das Wort war bei Gott, und das Wort war Gott.")],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert verse == [(1, 1, "Im Anfang war das Wort, und das Wort war bei Gott, und das Wort war Gott.")]


def test_eigenstaendige_querverweis_zeile_faellt_auch_ohne_ueberschrift_weg():
    pdf = _baue_pdf([[
        [_vers(16), _text("Denn also hat Gott die Welt geliebt.")],
        [("Röm 5,8; 1Joh 4,9", _KOERPER, _KOERPERGROESSE)],
        [_vers(17), _text("Denn Gott hat seinen Sohn nicht gesandt.")],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert verse == [
        (1, 16, "Denn also hat Gott die Welt geliebt."),
        (1, 17, "Denn Gott hat seinen Sohn nicht gesandt."),
    ]


def test_kapitelgrenze_genau_an_der_zwischenueberschrift_wenn_danach_die_verszahl_zurueckspringt():
    pdf = _baue_pdf([[
        [_vers(3), _text("Das Ende von Kapitel eins.")],
        [("Die Hochzeit von Kana", _KURSIV, _KOERPERGROESSE)],
        [("Joh 5,36", _KOERPER, _KOERPERGROESSE)],
        [_text("Und am dritten Tag war eine Hochzeit in Kana.")],
        [_vers(2), _text("Aber auch Jesus wurde eingeladen.")],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert verse == [
        (1, 3, "Das Ende von Kapitel eins."),
        (2, 1, "Und am dritten Tag war eine Hochzeit in Kana."),
        (2, 2, "Aber auch Jesus wurde eingeladen."),
    ]


def test_zwischenueberschrift_mitten_im_kapitel_ohne_verszahl_ruecksprung_bleibt_folgenlos():
    """Dieselbe Falle wie in der echten Schlachter-PDF (Johannes 2: "Die erste Tempelreinigung" steht lange
    vor Kapitelende, "Die Notwendigkeit der Wiedergeburt" erst an der echten Kapitel-3-Grenze) – nur die
    Überschrift UNMITTELBAR vor dem Rücksprung darf zur Kapitelgrenze werden, nicht die erste auf der Seite."""
    pdf = _baue_pdf([[
        [_vers(12), _text("Letzter Vers vor der ersten Zwischenüberschrift.")],
        [("Die erste Tempelreinigung", _KURSIV, _KOERPERGROESSE)],
        [("Mt 21,12", _KOERPER, _KOERPERGROESSE)],
        [_vers(13), _text("Geht mit steigenden Zahlen weiter,")],
        [_vers(14), _text("ohne dass hier ein neues Kapitel beginnt.")],
        [("Die Notwendigkeit der Wiedergeburt", _KURSIV, _KOERPERGROESSE)],
        [("Joh 3,3", _KOERPER, _KOERPERGROESSE)],
        [_text("Unnumerierter Vers 1 des wirklich neuen Kapitels.")],
        [_vers(2), _text("Zweiter Vers des neuen Kapitels.")],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert verse == [
        (1, 12, "Letzter Vers vor der ersten Zwischenüberschrift."),
        (1, 13, "Geht mit steigenden Zahlen weiter,"),
        (1, 14, "ohne dass hier ein neues Kapitel beginnt."),
        (2, 1, "Unnumerierter Vers 1 des wirklich neuen Kapitels."),
        (2, 2, "Zweiter Vers des neuen Kapitels."),
    ]


def test_ohne_passende_ueberschrift_bleibt_die_bekannte_luecke_bei_vers_eins():
    pdf = _baue_pdf([[
        [_vers(3), _text("Das Ende von Kapitel eins.")],
        [_text("Unnumerierter Versanfang ohne Überschrift.")],
        [_vers(2), _text("Zweiter Vers des neuen Kapitels.")],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert verse == [
        (1, 3, "Das Ende von Kapitel eins. Unnumerierter Versanfang ohne Überschrift."),
        (2, 2, "Zweiter Vers des neuen Kapitels."),
    ]


def test_kopfzeile_zaehlt_nicht_zum_verstext():
    pdf = _baue_pdf([[
        ("KOPF", "BUCH 4"),
        [_vers(6), _text("Es waren aber dort sechs steinerne Wasserkrüge.")],
        [_vers(7), _text("Jesus spricht zu ihnen: Füllt die Krüge mit Wasser!")],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert [(k, v) for k, v, _ in verse] == [(1, 6), (1, 7)]
    assert "BUCH" not in verse[0][2] and "4" not in verse[0][2]


def test_zeilenumbruch_mit_bindestrich_wird_ohne_leerzeichen_zusammengefuegt():
    pdf = _baue_pdf([[
        [_text("Er war einer von den beiden, die es von Jo-")],
        [_text("hannes gehört hatten.")],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert verse == [(1, 1, "Er war einer von den beiden, die es von Johannes gehört hatten.")]


def test_ligaturen_werden_ersetzt():
    # Reportlabs Standardschrift kann die Ligatur "ﬁ" nicht selbst darstellen – die Spans direkt aufbauen
    # statt über eine echte PDF, um nur die Ersetzung in `_zeile_aus_spans` zu prüfen.
    from app.adapters.outbound.verse_extractor import _zeile_aus_spans
    spans = [{"text": "Dieser ﬁndet zuerst seinen Bruder.", "font": _KOERPER, "size": _KOERPERGROESSE}]
    zeile = _zeile_aus_spans(spans, _KOERPERGROESSE)
    assert zeile.text == "Dieser findet zuerst seinen Bruder."


def test_ohne_fette_verszahlen_greift_die_alte_textregel_als_rueckfallebene():
    # Wie bei einer per OCR erkannten Textebene (siehe fraktur_ocr.py): keine Schriftart-Unterschiede, die
    # Verszahl steht nur noch als ganz normale Ziffer am Zeilenanfang im Text.
    pdf = _baue_pdf([[
        [_text("2 Dieses war im Anfang bei Gott.")],
        [_text("3 Alles ist durch dasselbe entstanden.")],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert verse == [
        (1, 2, "Dieses war im Anfang bei Gott."),
        (1, 3, "Alles ist durch dasselbe entstanden."),
    ]


def test_unplausibler_zahlensprung_zaehlt_nicht_als_versgrenze():
    pdf = _baue_pdf([[
        [_vers(4), _text("Henoch lebte dreihundertfünfundsechzig Jahre und war")],
        [_text("siebenhundertzweiundachtzig")],
        [_text("Jahre alt, als Gott ihn hinwegnahm.")],
        [_vers(5), _text("Danach ging es weiter.")],
    ]])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 1, None)
    assert [v for _, v, _ in verse] == [4, 5]


def test_nur_das_angefragte_buch_innerhalb_seines_seitenbereichs():
    pdf = _baue_pdf([
        [[_vers(1), _text("Vorangehendes Buch, zählt nicht mit.")]],
        [[_vers(1), _text("Das eigentliche Buch, Vers eins.")]],
        [[_vers(1), _text("Nachfolgendes Buch, zählt nicht mit.")]],
    ])
    verse = PyMuPdfVerseExtractor().buch_verse(pdf, 2, 2)
    assert verse == [(1, 1, "Das eigentliche Buch, Vers eins.")]
