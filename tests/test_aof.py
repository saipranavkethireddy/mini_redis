from src.persistence.aof import AppendOnlyFile


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