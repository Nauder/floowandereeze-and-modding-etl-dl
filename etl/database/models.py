from database.objects import base, engine
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column


class CardModel(base):
    """
    Model for card assets.

    Stores information about cards including:
    - name and description (original and modded)
    - bundle identifier
    - data index for Unity file
    - thumbnail icon
    """

    __tablename__ = "card"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    konami_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    frame_type: Mapped[str] = mapped_column(String(255))


base.metadata.create_all(engine)
