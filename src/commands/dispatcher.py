from typing import List, Any, Callable, Dict
from src.store import Store

from src.commands.string_cmds import(
    handle_ping, handle_incr,handle_del,handle_echo,
    handle_exists,handle_get,handle_set
)
from src.commands.hash_cmds import(
    handle_hdel,handle_hget,handle_hgetall,handle_hset
)
from src.commands.ttl_cmds import (
    handle_expire,handle_persist,handle_ttl
)

commandHandler = Callable[[List[Any],Store],Any]


class CommandDispatcher:
    """Routes parsed RESP commands to dedicated handlers."""

    def __init__(self, store: Store):
        self.store = store
        self._handlers: Dict[str, commandHandler] = {
            "PING": handle_ping,
            "ECHO": handle_echo,
            "SET": handle_set,
            "GET": handle_get,
            "DEL": handle_del,
            "EXISTS": handle_exists,
            "INCR": handle_incr,
            "HSET": handle_hset,
            "HGET": handle_hget,
            "HDEL": handle_hdel,
            "HGETALL": handle_hgetall,
            "EXPIRE": handle_expire,
            "TTL": handle_ttl,
            "PERSIST": handle_persist,
        }

    def dispatch(self, command: List[Any]) -> Any:
        if not command or not isinstance(command, list):
            return Exception("ERR invalid command format")
        
        cmd_name = str(command[0]).upper()
        args = command[1:]

        handler = self._handlers.get(cmd_name)
        if handler is None:
            return Exception(f"ERR unknown command '{cmd_name}")
        
        return handler(args, self.store)


