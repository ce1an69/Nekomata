"""AI interpretation prompt templates for tarot readings."""

from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parents[3] / "data"
_PROMPTS_DIR = _DATA_DIR / "prompts"

_system_prompt: str | None = None
_spread_prompts: dict[str, str] = {}


def load_system_prompt() -> str:
    """Load and cache the system prompt from data/prompts/system.md."""
    global _system_prompt
    if _system_prompt is None:
        _system_prompt = (_PROMPTS_DIR / "system.md").read_text(encoding="utf-8")
    return _system_prompt


def load_spread_prompt(spread_key: str) -> str:
    """Load and cache a spread-specific prompt from data/prompts/<key>.md."""
    if spread_key not in _spread_prompts:
        path = _PROMPTS_DIR / f"{spread_key}.md"
        if path.exists():
            _spread_prompts[spread_key] = path.read_text(encoding="utf-8")
        else:
            _spread_prompts[spread_key] = ""
    return _spread_prompts[spread_key]


def build_user_prompt(question: str, cards_info: str) -> str:
    """Build the user message for AI interpretation."""
    return f"""请为以下占卜进行解读：

求问者的问题：{question}

抽到的牌面：
{cards_info}

请逐张解读每张牌的含义，再综合分析牌面之间的关系，给出整体建议。"""
