"""AI interpretation prompt templates for tarot readings."""

from nekomata._paths import data_dir

_PROMPTS_DIR = data_dir() / "prompts"


def load_system_prompt() -> str:
    """Load the system prompt from data/prompts/system.md."""
    return (_PROMPTS_DIR / "system.md").read_text(encoding="utf-8")


def load_spread_prompt(spread_key: str) -> str:
    """Load a spread-specific prompt from data/prompts/<key>.md."""
    path = _PROMPTS_DIR / f"{spread_key}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _load_user_template() -> str:
    return (_PROMPTS_DIR / "user_template.md").read_text(encoding="utf-8")


def build_user_prompt(question: str, cards_info: str) -> str:
    """Build the user message for AI interpretation."""
    return _load_user_template().format(question=question, cards_info=cards_info)


def build_followup_prompt(question: str, lang: str = "en") -> str:
    """Build the user message for a follow-up question."""
    if lang == "en":
        return f"Follow-up question: {question}\nPlease provide additional interpretation for this follow-up."
    return f"追问：{question}\n请针对这个追问进行补充解读。"
