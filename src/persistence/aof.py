# src/persistence/aof.py
import os

class AppendOnlyFile:
    def __init__(self, filepath="appendonly.aof"):
        self.filepath = filepath
        # Open file in append mode, creating it if it doesn't exist
        self.file = open(self.filepath, "a+", encoding="utf-8")

    def write(self, command: list):
        """Append a command array to the AOF file using RESP format."""
        # RESP Array encoding: *<number-of-elements>\r\n$<len>\r\n<element>\r\n...
        parts = [f"*{len(command)}"]
        for arg in command:
            arg_str = str(arg)
            parts.append(f"${len(arg_str)}")
            parts.append(arg_str)
        
        encoded_command = "\r\n".join(parts) + "\r\n"
        self.file.write(encoded_command)
        self.file.flush() # Ensure it writes directly to disk

    def load(self):
        """Read and yield commands line-by-line from the AOF file during server startup."""
        if not os.path.exists(self.filepath):
            return []

        commands = []
        with open(self.filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Simple parser for replaying command logs on startup
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("*"):
                num_elements = int(line[1:])
                cmd = []
                i += 1
                for _ in range(num_elements):
                    if i < len(lines) and lines[i].startswith("$"):
                        # Skip length descriptor line, next line is the actual argument
                        i += 1
                        if i < len(lines):
                            cmd.append(lines[i].strip())
                    i += 1
                if cmd:
                    commands.append(cmd)
            else:
                i += 1
                
        return commands

    def close(self):
        if self.file and not self.file.closed:
            self.file.close()