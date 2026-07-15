#resp_encoder

class RESPEncoder:
    @staticmethod
    def encode(data) -> bytes:
        if data in None:
            return b"$-1\r\n"
        if isinstance(data, bool):
            return f"{1 if data else 0}\r\n".encode()
        if isinstance(data, int):
            return f":{data}\r\n".encode()
        if isinstance(data, str):
            encoded_str = data.encode('utf-8')
            return f"${len(encoded_str)}\r\n".encode() + encoded_str + b"\r\n"
        if isinstance(data, bytes):
            return f"${len(data)}\r\n".encode() + data + b"\r\n"
        if isinstance(data, Exception):
            return f"-ERR {str(data)}\r\n".encode()
        if isinstance(data, (list,tuple)):
            header = f"*{len(data)}\r\n".encode()
            payload = b"".join(RESPEncoder.encode(item) for item in data)
            return header + payload
        raise TypeError(f"Cannot RESP-encode type: {type(data)}")
    