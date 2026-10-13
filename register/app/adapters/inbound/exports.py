"""Export eines Registers als Liste: CSV (für Excel, Semikolon) oder Text (zum Drucken oder Einfügen)."""
import csv
import io

from app.domain.bible import BibleRef
from app.domain.models import RegisterEntry


def entries_table(entries: list[RegisterEntry], names: dict[str, str]) -> tuple[list[str], list[list[str]]]:
    """names: Register-ID -> Name des Registers."""
    rows = [[e.name, names.get(e.register_id, ""), "; ".join(r.format() for r in e.refs)] for e in entries]
    return ["Name", "Register", "Bibelstellen"], rows


def passages_table(pairs: list[tuple[BibleRef, list[RegisterEntry]]], names: dict[str, str]) -> tuple[list[str], list[list[str]]]:
    rows = [[ref.format(), "; ".join(f"{e.name} ({names.get(e.register_id, '')})" for e in entries)] for ref, entries in pairs]
    return ["Bibelstelle", "Einträge"], rows


def to_csv(header: list[str], rows: list[list[str]]) -> str:
    """Semikolon als Trenner, damit deutsches Excel die Spalten richtig öffnet."""
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";", lineterminator="\r\n")
    writer.writerow(header)
    writer.writerows(rows)
    return out.getvalue()


def to_text(rows: list[list[str]]) -> str:
    """Abraham (Namen): 1Mo 12,1-3; Hebr 11,8   bzw.   1Mo 12,1: Abraham (Namen); Haran (Orte)"""
    lines = [f"{r[0]} ({r[1]}): {r[2]}" if len(r) == 3 else f"{r[0]}: {r[1]}" for r in rows]
    return "\n".join(lines) + ("\n" if lines else "")
