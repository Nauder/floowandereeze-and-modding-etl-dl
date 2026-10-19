"""Read card names and their artwork IDs from Duel Links card tables."""

import struct
from typing import Dict

from .resource_service import decode_ydlz, load_resource


def get_card_names(game_path: str) -> Dict[str, str]:
    """Load the Steam client's English card tables from downloaded LocalData.

    LocalData filenames are CRC32 hashes of case-sensitive resource paths.
    The PC client inserts ``st_`` before resource filenames. The default
    (English) card tables do not have a locale directory.
    """
    tables = {}
    for name in ("CARD_Name", "CARD_Indx", "CARD_Prop3"):
        tables[name] = load_resource(game_path, f"Card/Data2/st_{name}")
    return parse_card_names(
        tables["CARD_Name"], tables["CARD_Indx"], tables["CARD_Prop3"]
    )


def decode_card_table(data: bytes) -> bytes:
    """Unpack a card table using the shared game-resource decoder."""
    return decode_ydlz(data)


def parse_card_names(names: bytes, indexes: bytes, properties: bytes) -> Dict[str, str]:
    """Join CARD_Name offsets to the Konami IDs stored in CARD_Prop3.

    Each property record is eight bytes, with the card ID in its low 16 bits.
    The corresponding CARD_Indx record contains two little-endian 32-bit
    offsets (name and description). Names are null-terminated UTF-8 strings;
    padding and empty records must not change the record alignment.
    """
    if not properties or len(properties) % 8 or len(indexes) != len(properties) + 8:
        raise ValueError("Card property and index tables have incompatible sizes")

    cards = {}
    for index, (card_id, _, _) in enumerate(struct.iter_unpack("<HHI", properties)):
        offset = struct.unpack_from("<I", indexes, index * 8)[0]
        if offset >= len(names):
            raise ValueError(f"Card {card_id} has an invalid name offset: {offset}")
        end = names.find(b"\0", offset)
        if end == -1:
            raise ValueError(f"Card {card_id} has an unterminated name")
        name = names[offset:end].decode("utf-8")
        if card_id and name:
            cards[str(card_id)] = name
    if not cards:
        raise ValueError("No card names found in game tables")
    return cards
