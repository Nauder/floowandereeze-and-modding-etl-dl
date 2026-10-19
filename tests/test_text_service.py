"""Regression tests for local display names and optional Parquet name columns."""

import json
import os
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

import msgpack
from pandas import read_parquet

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "etl"))

from services.data_service import DataService
from services.text_service import TextService, parse_text_group


def write_group(root, group, data):
    """Write a synthetic text group using the actual game resource hashing."""
    resource = f"Texts/st_IDS_{group}"
    bundle = f"{zlib.crc32(resource.encode()):08x}"
    path = Path(root) / bundle[:2] / bundle
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"YDLZ\x01\0\0\0" + zlib.compress(msgpack.packb(data)))


class TextGroupTests(unittest.TestCase):
    """Cover both text-table encodings and references used by accessory labels."""

    def test_plain_group_excludes_metadata(self):
        data = {"_GRP_": "NPC_NAME", "_LNG_": "en-US", "ID0001": "Étoile"}
        self.assertEqual(parse_text_group(msgpack.packb(data)), {"ID0001": "Étoile"})

    def test_scrambled_keys_and_values(self):
        """Fixed vectors prevent a symmetric round trip from hiding decoder bugs."""
        data = {"_SCRKEY_": True, "_SCR_": True, "h3MwMPcO": "4R9hbf8D\nZSDxxVJm"}
        self.assertEqual(
            parse_text_group(msgpack.packb(data)), {"ID0001": "Example Name"}
        )

    def test_independent_scrambling_flags(self):
        for data in (
            {"_SCRKEY_": True, "h3MwMPcO": "Étoile"},
            {"_SCR_": True, "ID0001": "BLZ0b9crZQ=="},
        ):
            with self.subTest(data=data):
                self.assertEqual(
                    parse_text_group(msgpack.packb(data)), {"ID0001": "Étoile"}
                )

    def test_invalid_tables_fail(self):
        for data in (
            b"\xc1",
            msgpack.packb([]),
            msgpack.packb({"_SCR_": True, "ID0001": "!"}),
        ):
            with self.subTest(data=data), self.assertRaises(
                (ValueError, msgpack.UnpackException)
            ):
                parse_text_group(data)

    def test_resolve_character_subname_and_skill(self):
        with tempfile.TemporaryDirectory() as root:
            write_group(
                root,
                "NPC_NAME",
                {"ID0001": "Yami Yugi", "SUB_ID0001": "Yami Yugi (DM)"},
            )
            write_group(root, "SKILL", {"NAME994": "Example Skill"})
            write_group(
                root,
                "ITEM",
                {
                    "ID4001": 'Sleeves: <chara get="subname" id="1"/>',
                    "ID25000014": "Mat: <chara id='001' get='name' /> &amp; <skill id='994' type='name'/>",
                },
            )
            names = TextService(root)
            self.assertEqual(names.character_name(1), "Yami Yugi")
            self.assertEqual(names.item_name("4001"), "Sleeves: Yami Yugi (DM)")
            self.assertEqual(
                names.item_name("25000014"), "Mat: Yami Yugi & Example Skill"
            )

    def test_unknown_and_cyclic_references_are_unavailable(self):
        with tempfile.TemporaryDirectory() as root:
            names = TextService(root)
            names.groups = {
                "NPC_NAME": {"ID0001": "<chara id='1' get='name'/>", "ID0000": " "},
                "ITEM": {
                    "ID4001": "Sleeves: <chara id='2' get='name'/>",
                    "ID4002": "<unknown/>",
                },
            }
            for value in (
                names.character_name(1),
                names.character_name(0),
                names.item_name("4001"),
                names.item_name("4002"),
                names.item_name("missing"),
            ):
                self.assertIsNone(value)

    def test_missing_group_is_optional_and_cached(self):
        with tempfile.TemporaryDirectory() as root:
            names = TextService(root)
            with self.assertLogs("services.text_service", level="WARNING") as logs:
                self.assertIsNone(names.character_name(1))
                self.assertIsNone(names.character_name(2))
            self.assertEqual(len(logs.output), 1)

    def test_names_survive_parquet_export_without_dropping_assets(self):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as root:
            write_group(root, "NPC_NAME", {"ID0001": "Named Character"})
            write_group(
                root,
                "ITEM",
                {
                    "ID4001": "Same sleeve",
                    "ID4002": "Same sleeve",
                    "ID5001": "Named Mat",
                },
            )
            artwork = {"small": "s", "medium": "m"}
            data = {
                "card": {},
                "sleeve": {key: dict(artwork) for key in ("4001", "4002", "4999")},
                "playmat": {key: dict(artwork) for key in ("5001", "5999")},
                "character": [
                    {"konami_id": 1, "icon": "icon"},
                    {"konami_id": 2, "icon": "other"},
                ],
            }
            temp = Path(root) / "etl/services/temp"
            temp.mkdir(parents=True)
            (Path(root) / "data").mkdir()
            try:
                os.chdir(root)
                with patch("services.data_service.GAME_PATH", root), patch(
                    "socket.socket.connect", side_effect=AssertionError("Network")
                ):
                    service = DataService()
                    service._add_asset_names(data)
                    (temp / "data.json").write_text(json.dumps(data), encoding="utf-8")
                    service.write_data()
                for file, count, named in (
                    ("sleeves", 3, 2),
                    ("fields", 2, 1),
                    ("characters", 2, 1),
                ):
                    frame = read_parquet(Path(root) / f"data/{file}.parquet")
                    self.assertEqual(len(frame), count)
                    self.assertEqual(frame["name"].notna().sum(), named)
                    self.assertEqual(frame["name"].dtype.name, "string")
                self.assertEqual(data["character"][0]["icon"], "icon")
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
