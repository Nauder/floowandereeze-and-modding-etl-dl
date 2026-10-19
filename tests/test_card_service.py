"""Regression tests for the game's binary card-name tables (unittest)."""

import struct
import sys
import json
import os
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "etl"))

from services.card_service import decode_card_table, get_card_names, parse_card_names
from services.data_service import DataService


class CardTableTests(unittest.TestCase):
    """Keep ID alignment, UTF-8 names, and invalid-table handling covered."""

    def setUp(self):
        self.names = b"\0" * 8 + "Blue-Eyes White Dragon\0\0Étoile Cyber\0".encode(
            "utf-8"
        )
        self.indexes = b"".join(
            struct.pack("<II", offset, 0) for offset in (4, 8, 32, len(self.names))
        )
        self.properties = b"".join(
            struct.pack("<HHI", card_id, 0x6040, 0x8021F52C)
            for card_id in (0, 4007, 6482)
        )

    def test_names_use_property_ids_and_byte_offsets(self):
        """Padding and multibyte text must not shift names onto another ID."""
        self.assertEqual(
            parse_card_names(self.names, self.indexes, self.properties),
            {"4007": "Blue-Eyes White Dragon", "6482": "Étoile Cyber"},
        )

    def test_unpack_ydlz(self):
        """Version 1 is a YDLZ header followed by a zlib stream."""
        packed = b"YDLZ" + struct.pack("<I", 1) + zlib.compress(self.names)
        self.assertEqual(decode_card_table(packed), self.names)

    def test_invalid_ydlz(self):
        """Reject unknown headers, versions, and damaged compressed data."""
        for packed in (b"", b"YDLZ\x03\0\0\0", b"YDLZ\x01\0\0\0invalid"):
            with self.subTest(packed=packed), self.assertRaises(ValueError):
                decode_card_table(packed)

    def test_version_two_word_stream_and_remainders(self):
        """Fixed v2 vectors exercise all four possible final word lengths."""
        vectors = (
            ("b8db0300aa4f0001", b""),
            ("c1d34b04a35762001d", b"a"),
            ("cacb4b4c9a5f01263f71", b"ab"),
            ("d3c34b4cdb610002b2add8", b"abc"),
        )
        for encoded, expected in vectors:
            with self.subTest(expected=expected):
                self.assertEqual(
                    decode_card_table(b"YDLZ\x02\0\0\0" + bytes.fromhex(encoded)),
                    expected,
                )

    def write_tables(self, root):
        """Use the actual Steam resource hashes with synthetic table contents."""
        for bundle, data in (
            ("e542a117", self.names),
            ("c10d0903", self.indexes),
            ("47a9aa15", self.properties),
        ):
            path = Path(root) / bundle[:2] / bundle
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"YDLZ\x01\0\0\0" + zlib.compress(data))

    def test_load_downloaded_tables(self):
        """Find the tables using resource hashes, with no hardcoded local path."""
        with tempfile.TemporaryDirectory() as root:
            self.write_tables(root)
            self.assertEqual(get_card_names(root)["4007"], "Blue-Eyes White Dragon")

    def test_missing_download(self):
        """An incomplete installation must explain how to get the missing data."""
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(FileNotFoundError, "in-game data download"):
                get_card_names(root)

    def test_offline_pipeline_keeps_art_variants_and_other_assets(self):
        """Exercise real file loading, duplicate names, and missing artwork IDs."""
        self.names = b"\0" * 8 + b"Shared name\0"
        self.indexes = b"".join(
            struct.pack("<II", offset, 0) for offset in (4, 8, 8, 8, len(self.names))
        )
        self.properties = b"".join(
            struct.pack("<Q", card_id) for card_id in (0, 4007, 6482, 3400)
        )
        artwork = {"small": "s", "medium": "m", "large": "l"}
        ids = {
            "card": {
                **{card_id: artwork for card_id in ("4007", "6482", "3400", "9999")},
                "1234": {"small": "s"},
            },
            "sleeve": {"sleeve": {"small": "s", "medium": "m"}},
            "playmat": {},
            "character": [{"konami_id": 1}],
        }
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as root:
            self.write_tables(root)
            temp = Path(root) / "etl/services/temp"
            temp.mkdir(parents=True)
            (temp / "ids.json").write_text(json.dumps(ids), encoding="utf-8")
            try:
                os.chdir(root)
                with (
                    patch("services.data_service.GAME_PATH", root),
                    patch(
                        "socket.socket.connect", side_effect=AssertionError("Network")
                    ),
                    self.assertLogs("DataService", level="WARNING") as logs,
                ):
                    DataService().get_card_data()
                output = json.loads((temp / "data.json").read_text(encoding="utf-8"))
                self.assertFalse((Path(root) / "database.db").exists())
            finally:
                os.chdir(original_cwd)
        self.assertEqual(
            list(output["card"]),
            ["Shared name", "Shared name (alt 1)", "Shared name (alt 2)"],
        )
        self.assertEqual(output["card"]["Shared name (alt 2)"]["id"], "3400")
        self.assertIn("9999", " ".join(logs.output))
        for category in ("sleeve", "playmat", "character"):
            expected = ids[category]
            for asset in expected.values() if isinstance(expected, dict) else expected:
                asset["name"] = None
            self.assertEqual(output[category], expected)

    def test_mismatched_tables(self):
        """Do not quietly pair tables from incompatible game versions."""
        with self.assertRaises(ValueError):
            parse_card_names(self.names, self.indexes[:-8], self.properties)

    def test_bad_offset(self):
        """Offsets outside the name blob are corrupt data."""
        indexes = struct.pack("<II", len(self.names), 0) + self.indexes[8:]
        with self.assertRaises(ValueError):
            parse_card_names(self.names, indexes, self.properties)

    def test_unterminated_name(self):
        """Require a terminator instead of silently returning truncated text."""
        with self.assertRaises(ValueError):
            parse_card_names(self.names[:-1], self.indexes, self.properties)


if __name__ == "__main__":
    unittest.main()
