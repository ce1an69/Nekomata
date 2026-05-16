from __future__ import annotations

from nekomata.card.types import Position
from nekomata.spread.base import Spread


class PastPresentFuture(Spread):
    name = "Past / Present / Future"
    name_zh = "过去·现在·未来"

    def __init__(self) -> None:
        super().__init__()
        self._positions = [
            Position(name="Past", name_zh="过去", description="过去的影响"),
            Position(name="Present", name_zh="现在", description="当前状况"),
            Position(name="Future", name_zh="未来", description="可能的发展"),
        ]


class SituationActionResult(Spread):
    name = "Situation / Action / Result"
    name_zh = "处境·行动·结果"

    def __init__(self) -> None:
        super().__init__()
        self._positions = [
            Position(name="Situation", name_zh="处境", description="当前的处境"),
            Position(name="Action", name_zh="行动", description="建议的行动"),
            Position(name="Result", name_zh="结果", description="可能的结果"),
        ]
