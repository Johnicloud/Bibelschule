from datetime import datetime, timedelta, timezone

from app.adapters.outbound.memory_session_store import MemorySessionStore


def test_session_is_valid_right_after_creation():
    now = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
    store = MemorySessionStore(idle_timeout=timedelta(minutes=15), now=lambda: now)
    token = store.create("konto-1")
    assert store.account_id_for(token) == "konto-1"


def test_session_expires_after_idle_timeout():
    now = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
    store = MemorySessionStore(idle_timeout=timedelta(minutes=15), now=lambda: now)
    token = store.create("konto-1")
    now += timedelta(minutes=16)
    assert store.account_id_for(token) is None


def test_activity_pushes_the_timeout_back(monkeypatch):
    now = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
    store = MemorySessionStore(idle_timeout=timedelta(minutes=15), now=lambda: now)
    token = store.create("konto-1")
    now += timedelta(minutes=10)
    assert store.account_id_for(token) == "konto-1"   # noch da, zählt als Aktivität
    now += timedelta(minutes=10)                       # 20 Min seit Anlage, aber nur 10 seit letzter Aktivität
    assert store.account_id_for(token) == "konto-1"


def test_delete_and_unknown_token():
    store = MemorySessionStore()
    token = store.create("konto-1")
    store.delete(token)
    assert store.account_id_for(token) is None
    assert store.account_id_for("gibt-es-nicht") is None
