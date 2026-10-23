from src.persistence.aof import AppendOnlyFile
from src.store import Store
from src.commands.dispatcher import CommandDispatcher


def replay(path):
    """Simulate a server restart: load the AOF into a fresh store."""
    aof = AppendOnlyFile(path)
    d = CommandDispatcher(Store())
    for command in aof.load():
        d.dispatch(command)
    aof.close()
    return d


def test_aof_write_and_load(tmp_path):
    path = tmp_path / "appendonly.aof"

    aof = AppendOnlyFile(path)
    aof.write(["SET", "foo", "bar"])
    aof.write(["SET", "name", "Pranav"])
    aof.write(["DEL", "foo"])
    aof.close()

    recovered = AppendOnlyFile(path)
    commands = recovered.load()
    recovered.close()

    assert commands == [
        ["SET", "foo", "bar"],
        ["SET", "name", "Pranav"],
        ["DEL", "foo"],
    ]


def test_restart_restores_state(tmp_path):
    path = tmp_path / "appendonly.aof"

    aof = AppendOnlyFile(path)
    aof.write(["SET", "k", "v"])
    aof.write(["HSET", "h", "f", "v"])
    aof.write(["INCR", "c"])
    aof.close()

    d = replay(path)

    assert d.dispatch(["GET", "k"]) == "v"
    assert d.dispatch(["HGET", "h", "f"]) == "v"   # fails until HSET typo is fixed
    assert d.dispatch(["GET", "c"]) == "1"


def test_replay_respects_delete(tmp_path):
    path = tmp_path / "appendonly.aof"

    aof = AppendOnlyFile(path)
    aof.write(["SET", "k", "v"])
    aof.write(["DEL", "k"])
    aof.close()

    d = replay(path)

    assert d.dispatch(["GET", "k"]) is None


def test_truncated_last_command_ignored(tmp_path):
    path = tmp_path / "appendonly.aof"
    path.write_bytes(
        b"*3\r\n$3\r\nSET\r\n$1\r\nk\r\n$1\r\nv\r\n"
        b"*2\r\n$3\r\nGE"            # crash mid-write
    )

    aof = AppendOnlyFile(path)
    commands = aof.load()
    aof.close()

    assert commands == [["SET", "k", "v"]]


def test_empty_file(tmp_path):
    aof = AppendOnlyFile(tmp_path / "empty.aof")
    commands = aof.load()
    aof.close()

    assert commands == []


def test_appends_across_reopen(tmp_path):
    path = tmp_path / "appendonly.aof"

    first = AppendOnlyFile(path)
    first.write(["SET", "a", "1"])
    first.close()

    second = AppendOnlyFile(path)
    second.write(["SET", "b", "2"])
    commands = second.load()
    second.close()

    assert commands == [["SET", "a", "1"], ["SET", "b", "2"]]