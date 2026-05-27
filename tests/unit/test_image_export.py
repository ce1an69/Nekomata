"""Tests for interpretation image export."""

from nekomata.card.data import load_all_cards
from nekomata.card.types import DrawnCard, Position
from nekomata.render.image_export import render_interp_image


def _drawn_cards(count: int = 3) -> list[DrawnCard]:
    cards = load_all_cards()[:count]
    return [
        DrawnCard(
            card=card,
            position=Position("Position", "位置", ""),
            is_reversed=index % 2 == 1,
        )
        for index, card in enumerate(cards)
    ]


def test_render_interp_image_handles_markdown_and_cards():
    md = (
        "你好呀，远方的朋友。**星辰**已经听见了你的声音。\n\n"
        "## 牌面解析\n\n"
        "- 从迷雾中苏醒\n"
        "- 释放与解脱\n\n"
        "> 你现在的状态是安全的。\n\n"
        "1. 直面恐惧\n"
        "2. 信任直觉\n"
    )

    img = render_interp_image(md, _drawn_cards(5))

    assert img.size[0] == 1080
    assert img.size[1] > 700
    assert img.getbbox() is not None
