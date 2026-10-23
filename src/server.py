import asyncio
import logging

# Protocol
from src.protocol.resp_encoder import RESPEncoder
from src.protocol.resp_parser import RESPParser

# Storage & Dispatcher
from src.store import Store
from src.commands.dispatcher import CommandDispatcher

# Persistence
from src.persistence.aof import AppendOnlyFile


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)


class RedisServer:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        aof_filename: str = "appendonly.aof"
    ):
        self.host = host
        self.port = port

        # Storage engine
        self.store = Store()

        # Command router
        self.dispatcher = CommandDispatcher(self.store)

        # Persistence
        self.aof = AppendOnlyFile(aof_filename)

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ):
        peer = writer.get_extra_info("peername")
        logging.info(f"Client connected from {peer}")

        parser = RESPParser()

        try:
            while True:
                data = await reader.read(1024)

                if not data:
                    logging.info(f"Client {peer} disconnected")
                    break

                # Give incoming bytes to our RESP parser
                parser.feed(data)

                # A single TCP read can contain multiple commands
                while True:
                    try:
                        command, success = parser.parse()
                    except Exception as e:
                        logging.error(
                            f"Protocol error from {peer}: {e}"
                        )

                        response = RESPEncoder.encode(
                            Exception(f"ERR Protocol error: {e}")
                        )

                        writer.write(response)
                        await writer.drain()

                        break

                    # Message is incomplete.
                    # Wait for more data from the client.
                    if not success:
                        break

                    if command is None:
                        continue

                    logging.info(f"Command: {command}")

                    # Execute command
                    result = self.dispatcher.dispatch(command)

                    # Persist successful mutating commands
                    cmd_name = str(command[0]).upper()
                    if not isinstance(result, Exception) and cmd_name in {
                        "SET", "DEL", "INCR", "HSET", "HDEL", "EXPIRE", "PERSIST"
                    }:
                        self.aof.write(command)

                    # Send response
                    response = RESPEncoder.encode(result)

                    writer.write(response)
                    await writer.drain()

        except asyncio.CancelledError:
            pass

        except Exception as e:
            logging.error(
                f"Error handling client {peer}: {e}"
            )

        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        """
        Recover the database from the AOF file and
        then start the TCP server.
        """

        # ------------------------------------------------
        # 1. Recover previous state from AOF
        # ------------------------------------------------

        commands = self.aof.load()

        if commands:
            logging.info(
                f"Restoring state from AOF "
                f"({len(commands)} commands)"
            )

            for command in commands:
                result = self.dispatcher.dispatch(command)

                if isinstance(result, Exception):
                    logging.error(
                        f"Failed to replay command: {command}"
                    )

        # ------------------------------------------------
        # 2. Start TCP server
        # ------------------------------------------------

        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )

        logging.info(
            f"Mini Redis server listening on "
            f"{self.host}:{self.port}"
        )

        try:
            async with server:
                await server.serve_forever()

        finally:
            self.aof.close()


if __name__ == "__main__":
    redis_server = RedisServer()

    try:
        asyncio.run(redis_server.start())

    except KeyboardInterrupt:
        logging.info("Server shutting down gracefully...")
        