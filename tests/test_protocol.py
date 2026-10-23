from src.protocol.resp_parser import RESPParser
from src.protocol.resp_encoder import RESPEncoder


def parse(data):
    parser = RESPParser()
    parser.feed(data)
    return parser.parse()


def test_parse_simple_string():
    value, success = parse(b"+OK\r\n")

    assert success is True
    assert value == "OK"


def test_parse_error():
    value, success = parse(b"-ERR unknown command\r\n")

    assert success is True
    assert isinstance(value, Exception)
    assert str(value) == "ERR unknown command"


def test_parse_integer():
    value, success = parse(b":1000\r\n")

    assert success is True
    assert value == 1000


def test_parse_bulk_string():
    value, success = parse(b"$5\r\nhello\r\n")

    assert success is True
    assert value == "hello"


def test_parse_null_bulk_string():
    value, success = parse(b"$-1\r\n")

    assert success is True
    assert value is None


def test_parse_array():
    value, success = parse(
        b"*2\r\n"
        b"$3\r\nGET\r\n"
        b"$3\r\nkey\r\n"
    )

    assert success is True
    assert value == ["GET", "key"]


def test_parse_incomplete_message():
    parser = RESPParser()

    parser.feed(b"$5\r\nhel")

    value, success = parser.parse()

    assert success is False
    assert value is None


def test_encoder():
    assert RESPEncoder.encode(100) == b":100\r\n"

    assert RESPEncoder.encode("hello") == (
        b"$5\r\nhello\r\n"
    )

    assert RESPEncoder.encode(None) == b"$-1\r\n"

    assert RESPEncoder.encode(["GET", "key"]) == (
        b"*2\r\n"
        b"$3\r\nGET\r\n"
        b"$3\r\nkey\r\n"
    )

def test_encode_bool():
    assert RESPEncoder.encode(True) == b":1\r\n"     # fails now


def test_encode_error():
    assert RESPEncoder.encode(Exception("ERR x")) == b"-ERR ERR x\r\n"


def test_pipelined_commands():
    p = RESPParser()
    p.feed(b"*1\r\n$4\r\nPING\r\n*1\r\n$4\r\nPING\r\n")
    assert p.parse() == (["PING"], True)
    assert p.parse() == (["PING"], True)


def test_array_split_across_feeds():
    p = RESPParser()
    p.feed(b"*2\r\n$3\r\nGET\r\n$3\r\nk")
    assert p.parse() == (None, False)
    p.feed(b"ey\r\n")
    assert p.parse() == (["GET", "key"], True)


def test_bulk_with_crlf_inside():
    p = RESPParser()
    p.feed(b"$4\r\na\r\nb\r\n")
    assert p.parse() == ("a\r\nb", True)


def test_empty_and_null_array():
    assert parse(b"*0\r\n") == ([], True)
    assert parse(b"*-1\r\n") == (None, True)


import pytest

@pytest.mark.parametrize("bad", [b"!oops\r\n", b"$abc\r\n", b"$3\r\nabcXX"])
def test_invalid_input_raises(bad):
    with pytest.raises(ValueError):
        parse(bad)