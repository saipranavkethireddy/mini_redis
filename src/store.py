import time
from typing import Any, Dict, Optional, List, Union


class Store:
    """In-Memory Storage Engine supporting Strings, Hashes, and TTL Expiration."""

    def __init__(self):
        # Main key-value storage: map[key] -> value
        self._data: Dict[str, Any] = {}
        # Expiration registry: map[key] -> unix_timestamp (float)
        self._expires: Dict[str, float] = {}

    # -------------------------------------------------
    # EXPIRATION & TTL ENGINE
    # -------------------------------------------------

    def _is_expired(self, key: str) -> bool:
        """
        Passive Eviction: Checks if a key has passed its expiration time.
        If expired, automatically purges the key from memory.
        """
        if key in self._expires:
            if time.time() >= self._expires[key]:
                self.delete(key)
                return True
        return False

    def expire(self, key: str, seconds: int) -> int:
        """
        Sets a timeout on key (in seconds).
        Returns 1 if expiration was set, 0 if key does not exist.
        """
        if self._is_expired(key) or key not in self._data:
            return 0
        
        self._expires[key] = time.time() + seconds
        return 1

    def ttl(self, key: str) -> int:
        """
        Gets remaining time-to-live of a key in seconds.
        Returns:
          -2 if key does not exist (or expired)
          -1 if key exists but has no associated expire
          integer TTL in seconds otherwise
        """
        if self._is_expired(key) or key not in self._data:
            return -2
        if key not in self._expires:
            return -1

        remaining = int(self._expires[key] - time.time())
        if remaining <= 0:
            self.delete(key)
            return -2
        return remaining

    def persist(self, key: str) -> int:
        """Removes the existing timeout on key, turning it into a persistent key."""
        if self._is_expired(key) or key not in self._data:
            return 0
        if key in self._expires:
            del self._expires[key]
            return 1
        return 0

    # -------------------------------------------------
    # KEY MANAGEMENT & STRING COMMANDS
    # -------------------------------------------------

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> str:
        """Sets key to hold string/value. Optionally sets TTL in seconds."""
        self._data[key] = str(value)
        
        # Overwriting a key clears previous expiration unless explicitly specified
        if ttl_seconds is not None:
            self._expires[key] = time.time() + ttl_seconds
        else:
            self._expires.pop(key, None)
            
        return "OK"

    def get(self, key: str) -> Optional[str]:
        """Gets value of key. Returns None if key does not exist or is wrong type."""
        if self._is_expired(key):
            return None

        val = self._data.get(key, None)
        if val is None:
            return None
            
        if not isinstance(val, str):
            raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")
            
        return val

    def delete(self, *keys: str) -> int:
        """Deletes one or more keys. Returns the count of deleted keys."""
        deleted_count = 0
        for key in keys:
            # Clean up expiration tracking regardless
            self._expires.pop(key, None)
            if key in self._data:
                del self._data[key]
                deleted_count += 1
        return deleted_count

    def exists(self, *keys: str) -> int:
        """Returns count of existing non-expired keys."""
        count = 0
        for key in keys:
            if not self._is_expired(key) and key in self._data:
                count += 1
        return count

    def incrby(self, key: str, increment: int = 1) -> int:
        """Increments the number stored at key by increment integer."""
        if self._is_expired(key):
            self.delete(key)

        val = self._data.get(key, "0")
        try:
            current_num = int(val)
        except ValueError:
            raise ValueError("ERR value is not an integer or out of range")

        new_val = current_num + increment
        self._data[key] = str(new_val)
        return new_val

    # =====================================================================
    # HASH DATA STRUCTURE COMMANDS
    # =====================================================================

    def hset(self, key: str, field: str, value: str) -> int:
        """
        Sets field in hash stored at key to value.
        Returns 1 if field is new, 0 if field was updated.
        """
        if self._is_expired(key):
            self.delete(key)

        if key not in self._data:
            self._data[key] = {}
        elif not isinstance(self._data[key], dict):
            raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

        is_new_field = field not in self._data[key]
        self._data[key][field] = str(value)
        return 1 if is_new_field else 0

    def hget(self, key: str, field: str) -> Optional[str]:
        """Gets value associated with field in hash stored at key."""
        if self._is_expired(key):
            return None

        hash_map = self._data.get(key)
        if hash_map is None:
            return None
        if not isinstance(hash_map, dict):
            raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

        return hash_map.get(field, None)

    def hdel(self, key: str, *fields: str) -> int:
        """Removes specified fields from hash stored at key."""
        if self._is_expired(key) or key not in self._data:
            return 0

        hash_map = self._data.get(key)
        if not isinstance(hash_map, dict):
            raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

        count = 0
        for field in fields:
            if field in hash_map:
                del hash_map[field]
                count += 1

        # Delete empty hash from main store
        if len(hash_map) == 0:
            self.delete(key)

        return count

    def hgetall(self, key: str) -> List[str]:
        """Returns all fields and values of hash stored at key as a flat array."""
        if self._is_expired(key):
            return []

        hash_map = self._data.get(key)
        if hash_map is None:
            return []
        if not isinstance(hash_map, dict):
            raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

        result = []
        for f, v in hash_map.items():
            result.extend([f, v])
        return result