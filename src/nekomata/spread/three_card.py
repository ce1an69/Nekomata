"""Three-card spread variants: Past/Present/Future, Body/Mind/Spirit, Situation/Action/Result."""


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


class BodyMindSpirit(Spread):
    name = "Body / Mind / Spirit"
    name_zh = "身·心·灵"

    def __init__(self) -> None:
        super().__init__()
        self._positions = [
            Position(name="Body", name_zh="身", description="身体与物质状态"),
            Position(name="Mind", name_zh="心", description="思想与情绪状态"),
            Position(name="Spirit", name_zh="灵", description="灵性与直觉指引"),
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
