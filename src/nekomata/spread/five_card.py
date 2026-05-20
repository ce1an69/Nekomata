"""Five-card cross spread with challenge and guidance positions."""

from nekomata.spread.base import Spread


class FiveCardCross(Spread):
    name = "Five Card Cross"

    @property
    def display_order(self) -> list[int]:
        return [4, 0, 1, 3, 2]
