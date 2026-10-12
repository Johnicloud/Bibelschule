"""Ausgehender Adapter: das Dienstverzeichnis (Name -> URL) und HTTP zu den Diensten."""
import json
import logging

import httpx

from app.application.ports import ServiceGateway

log = logging.getLogger(__name__)


def parse_services(text: str) -> dict[str, str]:
    """'karteikarten=http://karteikarten:8000,register=http://register:8000' -> {Name: URL}"""
    out = {}
    for part in (text or "").split(","):
        if "=" in part:
            name, url = part.split("=", 1)
            if name.strip() and url.strip():
                out[name.strip()] = url.strip().rstrip("/")
    return out


class HttpServiceGateway(ServiceGateway):
    def __init__(self, services: dict[str, str], timeout: float = 3.0):
        self.services = services
        self.timeout = timeout

    def names(self) -> list[str]:
        return list(self.services)

    def _request(self, service: str, method: str, path: str, **kw) -> httpx.Response | None:
        try:
            return httpx.request(method, self.services[service] + path, timeout=self.timeout, **kw)
        except httpx.HTTPError as e:
            log.warning("Dienst %s nicht erreichbar: %s", service, e)
            return None

    def online(self, service: str) -> bool:
        r = self._request(service, "GET", "/api/health")
        return r is not None and r.status_code == 200

    def put_subject(self, service: str, subject_id: str, name: str) -> bool:
        r = self._request(service, "PUT", f"/api/subjects/{subject_id}", json={"name": name})
        return r is not None and r.status_code < 300

    def delete_subject(self, service: str, subject_id: str) -> bool:
        r = self._request(service, "DELETE", f"/api/subjects/{subject_id}")
        return r is not None and r.status_code < 300

    def status(self, service: str, subject_id: str) -> dict | None:
        r = self._request(service, "GET", f"/api/subjects/{subject_id}/status")
        return r.json() if r is not None and r.status_code == 200 else None

    def forward(self, service: str, method: str, path: str, query: str, body: bytes,
                content_type: str | None) -> tuple[int, bytes, str]:
        url = f"/api/{path}" + (f"?{query}" if query else "")
        headers = {"Content-Type": content_type} if content_type else None
        r = self._request(service, method, url, content=body or None, headers=headers)
        if r is None:
            detail = json.dumps({"detail": f"Der Dienst „{service}“ ist gerade nicht erreichbar."}, ensure_ascii=False)
            return 502, detail.encode("utf-8"), "application/json"
        return r.status_code, r.content, r.headers.get("content-type", "application/json")
