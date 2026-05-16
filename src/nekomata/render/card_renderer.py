from __future__ import annotations

from pathlib import Path

from rich.panel import Panel
from rich.text import Text

from nekomata.card.types import Card, DrawnCard


def get_preview_path(card: Card) -> Path | None:
    if card.image_path is None:
        return None
    return card.image_path.with_name(card.image_path.stem + "_detail.png")


def render_card_text(drawn: DrawnCard, width: int = 40) -> Panel:
    card = drawn.card
    reversal = " ↕ 逆位" if drawn.is_reversed else ""
    border_style = "blue" if drawn.is_reversed else "yellow"

    content = Text()
    content.append(f"{card.name_zh} ({card.name}){reversal}\n\n")

    if drawn.is_reversed:
        content.append("逆位关键词：", style="bold")
        content.append(", ".join(card.keywords_reversed))
        content.append("\n\n")
        content.append(card.meaning_reversed)
    else:
        content.append("正位关键词：", style="bold")
        content.append(", ".join(card.keywords_upright))
        content.append("\n\n")
        content.append(card.meaning_upright)

    return Panel(
        content,
        title=f"[{drawn.position.name_zh}]",
        border_style=border_style,
        width=width,
        padding=(0, 1),
    )


def render_card_detail(drawn: DrawnCard, width: int = 60) -> Panel:
    card = drawn.card
    border_style = "blue" if drawn.is_reversed else "yellow"
    status = "逆位 ↕" if drawn.is_reversed else "正位"

    content = Text()
    content.append(f"{card.name_zh} ({card.name})  [{status}]\n", style="bold")
    content.append(f"元素：{card.element}  ·  星座：{card.astrology}\n\n")

    content.append("正位关键词：", style="bold")
    content.append(", ".join(card.keywords_upright))
    content.append("\n")
    content.append(card.meaning_upright)
    content.append("\n\n")

    content.append("逆位关键词：", style="bold")
    content.append(", ".join(card.keywords_reversed))
    content.append("\n")
    content.append(card.meaning_reversed)

    return Panel(
        content,
        title=f"[{drawn.position.name_zh}] — {card.name_zh}",
        border_style=border_style,
        width=width,
        padding=(1, 2),
    )


def render_reading_summary(drawn_cards: list[DrawnCard], question: str) -> Panel:
    content = Text()
    content.append(f"🔮 {question}\n\n")
    for dc in drawn_cards:
        status = "逆位" if dc.is_reversed else "正位"
        content.append(f"【{dc.position.name_zh}】", style="bold")
        content.append(f" {dc.card.name_zh}（{status}）\n")
    return Panel(content, title="占卜结果", border_style="magenta")
