# tests/test_commands.py
import pytest
from src.store import DataStore
from src.commands.dispatcher import CommandDispatcher

def test_dispatcher_ping():
    store = DataStore()
    dispatcher = CommandDispatcher(store)
    res = dispatcher.dispatch(["PING"])
    assert res == "PONG"

def test_dispatcher_set_get():
    store = DataStore()
    dispatcher = CommandDispatcher(store)
    assert dispatcher.dispatch(["SET", "mykey", "myval"]) == "OK"
    assert dispatcher.dispatch(["GET", "mykey"]) == "myval"