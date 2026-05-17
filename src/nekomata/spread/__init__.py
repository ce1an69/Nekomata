"""Spread registry and factory for all tarot card layouts."""


from nekomata.spread.base import Spread
from nekomata.spread.single import SingleCardSpread
from nekomata.spread.three_card import PastPresentFuture, SituationActionResult, BodyMindSpirit
from nekomata.spread.five_card import FiveCardCross
from nekomata.spread.celtic import CelticCross

# Ordered registry: (key, description_zh, class)
SPREAD_REGISTRY: list[tuple[str, str, type[Spread]]] = [
    ("single", "每日灵感", SingleCardSpread),
    ("past_present_future", "时间线三牌阵", PastPresentFuture),
    ("situation_action_result", "问题分析", SituationActionResult),
    ("body_mind_spirit", "整体状态", BodyMindSpirit),
    ("five_card_cross", "处境+挑战+潜力", FiveCardCross),
    ("celtic_cross", "深度全面解读（10 牌）", CelticCross),
]


def get_spread(key: str) -> Spread:
    """Create a Spread instance by registry key, injecting the description."""
    for k, desc, cls in SPREAD_REGISTRY:
        if k == key:
            spread = cls()
            spread.description = desc
            return spread
    raise KeyError(f"Unknown spread: {key}")
