# tests/test_store.py
import time
import pytest
from src.store import DataStore

def test_set_and_get():
    store = DataStore()
    store.set("foo", "bar")
    assert store.get("foo") == "bar"

def test_get_expired():
    store = DataStore()
    store.set("foo", "bar", px=10)
    time.sleep(0.02)
    assert store.get("foo") is None

def test_delete():
    store = DataStore()
    store.set("foo", "bar")
    assert store.delete("foo") == 1
    assert store.get("foo") is None
    assert store.delete("foo") == 0