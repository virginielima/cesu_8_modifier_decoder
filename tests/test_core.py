import unittest

from cesu_8_modifier_decoder import decode_cesu8, Cesu8DecodeError


class TestDecodeAscii(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(decode_cesu8(b""), "")

    def test_plain_ascii(self):
        self.assertEqual(decode_cesu8(b"hello"), "hello")

    def test_mixed_ascii(self):
        self.assertEqual(decode_cesu8(b"a\x00b"), "a\x00b")


class TestDecodeBmp(unittest.TestCase):
    def test_two_byte(self):
        self.assertEqual(decode_cesu8(b"\xc3\xa9"), "\u00e9")

    def test_three_byte_bmp(self):
        self.assertEqual(decode_cesu8(b"\xe4\xb8\xad"), "\u4e2d")

    def test_mixed_text(self):
        self.assertEqual(decode_cesu8(b"hi \xc3\xa9!"), "hi \u00e9!")


class TestDecodeSupplementary(unittest.TestCase):
    def test_smiley_face(self):
        # U+1F600 -> surrogate pair D83D DE00
        data = bytes([0xED, 0xA0, 0xBD, 0xED, 0xB8, 0x80])
        self.assertEqual(decode_cesu8(data), "\U0001f600")

    def test_supplementary_plane_char(self):
        # U+10400 DESERET CAPITAL LETTER LONG I -> D801 DC00
        data = bytes([0xED, 0xA0, 0x81, 0xED, 0xB0, 0x80])
        self.assertEqual(decode_cesu8(data), "\U00010400")

    def test_supplementary_with_context(self):
        # "a" + U+1F600 + "b"
        data = b"a" + bytes([0xED, 0xA0, 0xBD, 0xED, 0xB8, 0x80]) + b"b"
        self.assertEqual(decode_cesu8(data), "a\U0001f600b")

    def test_two_supplementary_in_sequence(self):
        data = (
            bytes([0xED, 0xA0, 0xBD, 0xED, 0xB8, 0x80])
            + bytes([0xED, 0xA0, 0x81, 0xED, 0xB0, 0x80])
        )
        self.assertEqual(decode_cesu8(data), "\U0001f600\U00010400")

    def test_max_valid_code_point(self):
        # U+10FFFF -> surrogate pair DBFF DFFF
        data = bytes([0xED, 0xAF, 0xBF, 0xED, 0xBF, 0xBF])
        self.assertEqual(decode_cesu8(data), "\U0010ffff")


class TestDecodeErrors(unittest.TestCase):
    def test_lone_high_surrogate_at_end(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(bytes([0xED, 0xA0, 0xBD]))

    def test_lone_high_surrogate_followed_by_non_surrogate(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(bytes([0xED, 0xA0, 0xBD, 0x41]))

    def test_lone_low_surrogate(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(bytes([0xED, 0xB8, 0x80]))

    def test_lone_low_surrogate_after_regular_char(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(b"a" + bytes([0xED, 0xB8, 0x80]))

    def test_four_byte_sequence_rejected(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(b"\xf0\x9f\x98\x80")

    def test_truncated_two_byte(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(b"\xc3")

    def test_truncated_three_byte(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(b"\xe4\xb8")

    def test_truncated_surrogate_pair(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(bytes([0xED, 0xA0, 0xBD, 0xED, 0xB8]))

    def test_overlong_two_byte(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(b"\xc0\x80")

    def test_overlong_three_byte(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(b"\xe0\x80\x80")

    def test_unexpected_continuation_byte(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(b"\x80")

    def test_bad_continuation_byte(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(b"\xc3\x00")

    def test_bad_continuation_in_surrogate(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(bytes([0xED, 0xA0, 0x00]))

    def test_invalid_leading_byte(self):
        with self.assertRaises(Cesu8DecodeError):
            decode_cesu8(b"\xff")


class TestTypeError(unittest.TestCase):
    def test_str_rejected(self):
        with self.assertRaises(TypeError):
            decode_cesu8("hello")  # type: ignore[arg-type]


class TestBytearray(unittest.TestCase):
    def test_bytearray_input(self):
        self.assertEqual(decode_cesu8(bytearray(b"\xc3\xa9")), "\u00e9")


class TestCesu8DecodeErrorIsValueError(unittest.TestCase):
    def test_subclass(self):
        self.assertTrue(issubclass(Cesu8DecodeError, ValueError))


if __name__ == "__main__":
    unittest.main()
