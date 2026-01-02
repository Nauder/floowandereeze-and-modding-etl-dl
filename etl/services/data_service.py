"""Service for handling data processing and management."""

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Union
from datetime import datetime

from pandas import DataFrame, Series

from database.models import CardModel
from database.objects import session
from .character_service import CharacterAssets
from util import (
    GAME_PATH,
    get_data_wrapper,
    chunkify,
    NUM_THREADS,
    STREAMING_PATH,
    merge_nested_dicts,
)

from .game_service import GameService
from .ygopro_service import YGOProService


class DataService:
    """Service class for handling data operations."""

    def __init__(self) -> None:
        """Initialize the DataService with a GameService instance."""
        self.game_service = GameService()
        self.logger = logging.getLogger("DataService")
        self.processed = 0

    def get_ids(self) -> None:
        """Extract and process game IDs from asset bundles."""
        ids = get_data_wrapper()

        self.logger.info("Getting AssetBundles data...")

        all_dirs = [
            [data_dir, is_streaming]
            for is_streaming, path in [(False, GAME_PATH), (True, STREAMING_PATH)]
            for _, dirs, _ in os.walk(path)
            for data_dir in dirs
        ]

        dir_chunks = chunkify(all_dirs, NUM_THREADS)

        with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            results = list(executor.map(self.process_dirs, dir_chunks))

        for result in results:
            print(f"characters: {len(result['character'])}")
            self.merge_data(ids, result)

        # Convert CharacterAssets objects to dictionaries for JSON serialization
        ids["character"] = [
            char.to_dict() if hasattr(char, "to_dict") else char
            for char in ids["character"]
        ]

        with open("./etl/services/temp/ids.json", "w", encoding="utf-8") as outfile:
            json.dump(ids, outfile)

    def process_dirs(
        self, dir_list: List[List[Union[str, bool]]]
    ) -> Dict[str, Union[Dict[str, Any], List[Any]]]:
        """Process a list of directories to extract game data.

        Args:
            dir_list: List of [directory_name, is_streaming] pairs.

        Returns:
            Dictionary containing extracted data.
        """
        local_ids = get_data_wrapper()
        for data_dir, is_streaming in dir_list:
            if data_dir != "root":
                dir_ids = self.game_service.get_dir_data(data_dir, is_streaming)
                self.merge_data(local_ids, dir_ids)
                self.processed += 1

        return local_ids

    def merge_data(self, ids: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Merge extracted data into the main data structure.

        Args:
            ids: Main data structure to merge into.
            result: Data to merge.
        """
        ids["card"] = merge_nested_dicts(ids["card"], result["card"])
        ids["sleeve"] = merge_nested_dicts(ids["sleeve"], result["sleeve"])
        ids["playmat"] = merge_nested_dicts(ids["playmat"], result["playmat"])

        # Merge characters by konami_id to avoid duplicates
        self._merge_characters(ids["character"], result["character"])

    def _merge_characters(
        self, main_characters: List[Any], new_characters: List[Any]
    ) -> None:
        """Merge character lists, combining assets for characters with the same konami_id.

        Args:
            main_characters: Main list of characters to merge into.
            new_characters: New characters to merge.
        """
        for new_char in new_characters:
            # Find existing character with same konami_id
            existing_char = None
            for char in main_characters:
                if (
                    hasattr(char, "konami_id")
                    and hasattr(new_char, "konami_id")
                    and char.konami_id == new_char.konami_id
                ):
                    existing_char = char
                    break

            if existing_char:
                # Merge assets from new_char into existing_char
                self._merge_character_assets(existing_char, new_char)
            else:
                # Add new character
                main_characters.append(new_char)

    def _merge_character_assets(self, existing_char: Any, new_char: Any) -> None:
        """Merge assets from new_char into existing_char.

        Args:
            existing_char: Existing character to merge into.
            new_char: New character with assets to merge.
        """
        if hasattr(CharacterAssets, "_ENUM_TO_ATTR"):
            # Merge all asset attributes
            for attr_name in CharacterAssets._ENUM_TO_ATTR.values():
                new_value = getattr(new_char, attr_name, None)
                if new_value is not None:
                    # Only set if existing character doesn't have this asset
                    existing_value = getattr(existing_char, attr_name, None)
                    if existing_value is None:
                        setattr(existing_char, attr_name, new_value)

        # Also ensure series is set if missing
        if hasattr(new_char, "series") and not hasattr(existing_char, "series"):
            existing_char.series = new_char.series

    def add_suffix(self, names: List[str]) -> List[str]:
        """Add suffixes to duplicate names.

        Args:
            names: List of names to process.

        Returns:
            List of names with suffixes added for duplicates.
        """
        # Reverse the list to process from last to first
        reversed_names = list(reversed(names))
        name_counts: Dict[str, int] = {}
        updated_names = []

        for name in reversed_names:
            # Increment the count for this name
            if name in name_counts:
                name_counts[name] += 1
                updated_names.append(f"{name} (alt {name_counts[name] - 1})")
            else:
                name_counts[name] = 1
                updated_names.append(name)

        # Reverse the list back to the original order
        return list(reversed(updated_names))

    def remove_extra_suffix(self, cards: Dict[str, Any]) -> Dict[str, Any]:
        """Remove extra suffixes from card names.

        Args:
            cards: Dictionary of card data.

        Returns:
            Dictionary with cleaned card names.
        """
        # Create a new dictionary to store the updated keys
        updated_dict: Dict[str, Any] = {}

        # Iterate through the original dictionary
        for key, value in cards.items():
            # Check if the key contains '(alt 1)'
            if "(alt 1)" in key:
                # Remove '(alt 1)' from the key
                new_key = key.replace(" (alt 1)", "")

                # Check if the new key already exists in the updated dictionary
                if new_key not in cards:
                    # If it doesn't exist, add the new key with the original value
                    updated_dict[new_key] = value
                else:
                    # If it does exist, keep the original key and value
                    updated_dict[key] = value
            else:
                updated_dict[key] = value

        return updated_dict

    def get_card_data(self) -> None:
        """Extract and process card data from JSON files."""

        out_wrapper = get_data_wrapper()
        ygopro_service = YGOProService()

        data_response = ygopro_service.get_card_data()

        if not data_response[0]:
            raise Exception(f"Failed to get card data from YGOPRO: {data_response[1]}")

        self.logger.info(
            "YGOPro API call successful [%s], processing card data...", data_response[1]
        )

        with open("./etl/services/temp/ids.json", "r", encoding="utf-8") as ids_json:
            ids = json.load(ids_json)

            for card, data in ids["card"].items():
                if {"small", "medium", "large"}.issubset(set(data.keys())):

                    self.logger.info("Processing %s", card)
                    pro_card = (
                        session.query(CardModel)
                        .filter(CardModel.konami_id == card)
                        .first()
                    )

                    if not pro_card:
                        continue

                    name = pro_card.name

                    if name:
                        alt_count = 1

                        # Name duplication means this can't be parallelized :/
                        while name in out_wrapper["card"]:
                            name = name + f" (alt {alt_count})"
                            alt_count += 1

                        out_wrapper["card"][name] = {
                            "small": data["small"],
                            "medium": data["medium"],
                            "large": data["large"],
                            "id": card,
                        }

                        self.logger.info("Processed %s", name)

        out_wrapper["playmat"] = ids["playmat"]
        out_wrapper["sleeve"] = ids["sleeve"]
        out_wrapper["character"] = ids["character"]

        with open("./etl/services/temp/data.json", "w", encoding="utf-8") as outfile:
            json.dump(out_wrapper, outfile)

    def write_data(self) -> None:
        """Write processed data to Parquet files and update version information."""
        with open("./etl/services/temp/data.json", "r", encoding="utf-8") as data_file:
            data = json.load(data_file)

            self.logger.info("Writing Sleeves...")
            # Filter sleeves with required keys
            valid_sleeves = {
                k: v
                for k, v in data["sleeve"].items()
                if isinstance(v, dict) and all(key in v for key in ["small", "medium"])
            }

            if valid_sleeves:
                sleeves = DataFrame()
                sleeves.insert(0, "konami_id", valid_sleeves.keys())
                sleeves.insert(
                    0,
                    "small",
                    Series([sleeve["small"] for sleeve in valid_sleeves.values()]),
                )
                sleeves.insert(
                    0,
                    "medium",
                    Series([sleeve["medium"] for sleeve in valid_sleeves.values()]),
                )
                sleeves.to_parquet("./data/sleeves.parquet")
                self.logger.info("Wrote %d sleeves", len(valid_sleeves))
            else:
                self.logger.warning("No valid sleeves found to write")

            self.logger.info("Writing Cards...")
            # Filter cards with required keys
            valid_cards = {
                k: v
                for k, v in data["card"].items()
                if isinstance(v, dict)
                and all(key in v for key in ["small", "medium", "large", "id"])
            }

            if valid_cards:
                cards = DataFrame()
                cards.insert(0, "name", valid_cards.keys())
                cards.insert(
                    0,
                    "small",
                    Series([value["small"] for value in valid_cards.values()]),
                )
                cards.insert(
                    0,
                    "medium",
                    Series([value["medium"] for value in valid_cards.values()]),
                )
                cards.insert(
                    0,
                    "large",
                    Series([value["large"] for value in valid_cards.values()]),
                )
                cards.insert(
                    0,
                    "konami_id",
                    Series([value["id"] for value in valid_cards.values()]),
                )
                cards.to_parquet("./data/cards.parquet")
                self.logger.info("Wrote %d cards", len(valid_cards))
            else:
                self.logger.warning("No valid cards found to write")

            self.logger.info("Writing Fields...")
            # Filter playmats with required keys
            valid_playmats = {
                k: v
                for k, v in data["playmat"].items()
                if isinstance(v, dict) and all(key in v for key in ["small", "medium"])
            }

            if valid_playmats:
                fields = DataFrame()
                fields.insert(0, "konami_id", valid_playmats.keys())
                fields.insert(
                    0,
                    "small",
                    Series([field["small"] for field in valid_playmats.values()]),
                )
                fields.insert(
                    0,
                    "medium",
                    Series([field["medium"] for field in valid_playmats.values()]),
                )
                fields.to_parquet("./data/fields.parquet")
                self.logger.info("Wrote %d fields", len(valid_playmats))
            else:
                self.logger.warning("No valid fields found to write")

            self.logger.info("Writing Characters...")
            # Process characters data
            if data["character"]:
                # Convert character objects to dictionaries if needed
                character_dicts = []
                for char in data["character"]:
                    if isinstance(char, dict):
                        character_dicts.append(char)
                    else:
                        # Use the to_dict method if available, otherwise convert manually
                        if hasattr(char, "to_dict"):
                            character_dicts.append(char.to_dict())
                        else:
                            # Fallback: extract attributes manually
                            char_dict = {}
                            if hasattr(char, "konami_id"):
                                char_dict["konami_id"] = char.konami_id
                            if hasattr(char, "series"):
                                char_dict["series"] = char.series
                            character_dicts.append(char_dict)

                if character_dicts:
                    # Get all unique keys from all character dictionaries
                    all_keys = set()
                    for char_dict in character_dicts:
                        all_keys.update(char_dict.keys())

                    # Create DataFrame with all attributes
                    characters = DataFrame()
                    for key in sorted(all_keys):  # Sort for consistent column order
                        characters.insert(
                            len(characters.columns),
                            key,
                            [char_dict.get(key) for char_dict in character_dicts],
                        )

                    characters.to_parquet("./data/characters.parquet")
                    self.logger.info(
                        "Wrote %d characters with %d attributes",
                        len(character_dicts),
                        len(all_keys),
                    )
                else:
                    self.logger.warning("No valid character data found to write")
            else:
                self.logger.warning("No characters found to write")

            self.logger.info("Updating Version...")
            with open("./data/version.txt", "w", encoding="utf-8") as file:
                file.write(datetime.today().strftime("%Y-%m-%d"))
