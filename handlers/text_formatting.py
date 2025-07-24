class StringProcessor:
    def trunc64(self, s: str) -> str:
        # Build a new string that when encoded is less than 64 bytes.
        result_bytes = bytearray()
        for char in s:
            char_bytes = char.encode("utf-8")
            if len(result_bytes) + len(char_bytes) < 64:
                result_bytes.extend(char_bytes)
            else:
                break
        return result_bytes.decode("utf-8", errors="ignore")