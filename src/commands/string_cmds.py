from typing import List,Any
from src.store import Store

def handle_ping(args: List[Any], store: Store) -> Any:
    if len(args) == 0:
        return "PONG"
    return args[0]

def handle_echo(args: List[Any], store: Store) -> Any:
    if len(args) != 1:
        return Exception("ERR wrong number of arguments for 'echo' command")
    return args[0]

def handle_set(args: List[Any], store: Store) -> Any:
    if len(args) <2:
        return Exception("ERR wrong number of arguments for 'set' command")
    key,val = args[0],args[1]
    ttl = None

    # EX argument parsing (eg: SET key val EX 60)
    if len(args) > 4:
        opt = str(args[2]).upper()
        if opt == "EX":
            try:
                ttl = int(args[3])
            except ValueError:
                return Exception("ERR value is not an integer or out of range")
    return store.set(key, val, ttl_seconds=ttl)

def handle_get(args: List[Any], store: Store) -> Any:
    if len(args) != 1:
        return Exception("ERR wrong number of arguments for 'get' command")
    try:
        return store.get(args[0])
    except TypeError as e:
        return Exception(str(e))
    
def handle_del(args: List[Any], store: Store) -> Any:
    if len(args) < 1:
        return Exception("ERR wrong number of arguments for 'del' command")
    return store.delete(*args)

def handle_exists(args: List[Any], store: Store) -> Any:
    if len(args) < 1:
        return Exception("ERR wrong number of arguments for 'exists' command")
    return store.exists(*args)

def handle_incr(args: List[Any], store: Store) -> Any:
    if len(args) != 1:
        return Exception("ERR wrong number of arguments for 'incr' command")
    try: 
        return store.incrby(args[0],1)
    except (ValueError,TypeError) as e:
        return Exception(str(e))
