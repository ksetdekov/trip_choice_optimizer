import unittest
from handlers.text_formatting import StringProcessor

class TestStringProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = StringProcessor()
    
    def test_empty_string(self):
        # An empty string should return empty.
        result = self.processor.trunc64("")
        self.assertEqual(result, "")
    
    def test_small_ascii_string(self):
        # A short ASCII string that doesn't hit the byte limit should be unchanged.
        s = "Hello, world!"
        result = self.processor.trunc64(s)
        self.assertEqual(result, s)
    
    def test_ascii_truncation(self):
        # For an ASCII string, each character is one byte.
        # If the input string contains 64 "a"s, the function should only keep 63 "a"s.
        s = "a" * 64
        expected = "a" * 63
        result = self.processor.trunc64(s)
        # Verify that the encoded result is less than 64 bytes.
        self.assertLess(len(result.encode("utf-8")), 64)
        self.assertEqual(result, expected)
    
    def test_multibyte_truncation(self):
        # Using a 2-byte character like "é"
        # Each "é" takes two bytes, so we expect that only as many characters can be added before exceeding 63 bytes.
        s = "é" * 40  # 40 * 2 bytes = 80 bytes if completely added.
        result = self.processor.trunc64(s)
        # Ensure that the total byte length is less than 64.
        self.assertLess(len(result.encode("utf-8")), 64)
        # Additionally, ensure that the returned string is a prefix of the original string.
        self.assertTrue(s.startswith(result))
    
    def test_emoji_truncation(self):
        # Emoji like "😀" are 4 bytes in utf-8.
        s = "😀" * 20  # 20 * 4 = 80 bytes if untruncated.
        result = self.processor.trunc64(s)
        self.assertLess(len(result.encode("utf-8")), 64)
        # Returned string should be a prefix of the original string.
        self.assertTrue(s.startswith(result))
    
    def test_mixed_characters(self):
        # A mix of ASCII and multibyte characters.
        s = "Hello, 😀 world! é" * 5
        result = self.processor.trunc64(s)
        self.assertLess(len(result.encode("utf-8")), 64)
        self.assertTrue(s.startswith(result))

if __name__ == "__main__":
    unittest.main()