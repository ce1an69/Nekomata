from __future__ import annotations

from nekomata.card.types import DrawnCard


def template_interpret(drawn_cards: list[DrawnCard], question: str) -> str:
    parts = [f"🔮 问题：{question}\n"]
    for dc in drawn_cards:
        status = "逆位" if dc.is_reversed else "正位"
        keywords = dc.card.keywords_reversed if dc.is_reversed else dc.card.keywords_upright
        meaning = dc.card.meaning_reversed if dc.is_reversed else dc.card.meaning_upright
        parts.append(f"【{dc.position.name_zh}】{dc.card.name_zh}（{status}）")
        parts.append(f"  关键词：{', '.join(keywords)}")
        parts.append(f"  释义：{meaning}")
        parts.append("")
    return "\n".join(parts)
