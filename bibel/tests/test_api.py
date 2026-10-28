from app.adapters.inbound.api import index_out
from app.domain.models import Bibelindex, Buchseite


def test_index_nennt_die_kapitelzahl_je_buch():
    # Für das Bücherregal der Oberfläche: Dicke und Kapitelauswahl brauchen die Zahl der Kapitel.
    index = Bibelindex(buchseiten=[Buchseite(buch_index=0, seite=5), Buchseite(buch_index=18, seite=300),
                                   Buchseite(buch_index=65, seite=1300)], dateiname="b.pdf")
    kapitel = {b["short"]: b["kapitel_gesamt"] for b in index_out(index)["buecher"]}
    assert kapitel == {"1Mo": 50, "Ps": 150, "Offb": 22}
