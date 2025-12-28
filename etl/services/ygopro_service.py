import logging

import requests

from database.models import CardModel
from database.objects import session


class YGOProService:
    """
    A service for interacting with the YGOPro API.
    """

    # YGOPro API URL
    # Note: The 'Duel Links' format option appears to be very outdated, so OCG is used as a workaround
    API_URL: str = (
        "https://db.ygoprodeck.com/api/v7/cardinfo.php?format=OCG&misc=Yes"
    )

    def __init__(self):
        self._last_request_time = 0
        self.logger = logging.getLogger(__name__)

    def get_card_data(self) -> tuple[bool, str]:
        """Get metadata for Duel Links cards from the YGOPro API."""

        if session.query(CardModel).count() > 0:
            return True, "Card data already exists in database."

        metadata_response = requests.get(self.API_URL)

        if metadata_response.status_code != 200:
            return False, f"Failed to get metadata for cards: {metadata_response.text}"

        metadata = metadata_response.json()["data"]

        print(metadata[0]["misc_info"][0])

        session.add_all(
            [
                CardModel(
                    name=card["name"],
                    konami_id=card["misc_info"][0]["konami_id"],
                    frame_type=card["frameType"],
                )
                for card in metadata
                if "konami_id" in card["misc_info"][0]
            ]
        )
        session.commit()

        return True, f"Successfully got metadata for {len(metadata)} cards."
