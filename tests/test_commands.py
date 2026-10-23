import pytest
from src.store import Store
from src.commands.dispatcher import CommandDispatcher


@pytest.fixture
def d():
    return CommandDispatcher(Store())


def test_ping(d):
    assert d.dispatch(["PING"]) == "PONG"


def test_set_get(d):
    assert d.dispatch(["SET", "k", "v"]) == "OK"
    assert d.dispatch(["GET", "k"]) == "v"


def test_lowercase_command(d):
    assert d.dispatch(["set", "k", "v"]) == "OK"
    assert d.dispatch(["get", "k"]) == "v"


# --- bugs ---
def test_hset_via_dispatcher(d):                      # hest typo
    assert d.dispatch(["HSET", "u", "name", "sai"]) == 1
    assert d.dispatch(["HGET", "u", "name"]) == "sai"


def test_expire_then_ttl(d):                          # swapped args
    d.dispatch(["SET", "k", "v"])
    assert d.dispatch(["EXPIRE", "k", "10"]) == 1
    assert 0 < d.dispatch(["TTL", "k"]) <= 10


def test_set_with_ex(d):                              # len(args) > 4
    d.dispatch(["SET", "k", "v", "EX", "10"])
    assert 0 < d.dispatch(["TTL", "k"]) <= 10


def test_unknown_command_message(d):
    assert str(d.dispatch(["FOO"])) == "ERR unknown command 'FOO'"


# --- edge cases ---
def test_persist(d):
    d.dispatch(["SET", "k", "v", "EX", "10"])
    assert d.dispatch(["PERSIST", "k"]) == 1
    assert d.dispatch(["TTL", "k"]) == -1


def test_ttl_missing_and_no_expiry(d):
    assert d.dispatch(["TTL", "nope"]) == -2
    d.dispatch(["SET", "k", "v"])
    assert d.dispatch(["TTL", "k"]) == -1


def test_wrongtype_get_on_hash(d):
    d.dispatch(["HSET", "h", "f", "v"])
    assert "WRONGTYPE" in str(d.dispatch(["GET", "h"]))


def test_wrongtype_hset_on_string(d):
    d.dispatch(["SET", "s", "v"])
    assert "WRONGTYPE" in str(d.dispatch(["HSET", "s", "f", "v"]))


def test_incr(d):
    assert d.dispatch(["INCR", "c"]) == 1
    assert d.dispatch(["INCR", "c"]) == 2
    d.dispatch(["SET", "s", "abc"])
    assert isinstance(d.dispatch(["INCR", "s"]), Exception)


@pytest.mark.parametrize("cmd", [["GET"], ["SET", "k"], ["HGET", "h"], ["EXPIRE", "k"], ["TTL"]])
def test_wrong_arg_count(d, cmd):
    assert isinstance(d.dispatch(cmd), Exception)