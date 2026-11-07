"""Domäne: aus dem Text einer Fragenliste die einzelnen Fragen herauslesen. Reine Textbearbeitung, keine KI."""
import re
import unicodedata

# "12. Frage" oder "12.Frage" am Zeilenanfang
NUMMER = re.compile(r"^\s*\d{1,3}\s*[.)]\s*(?=\S)")


def _sauber(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)             # Ligaturen (ﬁ, ﬂ) und Ähnliches
    text = text.replace("﻿", "").replace("­", "")
    return re.sub(r"\s+", " ", text).strip()


def _verbinden(teile: list[str]) -> str:
    text = ""
    for teil in teile:
        if text.endswith("-") and teil[:1].islower():       # Silbentrennung am Zeilenende
            text = text[:-1] + teil
        else:
            text = f"{text} {teil}".strip()
    return text


def fragen_erkennen(zeilen: list[str]) -> list[str]:
    """Mit Nummern ("1. …", Zeilenumbruch mitten in der Frage möglich) oder ohne (jeder Absatz eine Frage – so
    liefert Word eine automatisch nummerierte Liste, die Nummern stehen dort nicht im Text)."""
    zeilen = [z for z in (_sauber(z) for z in zeilen) if z]
    if sum(1 for z in zeilen if NUMMER.match(z)) >= 2:
        fragen: list[list[str]] = []
        for z in zeilen:
            if NUMMER.match(z):
                fragen.append([NUMMER.sub("", z, count=1)])
            elif fragen:
                fragen[-1].append(z)
        return [f for f in (_verbinden(teile) for teile in fragen) if f]
    return zeilen
