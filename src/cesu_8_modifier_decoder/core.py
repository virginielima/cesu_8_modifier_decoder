from typing import List


class Cesu8DecodeError(ValueError):
    """Raised when a byte sequence is not valid CESU-8.

    Subclasses ValueError so existing code that catches ValueError for
    malformed UTF-8-like input keeps working.
    """


def _decode_one(seq: bytes, i: int, length: int) -> "tuple[int, int]":
    """Decode a single CESU-8 code unit starting at index ``i``.

    Returns (code_unit, next_index). A "code unit" here is either a
    decoded Unicode code point (for 1/2/3-byte sequences) or a raw
    surrogate value in the range U+D800..U+DFFF (for the 3-byte encoded
    surrogate form used by CESU-8).
    """
    if i >= length:
        raise Cesu8DecodeError("unexpected end of input")

    b0 = seq[i]

    if b0 < 0x80:
        return b0, i + 1

    if b0 < 0xC0:
        raise Cesu8DecodeError(
            f"unexpected continuation byte 0x{b0:02x} at index {i}"
        )

    if b0 < 0xE0:
        if i + 1 >= length:
            raise Cesu8DecodeError("truncated 2-byte sequence")
        b1 = seq[i + 1]
        if (b1 & 0xC0) != 0x80:
            raise Cesu8DecodeError(f"bad second byte 0x{b1:02x} at index {i + 1}")
        cp = ((b0 & 0x1F) << 6) | (b1 & 0x3F)
        if cp < 0x80:
            raise Cesu8DecodeError(f"overlong 2-byte encoding at index {i}")
        return cp, i + 2

    if b0 < 0xF0:
        if i + 2 >= length:
            raise Cesu8DecodeError("truncated 3-byte sequence")
        b1 = seq[i + 1]
        b2 = seq[i + 2]
        if (b1 & 0xC0) != 0x80:
            raise Cesu8DecodeError(f"bad second byte 0x{b1:02x} at index {i + 1}")
        if (b2 & 0xC0) != 0x80:
            raise Cesu8DecodeError(f"bad third byte 0x{b2:02x} at index {i + 2}")
        cp = ((b0 & 0x0F) << 12) | ((b1 & 0x3F) << 6) | (b2 & 0x3F)
        if cp < 0x800:
            raise Cesu8DecodeError(f"overlong 3-byte encoding at index {i}")
        return cp, i + 3

    raise Cesu8DecodeError(
        f"invalid leading byte 0x{b0:02x} at index {i}; "
        "CESU-8 has no 4-byte sequences"
    )


def decode_cesu8(data: bytes) -> str:
    """Decode CESU-8 encoded bytes into a Python ``str``.

    CESU-8 encodes supplementary characters (U+10000..U+10FFFF) as a
    pair of 3-byte UTF-8-style sequences, each representing one half of
    a UTF-16 surrogate pair. This decoder reconstructs the original
    code point from such pairs.

    Single BMP characters (including lone surrogates) use standard
    1/2/3-byte UTF-8 forms.

    Raises :class:`Cesu8DecodeError` on malformed input.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("decode_cesu8 requires bytes or bytearray")

    seq = bytes(data)
    length = len(seq)
    chars: List[str] = []
    i = 0

    while i < length:
        cp, j = _decode_one(seq, i, length)

        if 0xD800 <= cp <= 0xDBFF:
            # High surrogate. A low surrogate must follow, otherwise this
            # is a lone surrogate which CESU-8 forbids.
            if j >= length:
                raise Cesu8DecodeError(
                    f"lone high surrogate at end of input (index {i})"
                )
            cp2, k = _decode_one(seq, j, length)
            if not (0xDC00 <= cp2 <= 0xDFFF):
                raise Cesu8DecodeError(
                    f"high surrogate at index {i} not followed by "
                    f"a low surrogate"
                )
            full = 0x10000 + ((cp - 0xD800) << 10) + (cp2 - 0xDC00)
            chars.append(chr(full))
            i = k
        elif 0xDC00 <= cp <= 0xDFFF:
            raise Cesu8DecodeError(
                f"lone low surrogate 0x{cp:04x} at index {i}"
            )
        else:
            chars.append(chr(cp))
            i = j

    return "".join(chars)
