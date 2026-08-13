"""Hidden tests: binary codec — GOLDEN BYTES, bit-exact, no tolerance."""
import struct
import zlib

import pytest

from codec import (decode_message, decode_signed, decode_varint,
                   encode_message, encode_signed, encode_varint)


# ── unsigned varint: golden vectors ─────────────────────────────────────────
def test_varint_golden():
    assert encode_varint(0) == b"\x00"
    assert encode_varint(1) == b"\x01"
    assert encode_varint(127) == b"\x7f"
    assert encode_varint(128) == b"\x80\x01"
    assert encode_varint(300) == b"\xac\x02"
    assert encode_varint(16383) == b"\xff\x7f"
    assert encode_varint(16384) == b"\x80\x80\x01"
    assert encode_varint(2**32 - 1) == b"\xff\xff\xff\xff\x0f"
    assert encode_varint(2**64 - 1) == b"\xff" * 9 + b"\x01"


def test_varint_negative_raises():
    with pytest.raises(ValueError):
        encode_varint(-1)


def test_varint_roundtrip():
    for v in [0, 1, 127, 128, 255, 300, 10000, 2**32, 2**63]:
        data = encode_varint(v)
        val, pos = decode_varint(data)
        assert val == v and pos == len(data)


def test_varint_malformed():
    with pytest.raises(ValueError):
        decode_varint(b"\x80")            # truncated
    with pytest.raises(ValueError):
        decode_varint(b"\x80\x80")        # truncated
    with pytest.raises(ValueError):
        decode_varint(b"\x80" * 11)       # too long
    with pytest.raises(ValueError):
        decode_varint(b"\x80\x00")        # non-canonical overlong
    with pytest.raises(ValueError):
        decode_varint(b"")                # empty


def test_varint_pos_offset():
    data = b"\x99" + encode_varint(300) + b"\x99"
    val, pos = decode_varint(data, pos=1)
    assert val == 300 and pos == 3


# ── zigzag signed varint ────────────────────────────────────────────────────
def test_zigzag_golden():
    assert encode_signed(0) == b"\x00"
    assert encode_signed(-1) == b"\x01"
    assert encode_signed(1) == b"\x02"
    assert encode_signed(-2) == b"\x03"
    assert encode_signed(2) == b"\x04"
    assert encode_signed(63) == b"\x7e"
    assert encode_signed(-64) == b"\x7f"
    assert encode_signed(64) == b"\x80\x01"
    assert encode_signed(-65) == b"\x81\x01"


def test_zigzag_roundtrip():
    for v in [0, 1, -1, 2, -2, 100, -100, 2**40, -(2**40), 2**63 - 1]:
        val, pos = decode_signed(encode_signed(v))
        assert val == v and pos == len(encode_signed(v))


# ── message framing: golden bytes ───────────────────────────────────────────
def _ref_varint(n: int) -> bytes:
    """Independent reference varint — NOT the solver's implementation."""
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _expected_message(msg_type, payload):
    return (b"\xeb\x90\x01" + bytes([msg_type])
            + _ref_varint(len(payload)) + payload
            + struct.pack("<I", zlib.crc32(payload) & 0xFFFFFFFF))


def test_message_golden_bytes():
    cases = [
        (7, b"hello"),
        (0, b""),
        (255, b"\x00\x01\x02"),
        (1, b"x" * 300),          # length needs multi-byte varint
    ]
    for msg_type, payload in cases:
        assert encode_message({"type": msg_type, "payload": payload}) \
            == _expected_message(msg_type, payload), (msg_type, len(payload))


def test_message_roundtrip():
    for msg_type in [0, 1, 128, 255]:
        for payload in [b"", b"a", b"hello world", bytes(range(256)),
                        b"x" * 1000]:
            data = encode_message({"type": msg_type, "payload": payload})
            assert decode_message(data) == {"type": msg_type,
                                            "payload": payload}


def test_message_wrong_magic():
    data = _expected_message(1, b"abc")
    bad = b"\xeb\x91" + data[2:]
    with pytest.raises(ValueError) as e:
        decode_message(bad)
    assert "magic" in str(e.value).lower()


def test_message_wrong_version():
    data = _expected_message(1, b"abc")
    bad = data[:2] + b"\x02" + data[3:]
    with pytest.raises(ValueError) as e:
        decode_message(bad)
    assert "version" in str(e.value).lower()


def test_message_truncated():
    data = _expected_message(1, b"abcdef")
    for cut in range(1, len(data)):
        with pytest.raises(ValueError):
            decode_message(data[:cut])


def test_message_crc_mismatch():
    data = _expected_message(1, b"abcdef")
    bad = bytearray(data)
    bad[-1] ^= 0xFF
    with pytest.raises(ValueError) as e:
        decode_message(bytes(bad))
    assert "crc" in str(e.value).lower() or "checksum" in str(e.value).lower()


def test_message_payload_corruption_detected():
    data = _expected_message(1, b"abcdef")
    bad = bytearray(data)
    bad[7] ^= 0x01  # flip a payload bit
    with pytest.raises(ValueError):
        decode_message(bytes(bad))


def test_message_length_mismatch():
    data = _expected_message(1, b"abc")
    bad = data[:4] + encode_varint(2) + data[5:]  # lie about length
    with pytest.raises(ValueError):
        decode_message(bad)


def test_message_trailing_bytes_rejected():
    data = _expected_message(1, b"abc") + b"\x00"
    with pytest.raises(ValueError):
        decode_message(data)


def test_message_type_out_of_range():
    with pytest.raises(ValueError):
        encode_message({"type": 256, "payload": b"x"})
    with pytest.raises(ValueError):
        encode_message({"type": -1, "payload": b"x"})
