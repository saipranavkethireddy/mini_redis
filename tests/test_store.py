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