"""Single-card daily guidance spread."""


from nekomata.card.types import Position
from nekomata.spread.base import Spread


class SingleCardSpread(Spread):
    name = "Single Card"
    name_zh = "单牌"

    def __init__(self) -> None:
        super().__init__()
        self._positions = [
            Position(name="Daily Guidance", name_zh="今日指引", description="今日的灵感与指引"),
        ]
