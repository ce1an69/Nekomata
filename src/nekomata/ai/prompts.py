from __future__ import annotations

SYSTEM_PROMPT = """你是一位经验丰富的塔罗占卜师，擅长将塔罗牌义与猫咪的习性巧妙结合。
你会根据求问者的问题和所抽到的牌面，给出温暖、有洞察力的解读。

解读风格：{style}
"""


def build_interpretation_prompt(question: str, cards_info: str) -> str:
    return f"""请为以下占卜进行解读：

求问者的问题：{question}

抽到的牌面：
{cards_info}

请给出整体解读，结合牌面之间的关系进行分析。"""
