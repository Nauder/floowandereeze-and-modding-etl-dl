"""Regression coverage for numbered character asset filenames."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "etl"))

from services.character_service import (
    CharaAssetType,
    is_character_asset,
    match_asset_by_string,
)
from services.game_service import GameService
from util import get_data_wrapper


class CharacterAssetTests(unittest.TestCase):
    """Exercise detection, exact matching, and the extracted character record."""

    def test_all_supported_assets_reach_their_own_column(self):
        service = GameService()
        ids = get_data_wrapper()
        for index, asset_type in enumerate(CharaAssetType):
            key = (
                "assets/resources/characters/sn0001/images/en-us/"
                f"{asset_type.value.lower()}.png"
            )
            bundle = f"{index:08x}"
            with self.subTest(asset_type=asset_type):
                self.assertTrue(is_character_asset(key))
                self.assertEqual(match_asset_by_string(key), asset_type)
                service._parse_character_asset(ids, bundle, key)

        self.assertEqual(len(ids["character"]), 1)
        character = ids["character"][0]
        self.assertEqual(character.konami_id, 1)
        for index, asset_type in enumerate(CharaAssetType):
            self.assertEqual(character.get_asset_by_enum(asset_type), f"{index:08x}")

    def test_case_insensitive_filenames(self):
        key = "assets/resources/characters/sn0001/Chara003_10.PNG"
        self.assertTrue(is_character_asset(key))
        self.assertEqual(match_asset_by_string(key), CharaAssetType.DUEL_10)

    def test_unrelated_or_unsupported_names_do_not_match_prefixes(self):
        for name in (
            "otherchara003_1.png",
            "chara003_100.png",
            "chara007_100.png",
            "chara003_1.png.meta",
            "chara004_10.png",
            "chara001_backup.png",
        ):
            with self.subTest(name=name):
                self.assertIsNone(match_asset_by_string(name))
        self.assertFalse(is_character_asset("otherchara003_1.png"))
        self.assertFalse(is_character_asset("chara003_1.png.meta"))


if __name__ == "__main__":
    unittest.main()
