from typing import List,Any
from src.store import Store

def handle_hset(args: List[Any], store: Store) -> Any:
    if len(args) != 3:
        return Exception("ERR wrong number of arguments for 'hset' command")
    try:
        return store.hest(args[0],args[1],args[2])
    except TypeError as e:
        return Exception(str(e))
    
def handle_hget(args: List[Any], store: Store) -> Any:
    if len(args) != 2:
        return Exception("ERR wrong number of arguments for 'hget' command")
    try:
        return store.hget(args[0], args[1])
    except TypeError as e:
        return Exception(str(e))
    
def handle_hdel(args: List[Any], store: Store) -> Any:
    if len(args) < 2:
        return Exception("ERR wrong number of arguments for 'hdel' command")
    try:
        return store.hdel(args[0], *args[1:])
    except TypeError as e:
        return Exception(str(e))
    
def handle_hgetall(args: List[Any], store: Store) -> Any:
    if len(args) != 1:
        return Exception("ERR wrong number of arguments for 'hgetall' command")
    try:
        return store.hgetall(args[0])
    except TypeError as e:
        return Exception(str(e))