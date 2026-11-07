"""Ausgehender Adapter: meldet diesen Dienst beim Kern an. Danach erscheint er von selbst in der Oberfläche."""
import json
import logging
import time
import urllib.request

log = logging.getLogger(__name__)


def register_with_kern(kern_url: str, name: str, own_url: str, tries: int = 100, pause: float = 3.0) -> bool:
    """Versucht es, bis der Kern antwortet und die Fächer übergeben hat (beim Start laufen oft beide noch hoch)."""
    body = json.dumps({"name": name, "url": own_url}).encode("utf-8")
    for _ in range(tries):
        time.sleep(pause)
        try:
            req = urllib.request.Request(kern_url.rstrip("/") + "/api/registry", data=body,
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if json.loads(resp.read()).get("synced"):
                    log.info("Beim Kern angemeldet.")
                    return True
        except Exception as e:
            log.info("Kern noch nicht bereit: %s", e)
    log.warning("Anmeldung beim Kern nicht gelungen. Beim nächsten Start wird es erneut versucht.")
    return False
