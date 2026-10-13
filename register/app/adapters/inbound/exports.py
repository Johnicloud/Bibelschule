"""Export des Registers als Liste: CSV (für Excel, Semikolon) oder Text (zum Drucken oder Einfügen)."""
import csv
import io

from app.domain.bible import BibleRef
from app.domain.models import RegisterEntry

KIND_LABEL = {"person": "Name", "place": "Ort"}


def entries_table(entries: list[RegisterEntry]) -> tuple[list[str], list[list[str]]]:
    rows = [[e.name, KIND_LABEL[e.kind], "; ".join(r.format() for r in e.refs)] for e in entries]
    return ["Name", "Art", "Bibelstellen"], rows


def passages_table(pairs: list[tuple[BibleRef, list[RegisterEntry]]]) -> tuple[list[str], list[list[str]]]:
    rows = [[ref.format(), "; ".join(f"{e.name} ({KIND_LABEL[e.kind]})" for e in entries)] for ref, entries in pairs]
    return ["Bibelstelle", "Namen und Orte"], rows


def to_csv(header: list[str], rows: list[list[str]]) -> str:
    """Semikolon als Trenner, damit deutsches Excel die Spalten richtig öffnet."""
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";", lineterminator="\r\n")
    writer.writerow(header)
    writer.writerows(rows)
    return out.getvalue()


def to_text(rows: list[list[str]]) -> str:
    """Abraham (Name): 1Mo 12,1-3; Hebr 11,8   bzw.   1Mo 12,1: Abraham (Name); Haran (Ort)"""
    lines = [f"{r[0]} ({r[1]}): {r[2]}" if len(r) == 3 else f"{r[0]}: {r[1]}" for r in rows]
    return "\n".join(lines) + ("\n" if lines else "")
