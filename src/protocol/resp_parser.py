class RESPParser:
    def __init__(self):
        self._buffer = bytearray()

    def feed(self, data: bytes):
        self._buffer.extend(data)
    
    def parse(self):
        if not self._buffer:
            return None, False
        
        line_end = self._buffer.find(b"\r\n")
        if line_end == -1:
            return None, False
        
        first_byte = chr(self._buffer[0])
        line = self._buffer[1:line_end]

        if first_byte == "+":
            parsed_val = line.decode('utf-8')
            del self._buffer[:line_end+2]
            return parsed_val, True
        
        elif first_byte == "-":
            parsed_val = Exception(line.decode('utf-8'))
            del self._buffer[:line_end+2]
            return parsed_val, True
        
        elif first_byte == ":":
            try:
                parsed_val = int(line)
            except ValueError:
                raise ValueError("Protocol error: invalid integer format")
            del self._buffer[:line_end+2]
            return parsed_val, True
        
        elif first_byte == "$":
            try:
                length = int(line)
            except ValueError:
                raise ValueError("Protocol error: invalid bulk string length")
            
            if length == "-1":
                del self._buffer[:line_end+2]
                return None, True
            
            start_index = line_end+2
            end_index = start_index + length

            if len(self._buffer) < end_index + 2:
                return None, False
            
            if self._buffer[end_index:end_index+2] != b"\r\n":
                raise ValueError("Protocol error: missing bulk string terminator")
            
            payload = self._buffer[start_index:end_index].decode('utf-8')
            del self._buffer[:end_index+2]
            return payload, True

        elif first_byte == "*":
            try: 
                num_elements = int(line)
            except ValueError:
                raise ValueError("Protocol error: invalid array length")
            
            if num_elements == -1:
                del self._buffer[:line_end+2]
                return None, True

            origianal_buffer = bytearray(self._buffer)
            del self._buffer[:line_end+2]

            elements = []
            for _ in range(num_elements):
                element, success = self.parse()
                if not success:
                    self._buffer = origianal_buffer
                    return None, False
                elements.append(element)

            return elements, True
        
        else:
            raise ValueError(f"Protocol error: unexpected initial byte '{first_byte}'")