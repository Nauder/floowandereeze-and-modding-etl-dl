"""Service for handling game data extraction and processing."""

import os
from typing import Any, Dict

import UnityPy

from util import STREAMING_PATH, GAME_PATH, get_data_wrapper

from .unity_service import UnityService


class GameService:
    """Service class for handling game data operations."""

    def __init__(self) -> None:
        """Initialize the GameService with a UnityService instance."""
        self.unity_service = UnityService()

    def get_dir_data(self, data_dir: str, is_streaming: bool) -> Dict[str, Any]:
        """Get data from a directory in the game files.

        Args:
            data_dir: Directory to extract data from.
            is_streaming: Whether to use streaming assets path.

        Returns:
            Dictionary containing extracted data.
        """
        ids = get_data_wrapper()
        for _, _, files in os.walk(
            os.path.join(STREAMING_PATH if is_streaming else GAME_PATH, data_dir)
        ):
            for bundle in files:
                env = UnityPy.load(
                    self.unity_service.prepare_environment(is_streaming, bundle)
                )
                for key in env.container.keys():
                    if data_dir.lower() == "c7":
                        pass
                    if "assets/resources/card/en-us/" in key:
                        self._parse_card(ids, env, bundle, key)
                    elif "assets/resources/sleeve/" in key:
                        self._parse_sleeve(ids, env, bundle, key)
                    elif "assets/resources/playmat/" in key:
                        self._parse_playmat(ids, env, bundle, key)

        return ids

    def _parse_card(self, ids: Dict[str, Any], env: Any, bundle: str, key: str) -> None:
        """Parse card data from Unity environment.

        Args:
            ids: Dictionary to store parsed data.
            env: Unity environment.
            bundle: Bundle name.
            key: Key of the card.
        """
        for obj in env.objects:
            if obj.type.name == "Texture2D":
                obj_data = obj.read()
                if obj_data.m_Name not in ids["card"]:
                    ids["card"][obj_data.m_Name] = {}
                if "/s/" in key:
                    ids["card"][obj_data.m_Name]["small"] = bundle
                if "/m/" in key:
                    ids["card"][obj_data.m_Name]["medium"] = bundle
                if "/l/" in key:
                    ids["card"][obj_data.m_Name]["large"] = bundle
                if "/mask/" in key:
                    ids["card"][obj_data.m_Name]["mask"] = bundle
                if "/name/" in key:
                    ids["card"][obj_data.m_Name]["name"] = bundle

    def _parse_sleeve(
        self, ids: Dict[str, Any], env: Any, bundle: str, key: str
    ) -> None:
        """Parse sleeve data from Unity environment.

        Args:
            ids: Dictionary to store parsed data.
            env: Unity environment.
            bundle: Bundle name.
            key: Key of the sleeve.
        """
        for obj in env.objects:
            if obj.type.name == "Texture2D":
                obj_data = obj.read()
                if obj_data.m_Name not in ids["sleeve"]:
                    ids["sleeve"][obj_data.m_Name] = {}
                if "/s/" in key:
                    ids["sleeve"][obj_data.m_Name]["small"] = bundle
                if "/m/" in key:
                    ids["sleeve"][obj_data.m_Name]["medium"] = bundle

    def _parse_playmat(
        self, ids: Dict[str, Any], env: Any, bundle: str, key: str
    ) -> None:
        """Parse field data from Unity environment.

        Args:
            ids: Dictionary to store parsed data.
            env: Unity environment.
            bundle: Bundle name.
            key: Key of the playmat.
        """
        for obj in env.objects:
            if obj.type.name == "Texture2D":
                obj_data = obj.read()
                if obj_data.m_Name not in ids["playmat"]:
                    ids["playmat"][obj_data.m_Name] = {}
                if "/s/" in key:
                    ids["playmat"][obj_data.m_Name]["small"] = bundle
                if "/m/" in key:
                    ids["playmat"][obj_data.m_Name]["medium"] = bundle
