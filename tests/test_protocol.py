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