import pytest
from src.protocol.resp_parser import RESPParser
from src.protocol.resp_encoder import RESPEncoder

def test_parse_simple_string():
    parser = RESPParser(b"+OK\r\n")
    assert parser.parse() == "OK"

def test_parse_error():
    parser = RESPParser(b"-ERR unknown command\r\n")
    assert parser.parse() == "ERR unknown command"

def test_parse_integer():
    parser = RESPParser(b":1000\r\n")
    assert parser.parse() == 1000

def test_parse_bulk_string():
    parser = RESPParser(b"$5\r\nhello\r\n")
    assert parser.parse() == "hello"

def test_parse_array():
    parser = RESPParser(b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n")
    assert parser.parse() == ["GET", "key"]

def test_encoder():
    assert RESPEncoder.encode_simple_string("OK") == b"+OK\r\n"
    assert RESPEncoder.encode_error("ERR fail") == b"-ERR fail\r\n"
    assert RESPEncoder.encode_integer(42) == b":42\r\n"
    assert RESPEncoder.encode_bulk_string("test") == b"$4\r\ntest\r\n"
    assert RESPEncoder.encode_null() == b"$-1\r\n"