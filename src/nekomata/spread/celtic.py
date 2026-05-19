"""Celtic Cross spread — 10-card comprehensive reading."""


from nekomata.card.types import Position
from nekomata.spread.base import Spread


class CelticCross(Spread):
    name = "Celtic Cross"
    name_zh = "凯尔特十字"

    def __init__(self) -> None:
        super().__init__()
        self._positions = [
            Position(name="Present", name_zh="当前处境", description="问题的核心现状"),
            Position(name="Challenge", name_zh="挑战", description="面临的阻碍或冲突"),
            Position(name="Subconscious", name_zh="潜意识", description="深层影响、未被察觉的因素"),
            Position(name="Past", name_zh="过去", description="近期影响当前局势的事件"),
            Position(name="Possible Outcome", name_zh="可能结果", description="按当前趋势的自然发展"),
            Position(name="Future", name_zh="未来", description="即将发生的事件"),
            Position(name="Self", name_zh="自我", description="求问者的态度和心态"),
            Position(name="Environment", name_zh="环境", description="外部影响（他人、社会、环境）"),
            Position(name="Guidance", name_zh="指引", description="建议的行动方向"),
            Position(name="Final Outcome", name_zh="最终结果", description="整体局势的最终走向"),
        ]

    @property
    def display_order(self) -> list[int]:
        return [4, 0, 1, 5, 9, 3, 2, 6, 7, 8]
