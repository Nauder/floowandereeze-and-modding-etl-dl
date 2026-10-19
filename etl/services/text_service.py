"""Read English display names from the game's optional MessagePack text groups."""

import base64
import html
import logging
import re
from typing import Dict, Optional

import msgpack

from .resource_service import load_resource, unscramble

_REFERENCE = re.compile(r"<(chara|skill)\b([^>]*)/?>", re.IGNORECASE)
_ATTRIBUTE = re.compile(r"(\w+)\s*=\s*(['\"])(.*?)\2")


def parse_text_group(data: bytes) -> Dict[str, str]:
    """Decode a plain or scrambled MessagePack dictionary, excluding metadata."""
    group = msgpack.unpackb(data, raw=False)
    if not isinstance(group, dict):
        raise ValueError("Game text group must be a dictionary")
    texts = {}
    for key, value in group.items():
        if (
            not isinstance(key, str)
            or not isinstance(value, str)
            or key.startswith("_")
        ):
            continue
        if group.get("_SCRKEY_", False):
            key = unscramble(
                base64.b64decode("".join(key.split()), validate=True)
            ).decode("utf-8")
        if group.get("_SCR_", False):
            value = unscramble(
                base64.b64decode("".join(value.split()), validate=True)
            ).decode("utf-8")
        texts[key] = value
    return texts


class TextService:
    """Cache optional name tables and resolve their character/skill references."""

    def __init__(self, game_path: str) -> None:
        self.game_path = game_path
        self.groups: Dict[str, Dict[str, str]] = {}
        self.logger = logging.getLogger(__name__)

    def get_group(self, group: str) -> Dict[str, str]:
        """Load each optional group once; missing downloads leave names empty."""
        if group not in self.groups:
            try:
                data = load_resource(self.game_path, f"Texts/st_IDS_{group}")
            except FileNotFoundError:
                self.logger.warning(
                    "Optional IDS_%s table is missing; names may be unavailable", group
                )
                self.groups[group] = {}
            else:
                try:
                    self.groups[group] = parse_text_group(data)
                except (ValueError, msgpack.UnpackException) as error:
                    raise ValueError(
                        f"Invalid IDS_{group} text table: {error}"
                    ) from error
        return self.groups[group]

    def character_name(self, character_id: int) -> Optional[str]:
        """Return a character's display name using its exact game ID."""
        return self._resolve(self.get_group("NPC_NAME").get(f"ID{character_id:04d}"))

    def item_name(self, item_id: str) -> Optional[str]:
        """Return the item label shared by sleeve and playmat artwork IDs."""
        if not item_id.isdecimal():
            return None
        return self._resolve(self.get_group("ITEM").get(f"ID{int(item_id):04d}"))

    def _resolve(self, text: Optional[str], depth: int = 0) -> Optional[str]:
        """Resolve known display-name tags; never export unresolved markup."""
        if not text or not text.strip() or depth >= 10:
            return None

        def replace(match: re.Match) -> str:
            attributes = {key: value for key, _, value in _ATTRIBUTE.findall(match[2])}
            reference_id = attributes.get("id", "")
            if not reference_id.isdecimal():
                return match[0]
            if match[1].lower() == "chara":
                kind = attributes.get("get")
                if kind not in ("name", "subname"):
                    return match[0]
                prefix = "SUB_ID" if kind == "subname" else "ID"
                value = self.get_group("NPC_NAME").get(
                    f"{prefix}{int(reference_id):04d}"
                )
            else:
                if attributes.get("type") != "name":
                    return match[0]
                value = self.get_group("SKILL").get(f"NAME{int(reference_id):03d}")
            return self._resolve(value, depth + 1) or match[0]

        text = _REFERENCE.sub(replace, text)
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        if re.search(r"<[^>]*>", text):
            return None
        return html.unescape(text).strip() or None
