"""AI interpretation prompt templates for tarot readings."""

from nekomata._paths import data_dir

_PROMPTS_DIR = data_dir() / "prompts"

_system_prompt: str | None = None
_spread_prompts: dict[str, str] = {}
_user_template: str | None = None


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


def _load_user_template() -> str:
    global _user_template
    if _user_template is None:
        _user_template = (_PROMPTS_DIR / "user_template.md").read_text(encoding="utf-8")
    return _user_template


def build_user_prompt(question: str, cards_info: str) -> str:
    """Build the user message for AI interpretation."""
    return _load_user_template().format(question=question, cards_info=cards_info)
