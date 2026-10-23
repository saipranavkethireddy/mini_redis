import asyncio
from src.server import RedisServer


async def _with_server(tmp_path, fn):
    srv = RedisServer(aof_filename=str(tmp_path / "s.aof"))
    server = await asyncio.start_server(srv.handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        return await fn(port, srv)
    finally:
        server.close()
        await server.wait_closed()
        srv.aof.close()


async def _send(port, payload, expect_bytes=None):
    r, w = await asyncio.open_connection("127.0.0.1", port)
    w.write(payload)
    await w.drain()
    data = await asyncio.wait_for(r.read(4096), timeout=2)
    w.close()
    return data


def test_ping_over_socket(tmp_path):
    async def run(port, srv):
        return await _send(port, b"*1\r\n$4\r\nPING\r\n")
    assert asyncio.run(_with_server(tmp_path, run)) == b"$4\r\nPONG\r\n"


def test_lowercase_set_is_persisted(tmp_path):        # fails now
    async def run(port, srv):
        await _send(port, b"*3\r\n$3\r\nset\r\n$1\r\nk\r\n$1\r\nv\r\n")
        return srv.aof.load()
    assert asyncio.run(_with_server(tmp_path, run)) == [["set", "k", "v"]]


def test_recovers_after_protocol_error(tmp_path):     # fails now (buffer not cleared)
    async def run(port, srv):
        r, w = await asyncio.open_connection("127.0.0.1", port)
        w.write(b"!garbage\r\n")
        await w.drain()
        await asyncio.wait_for(r.read(4096), timeout=2)        # error reply
        w.write(b"*1\r\n$4\r\nPING\r\n")
        await w.drain()
        data = await asyncio.wait_for(r.read(4096), timeout=2)
        w.close()
        return data
    assert b"PONG" in asyncio.run(_with_server(tmp_path, run))

def test_expire_logged_as_absolute(tmp_path):
    async def run(port, srv):
        await _send(port, b"*3\r\n$3\r\nSET\r\n$1\r\nk\r\n$1\r\nv\r\n")
        await _send(port, b"*3\r\n$6\r\nEXPIRE\r\n$1\r\nk\r\n$2\r\n10\r\n")
        return srv.aof.load()
    cmds = asyncio.run(_with_server(tmp_path, run))
    assert cmds[-1][0] == "EXPIREAT"