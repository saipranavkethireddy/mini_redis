import os
from pathlib import Path

from src.protocol.resp_encoder import RESPEncoder
from src.protocol.resp_parser import RESPParser


class AppendOnlyFile:
    """
    Append Only File (AOF) persistence and recovery.

    Every command is stored using RESP encoding.
    Commands can later be replayed to reconstruct the store.
    """

    def __init__(self, filepath="appendonly.aof"):
        self.filepath = Path(filepath)

        # Open in binary append mode.
        # Creates the file if it doesn't exist.
        self.file = open(self.filepath, "ab")

    def write(self, command: list):
        """
        Append a command to the AOF.

        Example:
            ["SET", "foo", "bar"]

        is stored as RESP:
            *3\\r\\n
            $3\\r\\nSET\\r\\n
            $3\\r\\nfoo\\r\\n
            $3\\r\\nbar\\r\\n
        """

        if not command:
            return

        encoded = RESPEncoder.encode(command)

        self.file.write(encoded)
        self.file.flush()

        # Ensure the data is pushed to disk.
        os.fsync(self.file.fileno())

    def load(self):
        """
        Read and decode all commands from the AOF.

        Returns:
            List of commands.
        """

        if not self.filepath.exists():
            return []

        with open(self.filepath, "rb") as f:
            data = f.read()

        if not data:
            return []

        parser = RESPParser()
        parser.feed(data)

        commands = []

        while parser._buffer:
            command, success = parser.parse()

            if not success:
                # Ignore an incomplete final command.
                break

            if command is None:
                continue

            if not isinstance(command, list):
                raise ValueError(
                    "Invalid AOF entry: expected RESP array"
                )

            commands.append(command)

        return commands

    def close(self):
        """Flush and close the AOF file."""

        if self.file and not self.file.closed:
            self.file.flush()
            os.fsync(self.file.fileno())
            self.file.close()