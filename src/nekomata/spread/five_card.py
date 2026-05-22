"""Five-card cross spread with challenge and guidance positions."""

from nekomata.spread.base import Spread


class FiveCardCross(Spread):
    @property
    def display_order(self) -> tuple[int, ...]:
        return (3, 0, 2, 1, 4)
