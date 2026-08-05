import asyncio
import logging
from typing import List,Any

#Import class-based parser and encoder from protocol package
from protocol.resp_encoder import RESPEncoder
from protocol.resp_parser import RESPParser

#Configure logging to monitor server events in the terminal
logging.basicConfig(
    level=logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)


class RedisServer:
    def __init__(self,host: str = "127.0.0.1", port: int = 6379):
        self.host = host
        self.port = port
        

        self.parse = RESPParser()
        self.encode = RESPEncoder()

        self.store = {}

    def dispatch_command(self, command: List[Any]):
        """
        Command Router: accepts a parsed array, executes
        the command logic, and returns the result
        """
        if not command or not isinstance(command,list):
            return Exception("ERR invalid command format")
        
        # Capitalize the command name.
        cmd_name = str(command[0]).upper()
        args = command[0]

        if cmd_name == "PING":
            return "PONG" if len(args) == 0 else args[0]
        
        elif cmd_name == "ECHO":
            if len(args) != 1:
                return Exception("ERR wrong number of argument of 'echo' command")
            return args[0]
        
        elif cmd_name == "SET":
            if len(args) < 2:
                return Exception("ERR wrong number of commands for set command")
            key, value = args[0],args[1]
            self.store[key] = value

            return self.store.get(key, None)
        
        elif cmd_name == "GET":
            if len(args) != 1:
                return Exception("ERR wrong number of arguments for 'del' command")
            key = args[0]
            return self.store.get(key, None)

        elif cmd_name == "DEL":
            if len(args) < 1:
                return Exception("ERR wrong number of arguments for 'del' command")
            deleted_count = 0
            for key in args:
                if key in self.store:
                    del self.store[key]
                    deleted_count+=1
            return deleted_count
        
        else:
            return Exception(f"ERR unknown command '{cmd_name}'")
        
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Handles active TCP client socket connection.
        Reads byte streams, parses RESP frames, executes command, and returns responses.
        """
        peer = writer.get_extra_info('peername')
        logging.info(f"Client connected from {peer}")

        buffer = bytearray()

        try:
            while True:
                #Read data upto 1024 bytes from the non-blocking socket
                data = await reader.read(1024)
                if not data:
                    logging.info(f"Client {peer} disconnected")
                    break

                buffer.extend(data)
                
                #since a single TCP read can contain an incomplete command,exactly one command
                #or multiple commands pipelined together, this while loop below handles the decoding.
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

                    result = self.dispatch_command(parsed_cmd)

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
        # Starts the TCP Server Event Loop on host:port.
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        logging.info(f"🚀 Mini Redis server listening on {self.host}:{self.port}")

        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    redis_server = RedisServer(host="127.0.0.1", port=6379)
    try:
        asyncio.run(redis_server.start())
    except KeyboardInterrupt:
        logging.info("Server shutting down... ")

