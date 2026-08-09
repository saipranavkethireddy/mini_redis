from typing import List, Any
from src.store import Store

def handle_expire(args: List[Any], store: Store) -> Any:
    if len(args) != 2:
        return Exception("ERR wrong number of arguments for 'expire' command")
    try:
        seconds = int(args[0])
    except ValueError:
        return Exception("ERR value is not an integer or out of range")
    return store.expire(args[0], seconds)

def handle_ttl(args: List[Any], store: Store) -> Any:
    if len(args) != 1:
        return Exception("ERR wrong number of arguments for 'ttl' command")
    return store.ttl(args[0])

def handle_persist(args: List[Any], store: Store) -> Any:
    if len(args) != 1:
        return Exception("ERR wrong number of arguments for 'persist' command")
    return store.persist(args[0])
