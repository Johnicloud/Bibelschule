"""`forward()` (Weiterleitung /api/<dienst>/…) braucht ein deutlich längeres Timeout als die eigenen,
schnellen Abfragen des Kerns (health/manifest/status) – manche Dienste befragen Ollama und brauchen bis zu
180 Sekunden (siehe aufgabenleser/pdfcreator). Ein zu kurzes Timeout hätte sie fälschlich als „nicht
erreichbar“ gemeldet (502), obwohl sie nur noch auf die KI warten."""
from unittest.mock import patch

from app.adapters.outbound.http_gateway import HttpServiceGateway


def gw():
    return HttpServiceGateway({"aufgabenleser": "http://aufgabenleser:8000"}, timeout=3.0, forward_timeout=200.0)


def test_forward_uses_the_longer_forward_timeout():
    with patch("app.adapters.outbound.http_gateway.httpx.request") as request:
        request.return_value.status_code = 200
        request.return_value.content = b"{}"
        request.return_value.headers = {"content-type": "application/json"}
        gw().forward("aufgabenleser", "POST", "lesen", "", b"pdf-inhalt", "multipart/form-data")
    assert request.call_args.kwargs["timeout"] == 200.0


def test_health_check_uses_the_short_default_timeout():
    with patch("app.adapters.outbound.http_gateway.httpx.request") as request:
        request.return_value.status_code = 200
        gw().online("aufgabenleser")
    assert request.call_args.kwargs["timeout"] == 3.0


def test_forward_returns_502_when_the_service_does_not_answer_in_time():
    import httpx
    with patch("app.adapters.outbound.http_gateway.httpx.request", side_effect=httpx.ReadTimeout("zu lange")):
        status, body, content_type, extra = gw().forward("aufgabenleser", "POST", "lesen", "", b"", None)
    assert status == 502 and b"nicht erreichbar" in body


def test_forward_reicht_range_durch_und_gibt_die_spul_header_zurueck():
    with patch("app.adapters.outbound.http_gateway.httpx.request") as request:
        request.return_value.status_code = 206
        request.return_value.content = b"abc"
        request.return_value.headers = {"content-type": "audio/mpeg", "content-range": "bytes 0-2/10", "accept-ranges": "bytes", "x-anderes": "nein"}
        status, body, content_type, extra = gw().forward("aufgabenleser", "GET", "datei", "", b"", None, "bytes=0-2")
    assert request.call_args.kwargs["headers"]["Range"] == "bytes=0-2"
    assert (status, content_type) == (206, "audio/mpeg")
    assert extra == {"accept-ranges": "bytes", "content-range": "bytes 0-2/10"}
