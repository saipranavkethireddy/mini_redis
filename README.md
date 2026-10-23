# mini_redis

A Redis-compatible in-memory key-value server written from scratch in Python. It speaks the Redis Serialization Protocol (RESP), so it works with `redis-cli` and standard Redis client libraries. It supports strings, hashes, TTL expiration, and append-only-file (AOF) persistence.

Built to understand how Redis works under the hood: wire protocols, event-loop networking, expiration strategies, and durability.

## Features

- **RESP parser and encoder.** Supports simple strings, errors, integers, bulk strings, and arrays. The parser is incremental, so it handles partial TCP reads and pipelined commands.
- **Async networking.** A single-threaded `asyncio` event loop serves many concurrent clients, the same model Redis itself uses.
- **Data types.** Strings and hashes, with Redis-style `WRONGTYPE` errors.
- **TTL expiration.** Keys expire passively: an expired key is removed when it is next accessed.
- **AOF persistence.** Every write is appended to disk in RESP format and fsynced. On startup the log is replayed to rebuild state. Relative expiries (`EXPIRE`, `SET ... EX`) are logged as absolute `EXPIREAT` timestamps, so TTLs stay correct across restarts.

## Supported commands

| Category   | Commands                                                     |
| ---------- | ------------------------------------------------------------ |
| Connection | `PING`, `ECHO`                                               |
| Strings    | `SET key value [EX seconds]`, `GET`, `DEL`, `EXISTS`, `INCR` |
| Hashes     | `HSET`, `HGET`, `HDEL`, `HGETALL`                            |
| Expiration | `EXPIRE`, `EXPIREAT`, `TTL`, `PERSIST`                       |

## Architecture

```
client ──TCP──▶ server.py (asyncio)
                   │
                   ▼
           RESPParser (bytes → command list)
                   │
                   ▼
           CommandDispatcher ──▶ string / hash / ttl handlers
                   │                        │
                   │                        ▼
                   │                     Store (dict + expiry map)
                   ▼
           AppendOnlyFile (write commands → appendonly.aof)
                   │
                   ▼
           RESPEncoder (result → bytes) ──▶ client
```

```
src/
├── server.py              # asyncio TCP server, AOF replay on startup
├── store.py               # in-memory engine: strings, hashes, TTL
├── protocol/
│   ├── resp_parser.py     # incremental RESP decoder
│   └── resp_encoder.py    # RESP encoder
├── commands/
│   ├── dispatcher.py      # routes command name → handler
│   ├── string_cmds.py
│   ├── hash_cmds.py
│   └── ttl_cmds.py
└── persistence/
    └── aof.py             # append-only file write + load
tests/                     # pytest suite
```

## Getting started

Requires Python 3.9+.

```bash
git clone https://github.com/saipranavkethireddy/mini_redis.git
cd mini_redis
python -m src.server        # listens on 127.0.0.1:6379
```

Connect with `redis-cli`:

```bash
$ redis-cli
127.0.0.1:6379> SET name pranav EX 60
OK
127.0.0.1:6379> GET name
"pranav"
127.0.0.1:6379> TTL name
(integer) 57
127.0.0.1:6379> HSET user city Hyderabad
(integer) 1
127.0.0.1:6379> HGETALL user
1) "city"
2) "Hyderabad"
```

Or use Python:

```python
import redis
r = redis.Redis(port=6379, decode_responses=True)
r.set("counter", 0)
r.incr("counter")
```

## Running tests

```bash
pip install pytest
pytest -v
```

The suite covers four layers:

- **Store:** data types, TTL logic (using a mocked clock, so no `sleep`), and WRONGTYPE errors.
- **Protocol:** RESP parsing and encoding, pipelined commands, partial reads, and malformed input.
- **Dispatcher:** every command, argument validation, and case-insensitive command names.
- **Server and AOF (integration):** real TCP connections, recovery after a protocol error, persistence of writes, and state restoration after a simulated restart.

Testing through the dispatcher and a real socket surfaced several bugs that store-level unit tests had missed. The git history shows the failing tests committed first, followed by one fix per commit.

## Design notes

- **Why asyncio instead of threads.** Commands are cheap, in-memory operations, so one event loop avoids locks entirely and mirrors Redis's single-threaded model.
- **Passive expiration.** Expired keys are deleted lazily on access. Real Redis also runs active sampling to reclaim memory from keys that are never read again.
- **AOF durability.** Every write is fsynced, which gives the strongest durability but the lowest write throughput. Redis's default instead fsyncs once per second.
- **Absolute TTLs in the AOF.** A relative `EXPIRE k 10` replayed after a restart would wrongly reset the countdown, so expiries are logged as absolute timestamps, as real Redis does.

## Limitations and roadmap

- [ ] Active expiration (background sweep of keys with TTLs)
- [ ] AOF rewrite and compaction
- [ ] Lists, sets, and sorted sets
- [ ] Binary-safe values (values are currently decoded as UTF-8)
- [ ] `MULTI`/`EXEC` transactions and pub/sub
- [ ] Benchmarks against real Redis using `redis-benchmark`
