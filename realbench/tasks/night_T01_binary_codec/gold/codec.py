"""Reference: binary protocol codec."""
import struct
import zlib

_MAGIC = b"\xeb\x90"
_VERSION = b"\x01"


def encode_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("value must be non-negative")
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def decode_varint(data: bytes, pos: int = 0) -> tuple[int, int]:
    result = 0
    shift = 0
    start = pos
    for _ in range(10):
        if pos >= len(data):
            raise ValueError("truncated varint")
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            # canonical check: overlong encodings are malformed
            if byte == 0 and shift > 0:
                raise ValueError("non-canonical varint")
            return result, pos
        shift += 7
    raise ValueError("varint too long")


def zigzag(n: int) -> int:
    return (n << 1) ^ (n >> 63) if n >= 0 else ((-n) << 1) - 1


def encode_signed(value: int) -> bytes:
    return encode_varint(zigzag(value))


def decode_signed(data: bytes, pos: int = 0) -> tuple[int, int]:
    val, pos = decode_varint(data, pos)
    return ((val >> 1) ^ -(val & 1)), pos


def encode_message(msg: dict) -> bytes:
    msg_type = msg["type"]
    payload = msg["payload"]
    if not isinstance(msg_type, int) or not 0 <= msg_type <= 255:
        raise ValueError("type must be an int in 0..255")
    if not isinstance(payload, (bytes, bytearray)):
        raise ValueError("payload must be bytes")
    payload = bytes(payload)
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    return (_MAGIC + _VERSION + bytes([msg_type])
            + encode_varint(len(payload)) + payload
            + struct.pack("<I", crc))


def decode_message(data: bytes) -> dict:
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("data must be bytes")
    data = bytes(data)
    if len(data) < 3 or data[:2] != _MAGIC:
        raise ValueError("bad magic")
    if data[2:3] != _VERSION:
        raise ValueError("unsupported version")
    if len(data) < 4:
        raise ValueError("truncated header")
    pos = 3
    msg_type = data[pos]
    pos += 1
    length, pos = decode_varint(data, pos)
    payload_end = pos + length
    if payload_end > len(data) - 4:
        raise ValueError("truncated payload")
    payload = data[pos:payload_end]
    expected_crc = struct.unpack("<I", data[payload_end:payload_end + 4])[0]
    actual_crc = zlib.crc32(payload) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise ValueError("CRC mismatch")
    if payload_end + 4 != len(data):
        raise ValueError("trailing bytes after message")
    return {"type": msg_type, "payload": payload}
