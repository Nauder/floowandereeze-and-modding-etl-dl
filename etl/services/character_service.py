import re

from enum import Enum
from typing import Any, List, Optional


class CharaSeries(Enum):
    """
    Enumeration of character series, based on their container path.

    For example, the character with the path `sn0411` is from ZEXAL, as it is in the 400-499 range
    """

    DM = 0
    GX = 100
    FDS = 200
    DSOD = 300
    ZEXAL = 400
    ARC_V = 500
    VRAINS = 600
    SEVENS = 700
    STANDARD = 800
    RUSH = 900
    NON_PLAYABLE = 9000

    def check_series(self, chara_id: int) -> bool:
        """Check whether a character belongs to a given series, or is a generic NPC."""
        return (
            self.value <= chara_id < self.value + 100
            if self.value < 9000
            else chara_id >= self.value
        )


class CharaAssetType(Enum):
    """Enumeration of character asset types, based on their names."""

    ICON = "Chara001"
    SELECT = "Chara002"
    DUEL_1 = "Chara003_1"
    DUEL_2 = "Chara003_2"
    DUEL_3 = "Chara003_3"
    DUEL_4 = "Chara003_4"
    DUEL_5 = "Chara003_5"
    DUEL_6 = "Chara003_6"
    DUEL_7 = "Chara003_7"
    DUEL_8 = "Chara003_8"
    DUEL_9 = "Chara003_9"
    DUEL_10 = "Chara003_10"
    DUEL_11 = "Chara003_11"
    DUEL_12 = "Chara003_12"
    DUEL_13 = "Chara003_13"
    DUEL_14 = "Chara003_14"
    DUEL_15 = "Chara003_15"
    DUEL_16 = "Chara003_16"
    DUEL_17 = "Chara003_17"
    DUEL_18 = "Chara003_18"
    DUEL_19 = "Chara003_19"
    DUEL_20 = "Chara003_20"
    DUEL_31 = "Chara003_31"
    DUEL_32 = "Chara003_32"
    DUEL_33 = "Chara003_33"
    DUEL_34 = "Chara003_34"
    DUEL_35 = "Chara003_35"
    DUEL_36 = "Chara003_36"
    DUEL_37 = "Chara003_37"
    DUEL_38 = "Chara003_38"
    DUEL_39 = "Chara003_39"
    DUEL_40 = "Chara003_40"
    DUEL_41 = "Chara003_41"
    DUEL_42 = "Chara003_42"
    WORLD = "Chara004"
    EVENT = "Chara004_1"
    DIALOG_0 = "Chara007_0"
    DIALOG_1 = "Chara007_1"
    DIALOG_2 = "Chara007_2"
    DIALOG_3 = "Chara007_3"
    DIALOG_4 = "Chara007_4"
    DIALOG_5 = "Chara007_5"
    DIALOG_6 = "Chara007_6"
    DIALOG_7 = "Chara007_7"
    DIALOG_8 = "Chara007_8"
    DIALOG_9 = "Chara007_9"
    DIALOG_10 = "Chara007_10"
    DIALOG_11 = "Chara007_11"
    DIALOG_12 = "Chara007_12"
    DIALOG_13 = "Chara007_13"
    DIALOG_14 = "Chara007_14"
    DIALOG_15 = "Chara007_15"
    DIALOG_16 = "Chara007_16"
    DIALOG_17 = "Chara007_17"
    DIALOG_18 = "Chara007_18"
    DIALOG_19 = "Chara007_19"
    DIALOG_20 = "Chara007_20"
    DIALOG_21 = "Chara007_21"
    DIALOG_22 = "Chara007_22"
    DIALOG_23 = "Chara007_23"
    DIALOG_24 = "Chara007_24"
    DIALOG_25 = "Chara007_25"
    DIALOG_26 = "Chara007_26"
    DIALOG_31 = "Chara007_31"
    DIALOG_32 = "Chara007_32"
    DIALOG_33 = "Chara007_33"
    DIALOG_34 = "Chara007_34"
    DIALOG_35 = "Chara007_35"
    DIALOG_36 = "Chara007_36"
    DIALOG_37 = "Chara007_37"
    DIALOG_38 = "Chara007_38"
    DIALOG_39 = "Chara007_39"
    DIALOG_40 = "Chara007_40"
    DIALOG_41 = "Chara007_41"
    DIALOG_42 = "Chara007_42"
    DIALOG_43 = "Chara007_43"
    DIALOG_44 = "Chara007_44"
    DIALOG_45 = "Chara007_45"
    SELECTED_LEGACY = "Chara009"
    SELECTED_NEW = "Chara010"
    HOME_VICTORY = "Chara050_1"
    HOME_SPECIAL = "Chara050_2"
    NAME_BIG = "CharaName001"
    NAME_SMALL = "CharaName002"
    CUTIN = "Cutin001"
    VICTORY = "Cutin002"
    DEFEAT = "Cutin003"
    VERSUS = "VS001"


def match_asset_by_string(asset_string: str) -> Optional[CharaAssetType]:
    for asset_type in CharaAssetType:
        if asset_type.value.lower() in asset_string:
            return asset_type

    return None


def is_character_asset(name: str) -> bool:
    return any(
        re.search(pattern + r"\d{3}\.png", name) is not None
        for pattern in ("chara", "charaname", "cutin", "vs")
    )


def get_konami_id(path: str) -> Optional[int]:
    """Extract numbers from pattern 'sn' + 4 digits"""

    match = re.search(r"sn(\d{4})", path)
    return int(match.group(1)) if match else None


class CharacterAssets:
    """Character assets container with dynamic mapping from CharaAssetType enum values."""

    # Create a mapping from enum values to attribute names
    _ENUM_TO_ATTR = {
        CharaAssetType.ICON: "icon",
        CharaAssetType.SELECT: "select",
        CharaAssetType.DUEL_1: "duel_1",
        CharaAssetType.DUEL_2: "duel_2",
        CharaAssetType.DUEL_3: "duel_3",
        CharaAssetType.DUEL_4: "duel_4",
        CharaAssetType.DUEL_5: "duel_5",
        CharaAssetType.DUEL_6: "duel_6",
        CharaAssetType.DUEL_7: "duel_7",
        CharaAssetType.DUEL_8: "duel_8",
        CharaAssetType.DUEL_9: "duel_9",
        CharaAssetType.DUEL_10: "duel_10",
        CharaAssetType.DUEL_11: "duel_11",
        CharaAssetType.DUEL_12: "duel_12",
        CharaAssetType.DUEL_13: "duel_13",
        CharaAssetType.DUEL_14: "duel_14",
        CharaAssetType.DUEL_15: "duel_15",
        CharaAssetType.DUEL_16: "duel_16",
        CharaAssetType.DUEL_17: "duel_17",
        CharaAssetType.DUEL_18: "duel_18",
        CharaAssetType.DUEL_19: "duel_19",
        CharaAssetType.DUEL_20: "duel_20",
        CharaAssetType.DUEL_31: "duel_31",
        CharaAssetType.DUEL_32: "duel_32",
        CharaAssetType.DUEL_33: "duel_33",
        CharaAssetType.DUEL_34: "duel_34",
        CharaAssetType.DUEL_35: "duel_35",
        CharaAssetType.DUEL_36: "duel_36",
        CharaAssetType.DUEL_37: "duel_37",
        CharaAssetType.DUEL_38: "duel_38",
        CharaAssetType.DUEL_39: "duel_39",
        CharaAssetType.DUEL_40: "duel_40",
        CharaAssetType.DUEL_41: "duel_41",
        CharaAssetType.DUEL_42: "duel_42",
        CharaAssetType.WORLD: "world",
        CharaAssetType.EVENT: "event",
        CharaAssetType.DIALOG_0: "dialog_0",
        CharaAssetType.DIALOG_1: "dialog_1",
        CharaAssetType.DIALOG_2: "dialog_2",
        CharaAssetType.DIALOG_3: "dialog_3",
        CharaAssetType.DIALOG_4: "dialog_4",
        CharaAssetType.DIALOG_5: "dialog_5",
        CharaAssetType.DIALOG_6: "dialog_6",
        CharaAssetType.DIALOG_7: "dialog_7",
        CharaAssetType.DIALOG_8: "dialog_8",
        CharaAssetType.DIALOG_9: "dialog_9",
        CharaAssetType.DIALOG_10: "dialog_10",
        CharaAssetType.DIALOG_11: "dialog_11",
        CharaAssetType.DIALOG_12: "dialog_12",
        CharaAssetType.DIALOG_13: "dialog_13",
        CharaAssetType.DIALOG_14: "dialog_14",
        CharaAssetType.DIALOG_15: "dialog_15",
        CharaAssetType.DIALOG_16: "dialog_16",
        CharaAssetType.DIALOG_17: "dialog_17",
        CharaAssetType.DIALOG_18: "dialog_18",
        CharaAssetType.DIALOG_19: "dialog_19",
        CharaAssetType.DIALOG_20: "dialog_20",
        CharaAssetType.DIALOG_21: "dialog_21",
        CharaAssetType.DIALOG_22: "dialog_22",
        CharaAssetType.DIALOG_23: "dialog_23",
        CharaAssetType.DIALOG_24: "dialog_24",
        CharaAssetType.DIALOG_25: "dialog_25",
        CharaAssetType.DIALOG_26: "dialog_26",
        CharaAssetType.DIALOG_31: "dialog_31",
        CharaAssetType.DIALOG_32: "dialog_32",
        CharaAssetType.DIALOG_33: "dialog_33",
        CharaAssetType.DIALOG_34: "dialog_34",
        CharaAssetType.DIALOG_35: "dialog_35",
        CharaAssetType.DIALOG_36: "dialog_36",
        CharaAssetType.DIALOG_37: "dialog_37",
        CharaAssetType.DIALOG_38: "dialog_38",
        CharaAssetType.DIALOG_39: "dialog_39",
        CharaAssetType.DIALOG_40: "dialog_40",
        CharaAssetType.DIALOG_41: "dialog_41",
        CharaAssetType.DIALOG_42: "dialog_42",
        CharaAssetType.DIALOG_43: "dialog_43",
        CharaAssetType.DIALOG_44: "dialog_44",
        CharaAssetType.DIALOG_45: "dialog_45",
        CharaAssetType.SELECTED_LEGACY: "selected_legacy",
        CharaAssetType.SELECTED_NEW: "selected_new",
        CharaAssetType.HOME_VICTORY: "home_victory",
        CharaAssetType.HOME_SPECIAL: "home_special",
        CharaAssetType.NAME_BIG: "name_big",
        CharaAssetType.NAME_SMALL: "name_small",
        CharaAssetType.CUTIN: "cutin",
        CharaAssetType.VICTORY: "victory",
        CharaAssetType.DEFEAT: "defeat",
        CharaAssetType.VERSUS: "versus",
    }

    # Create reverse mapping from string values to enum
    _VALUE_TO_ENUM = {asset_type.value: asset_type for asset_type in CharaAssetType}
    konami_id: int
    series: str

    def __init__(self):
        """Initialize with all asset attributes set to None."""
        # Initialize all attributes
        for attr_name in self._ENUM_TO_ATTR.values():
            setattr(self, attr_name, None)

    def set_asset_by_string(self, asset_string: str, value: Any) -> bool:
        """
        Args:
            asset_string: String to match against CharaAssetType values (e.g., "Chara001")
            value: Value to set for the matched asset

        Returns:
            True if match found and set, False otherwise
        """
        if asset_string in self._VALUE_TO_ENUM:
            enum_type = self._VALUE_TO_ENUM[asset_string]
            attr_name = self._ENUM_TO_ATTR[enum_type]
            setattr(self, attr_name, value)
            return True
        return False

    def get_asset_by_string(self, asset_string: str) -> Optional[Any]:
        """
        Get asset by matching the string against enum values.

        Args:
            asset_string: String to match against CharaAssetType values

        Returns:
            Asset value if found, None otherwise
        """
        if asset_string in self._VALUE_TO_ENUM:
            enum_type = self._VALUE_TO_ENUM[asset_string]
            attr_name = self._ENUM_TO_ATTR[enum_type]
            return getattr(self, attr_name)
        return None

    def set_asset_by_enum(self, asset_type: CharaAssetType, value: Any) -> None:
        """Set asset by CharaAssetType enum."""
        attr_name = self._ENUM_TO_ATTR[asset_type]
        setattr(self, attr_name, value)

    def get_asset_by_enum(self, asset_type: CharaAssetType) -> Optional[Any]:
        """Get asset by CharaAssetType enum."""
        attr_name = self._ENUM_TO_ATTR[asset_type]
        return getattr(self, attr_name)

    @classmethod
    def get_supported_strings(cls) -> List[str]:
        """Get list of all supported asset strings."""
        return list(cls._VALUE_TO_ENUM.keys())

    def to_dict(self) -> dict:
        """Convert CharacterAssets to a dictionary for JSON serialization."""
        result = {}

        # Add konami_id and series if they exist
        if hasattr(self, "konami_id"):
            result["konami_id"] = self.konami_id
        if hasattr(self, "series"):
            result["series"] = self.series

        # Add all asset attributes that are not None
        for attr_name in self._ENUM_TO_ATTR.values():
            value = getattr(self, attr_name, None)
            if value is not None:
                result[attr_name] = value

        return result
