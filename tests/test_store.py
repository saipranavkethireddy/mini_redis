import time

from src.store import Store


def test_set_and_get():
    store = Store()

    assert store.set("foo", "bar") == "OK"
    assert store.get("foo") == "bar"


def test_get_missing():
    store = Store()

    assert store.get("missing") is None


def test_get_expired():
    store = Store()

    store.set("foo", "bar", ttl_seconds=1)

    assert store.get("foo") == "bar"

    time.sleep(1.1)

    assert store.get("foo") is None


def test_delete():
    store = Store()

    store.set("foo", "bar")

    assert store.delete("foo") == 1
    assert store.get("foo") is None


def test_exists():
    store = Store()

    store.set("foo", "bar")

    assert store.exists("foo") == 1
    assert store.exists("missing") == 0


def test_incrby():
    store = Store()

    store.set("counter", "10")

    assert store.incrby("counter", 5) == 15
    assert store.get("counter") == "15"


def test_hset_and_hget():
    store = Store()

    assert store.hset("user", "name", "Pranav") == 1
    assert store.hget("user", "name") == "Pranav"


def test_hgetall():
    store = Store()

    store.hset("user", "name", "Pranav")
    store.hset("user", "age", "19")

    result = store.hgetall("user")

    assert result == ["name", "Pranav", "age", "19"]

def test_ttl_with_fake_clock(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("src.store.time.time", lambda: now[0])
    s = Store()
    s.set("k", "v", ttl_seconds=10)
    now[0] += 9.5
    assert s.ttl("k") == 1          # fails now: int() truncates to 0 → deleted
    now[0] += 1
    assert s.get("k") is None


def test_set_clears_old_ttl():
    s = Store()
    s.set("k", "v", ttl_seconds=10)
    s.set("k", "v2")
    assert s.ttl("k") == -1


def test_hdel_last_field_removes_key():
    s = Store()
    s.hset("h", "f", "v")
    assert s.hdel("h", "f") == 1
    assert s.exists("h") == 0


def test_hset_update_returns_zero():
    s = Store()
    s.hset("h", "f", "v")
    assert s.hset("h", "f", "v2") == 0


def test_multi_key_del_exists():
    s = Store()
    s.set("a", "1"); s.set("b", "2")
    assert s.exists("a", "b", "c") == 2
    assert s.delete("a", "b", "c") == 2


def test_expire_missing_key():
    assert Store().expire("nope", 10) == 0