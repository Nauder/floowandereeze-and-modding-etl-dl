"""Read the Steam client's hashed resources and decode YDLZ payloads."""

import struct
import zlib
from pathlib import Path


def load_resource(game_path: str, resource: str) -> bytes:
    """Read a case-sensitive resource path from the downloaded LocalData folder."""
    bundle = f"{zlib.crc32(resource.encode('utf-8')):08x}"
    path = Path(game_path) / bundle[:2] / bundle
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing game resource {resource}: {path}. "
            "Check game_path and complete the in-game data download."
        )
    try:
        return decode_ydlz(path.read_bytes())
    except ValueError as error:
        raise ValueError(f"Could not decode {resource} from {path}: {error}") from error


def unscramble(data: bytes) -> bytes:
    """Apply the game's symmetric, length-seeded 32-bit XOR word stream."""
    payload = bytearray(data)
    previous, current = ~len(payload) & 0xFFFFFFFF, len(payload)
    for offset in range(0, len(payload), 4):
        mixed = (previous ^ (previous << 11)) & 0xFFFFFFFF
        previous = current
        current = (current ^ (((current >> 5) ^ mixed) >> 8) ^ mixed) & 0xFFFFFFFF
        word = ((previous + current) & 0xFFFFFFFF).to_bytes(4, "little")
        for index in range(min(4, len(payload) - offset)):
            payload[offset + index] ^= word[index]
    return bytes(payload)


def decode_ydlz(data: bytes) -> bytes:
    """Unpack YDLZ v1/v2 resources without changing the game files."""
    if len(data) < 8 or data[:4] != b"YDLZ":
        raise ValueError("Resource is missing its YDLZ header")
    version = struct.unpack_from("<I", data, 4)[0]
    if version not in (1, 2):
        raise ValueError(f"Unsupported YDLZ resource version: {version}")
    payload = unscramble(data[8:]) if version == 2 else data[8:]
    try:
        return zlib.decompress(payload)
    except zlib.error as error:
        raise ValueError("Invalid compressed resource") from error
