"""Five-card cross spread with challenge and guidance positions."""


from nekomata.card.types import Position
from nekomata.spread.base import Spread


class FiveCardCross(Spread):
    name = "Five Card Cross"
    name_zh = "五牌十字"

    def __init__(self) -> None:
        super().__init__()
        self._positions = [
            Position(name="Present", name_zh="现状", description="当前处境"),
            Position(name="Challenge", name_zh="挑战", description="面临的阻碍"),
            Position(name="Foundation", name_zh="根基", description="问题根源"),
            Position(name="Past", name_zh="过去", description="近期影响"),
            Position(name="Guidance", name_zh="指引", description="建议方向"),
        ]
