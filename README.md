# CESU-8 Modifier Decoder

Decode CESU-8 encoded bytes into Python strings.

```python
from cesu_8_modifier_decoder import decode_cesu8, Cesu8DecodeError

# U+1F600 encoded as the CESU-8 surrogate pair D83D DE00
data = bytes([0xED, 0xA0, 0xBD, 0xED, 0xB8, 0x80])
print(decode_cesu8(data))  # 😀

try:
    decode_cesu8(bytes([0xED, 0xA0, 0xBD]))  # lone high surrogate
except Cesu8DecodeError as e:
    print(e)
```

## Why

CESU-8 is a non-standard encoding used in some database systems (notably
Oracle) and legacy middleware. Supplementary characters (U+10000 and above)
are represented as two 3-byte sequences encoding a UTF-16 surrogate pair
rather than a single 4-byte sequence as in UTF-8. Python's built-in `bytes.decode("utf-8")`
refuses these sequences, so a dedicated decoder is needed to read data
that was produced under that convention.

This library is a strict CESU-8 decoder, not a tolerant one. It rejects
lone surrogates and any byte sequence that is not well-formed CESU-8.
If you need to recover text from potentially corrupt data, clean it first.

## Edge cases

- **Lone surrogates are rejected.** A high surrogate (U+D800–U+DBFF) must
  be followed by a low surrogate (U+DC00–U+FFF) in CESU-8. A low surrogate
  appearing first is always an error.
- **4-byte UTF-8 sequences are rejected.** Pure CESU-8 never uses them; a
  leading byte in the range 0xF0–0xFF is malformed.
- **Overlong encodings are rejected.** A 2-byte form encoding a value below
  U+0080 or a 3-byte form encoding a value below U+0800 raises `Cesu8DecodeError`.
- `Cesu8DecodeError` subclasses `ValueError`, so existing `except ValueError`
  blocks still catch it.
