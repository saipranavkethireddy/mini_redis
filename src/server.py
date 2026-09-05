import asyncio
import logging
from typing import List, Any

# Protocol
from src.protocol.resp_encoder import RESPEncoder
from src.protocol.resp_parser import RESPParser

# Storage & Dispatcher
from src.store import Store
from src.commands.dispatcher import CommandDispatcher

# Persistence
from src.persistence.aof import AOFManager

# Configure logging to monitor server events in the terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)


class RedisServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 6379, aof_filename: str = "appendonly.aof"):
        self.host = host
        self.port = port

        # Protocol parser & encoder
        self.parser = RESPParser()
        self.encoder = RESPEncoder()

        # Storage engine & Command router
        self.store = Store()
        self.dispatcher = CommandDispatcher(self.store)

        # Persistence engine
        self.aof = AOFManager(filename=aof_filename)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Handles active TCP client socket connection.
        Reads byte streams, parses RESP frames, executes commands, and returns responses.
        """
        peer = writer.get_extra_info("peername")
        logging.info(f"Client connected from {peer}")

        buffer = bytearray()

        try:
            while True:
                # Read data up to 1024 bytes from the non-blocking socket
                data = await reader.read(1024)
                if not data:
                    logging.info(f"Client {peer} disconnected")
                    break

                buffer.extend(data)

                # Decode command frames from byte buffer
                while len(buffer) > 0:
                    try:
                        parsed_cmd, bytes_read = self.parser.parse(buffer)
                    except Exception as e:
                        logging.error(f"Protocol error from {peer}: {e}")
                        err_response = self.encoder.encode(Exception(f"ERR Protocol error: {e}"))
                        writer.write(err_response)
                        await writer.drain()
                        buffer.clear()
                        break

                    if parsed_cmd is None or bytes_read == 0:
                        break

                    del buffer[:bytes_read]

                    # Execute command through dispatcher
                    result = self.dispatcher.dispatch(parsed_cmd)

                    # Log write operations to Append-Only File if execution succeeded
                    if not isinstance(result, Exception):
                        self.aof.log_command(parsed_cmd)

                    # Encode result into RESP format and write back to socket
                    response_bytes = self.encoder.encode(result)
                    writer.write(response_bytes)
                    await writer.drain()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(f"Error handling client {peer}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        """Starts AOF replay to recover state, opens log file, and launches TCP event loop."""
        # 1. Replay existing AOF log to restore in-memory state
        replayed = self.aof.load(self.dispatcher)
        if replayed > 0:
            logging.info(f" Restored state from AOF ({replayed} commands replayed)")

        # 2. Open AOF file handle for append mode
        self.aof.open()

        # 3. Start TCP Listener
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        logging.info(f"🚀 Mini Redis server listening on {self.host}:{self.port}")

        try:
            async with server:
                await server.serve_forever()
        finally:
            # Clean up persistence file handle when server stops
            self.aof.close()


if __name__ == "__main__":
    redis_server = RedisServer(host="127.0.0.1", port=6379)
    try:
        asyncio.run(redis_server.start())
    except KeyboardInterrupt:
        logging.info("Server shutting down gracefully...")