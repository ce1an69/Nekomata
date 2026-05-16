# Phase 1 MVP 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现可运行的 TUI 塔罗占卜 MVP — 文字牌面、单牌/三牌阵、模板解读、日志存储。

**Architecture:** 自底向上构建：数据模型 → 牌组/牌阵逻辑 → 存储服务 → Textual Screen。Phase 1 全部使用文字渲染，像素牌面在 Phase 2 加入。

**Tech Stack:** Python 3.12+, Textual, PyYAML, SQLite, pytest, pytest-asyncio

---

## 文件结构

```
Nekomata/
├── pyproject.toml
├── config.toml
├── scripts/
│   └── generate_card_data.py      # 生成 card_meanings.yaml
├── data/
│   └── card_meanings.yaml         # 78 张牌释义（由脚本生成）
├── assets/
│   └── cards/
│       ├── major/                  # 22 张大阿卡纳 PNG（Phase 2）
│       │   ├── major_00.png        #   常规 64×96
│       │   ├── major_00_detail.png #   预览 128×192
│       │   └── ...
│       ├── cups/
│       ├── wands/
│       ├── swords/
│       └── pentacles/
├── src/
│   └── nekomata/
│       ├── __init__.py
│       ├── app.py                 # Textual App 入口
│       ├── screens/
│       │   ├── __init__.py
│       │   ├── home.py            # 首页
│       │   ├── spread_select.py   # 选牌阵
│       │   ├── question.py        # 输入问题
│       │   ├── reading.py         # 揭牌展示
│       │   └── interpretation.py  # 解读展示
│       ├── card/
│       │   ├── __init__.py
│       │   ├── types.py           # 数据模型
│       │   ├── data.py            # 牌义加载
│       │   └── deck.py            # 牌组逻辑
│       ├── spread/
│       │   ├── __init__.py
│       │   ├── base.py            # 牌阵基类
│       │   ├── single.py          # 单牌
│       │   └── three_card.py      # 三牌阵
│       ├── render/
│       │   ├── __init__.py
│       │   └── card_renderer.py   # 文字渲染
│       ├── ai/
│       │   ├── __init__.py
│       │   ├── interpreter.py     # 模板解读
│       │   └── prompts.py         # prompt 模板
│       └── storage/
│           ├── __init__.py
│           ├── config.py          # TOML 配置
│           └── journal.py         # SQLite 日志
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── __init__.py
    │   ├── test_types.py
    │   ├── test_data.py
    │   ├── test_deck.py
    │   ├── test_spread.py
    │   ├── test_renderer.py
    │   ├── test_interpreter.py
    │   ├── test_journal.py
    │   └── test_config.py
    └── integration/
        ├── __init__.py
        └── test_flow.py
```

---

### Task 1: 项目脚手架

**Files:**
- Create: `pyproject.toml`
- Create: `src/nekomata/__init__.py`（及所有子包 `__init__.py`）
- Create: `tests/conftest.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`
- Create: `assets/cards/.gitkeep`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "nekomata"
version = "0.1.0"
description = "像素风猫咪塔罗牌终端占卜应用"
requires-python = ">=3.12"
license = {text = "MIT"}
dependencies = [
    "textual>=0.50",
    "rich>=13.0",
    "pyyaml>=6.0",
    "pillow>=10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-mock>=3.12",
]
pixel = [
    "rich-pixels>=1.0",
]

[project.scripts]
nekomata = "nekomata.app:main"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: 创建目录结构和空文件**

```bash
mkdir -p src/nekomata/{screens,card,spread,render,ai,storage}
mkdir -p tests/{unit,integration}
mkdir -p assets/cards
touch src/nekomata/__init__.py
touch src/nekomata/screens/__init__.py
touch src/nekomata/card/__init__.py
touch src/nekomata/spread/__init__.py
touch src/nekomata/render/__init__.py
touch src/nekomata/ai/__init__.py
touch src/nekomata/storage/__init__.py
touch tests/__init__.py
touch tests/conftest.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch assets/cards/.gitkeep
```

- [ ] **Step 3: 安装依赖并验证**

Run: `pip install -e ".[dev]"`
Expected: 成功安装 textual, rich, pyyaml, pillow, pytest 等

Run: `pytest --co`
Expected: `no tests collected`（正常，还没有测试）

- [ ] **Step 4: 提交**

```bash
git add pyproject.toml src/ tests/ assets/cards/.gitkeep
git commit -m "chore: init project scaffolding with textual + pytest"
```

---

### Task 2: 牌数据模型（types.py）

**Files:**
- Create: `src/nekomata/card/types.py`
- Test: `tests/unit/test_types.py`

- [ ] **Step 1: 写测试**

```python
# tests/unit/test_types.py
from pathlib import Path

from nekomata.card.types import Arcana, Card, DrawnCard, Position, Reading


def test_arcana_values():
    assert set(Arcana) == {
        Arcana.MAJOR, Arcana.CUPS, Arcana.WANDS, Arcana.SWORDS, Arcana.PENTACLES
    }


def test_arcana_is_str():
    assert Arcana.MAJOR == "major"
    assert Arcana.CUPS == "cups"


def test_card_creation():
    card = Card(
        id="major_00",
        name="The Fool",
        name_zh="愚者",
        arcana=Arcana.MAJOR,
        number=0,
        element="air",
        astrology="Uranus",
        keywords_upright=("新开始", "天真", "冒险"),
        keywords_reversed=("鲁莽", "冒失", "停滞"),
        meaning_upright="一段新旅程的开始。",
        meaning_reversed="过于鲁莽。",
    )
    assert card.id == "major_00"
    assert card.arcana == Arcana.MAJOR
    assert len(card.keywords_upright) == 3


def test_card_frozen():
    card = Card(
        id="test", name="Test", name_zh="测试", arcana=Arcana.MAJOR,
        number=0, element="air", astrology="Uranus",
        keywords_upright=(), keywords_reversed=(),
        meaning_upright="up", meaning_reversed="down",
    )
    try:
        card.name = "changed"
        assert False, "Should be frozen"
    except AttributeError:
        pass


def test_position():
    pos = Position(name="Present", name_zh="现在", description="当前状况")
    assert pos.name_zh == "现在"


def test_drawn_card():
    card = Card(
        id="test", name="Test", name_zh="测试", arcana=Arcana.CUPS,
        number=1, element="water", astrology="Cancer",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
    )
    pos = Position(name="Past", name_zh="过去", description="过去的影响")
    dc = DrawnCard(card=card, position=pos, is_reversed=True)
    assert dc.is_reversed is True
    assert dc.card.name_zh == "测试"
    assert dc.position.name == "Past"


def test_reading():
    from datetime import datetime
    from uuid import uuid4
    reading = Reading(
        id=uuid4(),
        timestamp=datetime.now(),
        question="今天运势如何？",
        spread_name="Single Card",
        spread_name_zh="单牌",
        drawn_cards=[],
    )
    assert reading.interpretation is None
    assert reading.question == "今天运势如何？"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/test_types.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nekomata.card.types'`

- [ ] **Step 3: 实现 types.py**

```python
# src/nekomata/card/types.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import UUID


class Arcana(str, Enum):
    MAJOR = "major"
    CUPS = "cups"
    WANDS = "wands"
    SWORDS = "swords"
    PENTACLES = "pentacles"


@dataclass(frozen=True)
class Card:
    id: str
    name: str
    name_zh: str
    arcana: Arcana
    number: int
    element: str
    astrology: str
    keywords_upright: tuple[str, ...]
    keywords_reversed: tuple[str, ...]
    meaning_upright: str
    meaning_reversed: str
    image_path: Path | None = None


@dataclass(frozen=True)
class Position:
    name: str
    name_zh: str
    description: str


@dataclass
class DrawnCard:
    card: Card
    position: Position
    is_reversed: bool


@dataclass
class Reading:
    id: UUID
    timestamp: datetime
    question: str
    spread_name: str
    spread_name_zh: str
    drawn_cards: list[DrawnCard]
    interpretation: str | None = None
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/test_types.py -v`
Expected: 6 passed

- [ ] **Step 5: 提交**

```bash
git add src/nekomata/card/types.py tests/unit/test_types.py
git commit -m "feat: add card data models (Arcana, Card, DrawnCard, Position, Reading)"
```

---

### Task 3: 牌义数据 YAML + 加载器

**Files:**
- Create: `scripts/generate_card_data.py`
- Create: `data/card_meanings.yaml`（由脚本生成）
- Create: `src/nekomata/card/data.py`
- Test: `tests/unit/test_data.py`

- [ ] **Step 1: 写数据生成脚本**

```python
# scripts/generate_card_data.py
"""生成 data/card_meanings.yaml，包含全部 78 张塔罗牌释义。"""
from pathlib import Path
import yaml

MAJOR_ARCANA = [
    {"id": "major_00", "name": "The Fool", "name_zh": "愚者", "number": 0, "element": "air", "astrology": "Uranus",
     "up": ["新开始", "天真", "自由"], "down": ["鲁莽", "冒失", "犹豫"],
     "m_up": "猫咪追蝴蝶，不顾脚下悬崖——一段带着纯真与勇气的新旅程开始了。",
     "m_down": "盲目跳入未知，或者因为过度恐惧而停滞不前。"},
    {"id": "major_01", "name": "The Magician", "name_zh": "魔术师", "number": 1, "element": "air", "astrology": "Mercury",
     "up": ["创造力", "技能", "意志力"], "down": ["操纵", "欺骗", "浪费才能"],
     "m_up": "猫把桌上的东西一件件推下去——创造力与行动力的完美结合，你拥有所需的全部工具。",
     "m_down": "猫咪把毛线团玩成了死结——才能被浪费或用于不当目的。"},
    {"id": "major_02", "name": "The High Priestess", "name_zh": "女祭司", "number": 2, "element": "water", "astrology": "Moon",
     "up": ["直觉", "潜意识", "神秘"], "down": ["忽略直觉", "表面化", "隐藏动机"],
     "m_up": "猫在月光下静静凝视远方——倾听内心深处的声音，答案就在直觉之中。",
     "m_down": "猫咪假装没听到你叫它——忽视内在智慧，表面现象遮蔽了真相。"},
    {"id": "major_03", "name": "The Empress", "name_zh": "女皇", "number": 3, "element": "earth", "astrology": "Venus",
     "up": ["丰饶", "滋养", "自然"], "down": ["依赖", "过度保护", "创造力枯竭"],
     "m_up": "猫妈妈温柔地舔着小猫——丰饶与滋养的能量环绕，创造力蓬勃发展。",
     "m_down": "猫咪霸占了所有猫窝——过度依赖或控制，创造力陷入停滞。"},
    {"id": "major_04", "name": "The Emperor", "name_zh": "皇帝", "number": 4, "element": "fire", "astrology": "Aries",
     "up": ["权威", "秩序", "领导力"], "down": ["专制", "僵化", "控制欲"],
     "m_up": "猫端坐在最高处的猫爬架上俯瞰领地——稳定的结构、权威与领导力。",
     "m_down": "猫咪不准任何人靠近它的食盆——过度控制与僵化。"},
    {"id": "major_05", "name": "The Hierophant", "name_zh": "教皇", "number": 5, "element": "earth", "astrology": "Taurus",
     "up": ["传统", "教导", "信仰"], "down": ["教条", "叛逆", "墨守成规"],
     "m_up": "老猫教小猫如何使用猫砂盆——传统的智慧与值得信赖的指导。",
     "m_down": "猫咪拒绝使用新猫砂——过于固守传统或盲目叛逆。"},
    {"id": "major_06", "name": "The Lovers", "name_zh": "恋人", "number": 6, "element": "air", "astrology": "Gemini",
     "up": ["爱情", "选择", "和谐"], "down": ["失衡", "冲突", "错误选择"],
     "m_up": "两只猫互相舔毛——深刻的关系与重要的人生选择，需要心与心的连结。",
     "m_down": "两只猫为争夺阳光吵起来——关系失衡或价值观冲突。"},
    {"id": "major_07", "name": "The Chariot", "name_zh": "战车", "number": 7, "element": "water", "astrology": "Cancer",
     "up": ["意志", "胜利", "决心"], "down": ["失控", "攻击性", "方向不明"],
     "m_up": "猫以闪电般的速度冲向激光笔的红点——凭借坚定意志冲破障碍。",
     "m_down": "猫咪追着自己的尾巴转圈——失去方向感或缺乏自律。"},
    {"id": "major_08", "name": "Strength", "name_zh": "力量", "number": 8, "element": "fire", "astrology": "Leo",
     "up": ["勇气", "耐心", "内在力量"], "down": ["软弱", "自我怀疑", "缺乏自制"],
     "m_up": "猫安静地盯着你，你不敢动——不是蛮力，而是内在的坚定与温柔的勇气。",
     "m_down": "猫咪被黄瓜吓得跳起来——内在力量不足，被恐惧左右。"},
    {"id": "major_09", "name": "The Hermit", "name_zh": "隐者", "number": 9, "element": "earth", "astrology": "Virgo",
     "up": ["内省", "智慧", "独处"], "down": ["孤立", "逃避", "固执"],
     "m_up": "猫钻进纸箱深处沉思——需要独处与内省，在寂静中寻找内在智慧。",
     "m_down": "猫咪藏在床底下不肯出来——过度孤立，逃避现实。"},
    {"id": "major_10", "name": "Wheel of Fortune", "name_zh": "命运之轮", "number": 10, "element": "fire", "astrology": "Jupiter",
     "up": ["转折", "机遇", "命运"], "down": ["厄运", "抗拒改变", "周期低谷"],
     "m_up": "猫追着滚动的毛线球——命运的轮盘转动，好运降临，新的周期开始。",
     "m_down": "猫被滚动的毛线球绊倒了——运势低迷，但这也是暂时的。"},
    {"id": "major_11", "name": "Justice", "name_zh": "正义", "number": 11, "element": "air", "astrology": "Libra",
     "up": ["公正", "真相", "因果"], "down": ["不公", "逃避责任", "偏见"],
     "m_up": "猫一脸严肃地审视你打翻的水杯——公正与真相，因果循环自有定数。",
     "m_down": "猫咪打翻了花瓶却装无辜——不公正或逃避应承担的责任。"},
    {"id": "major_12", "name": "The Hanged Man", "name_zh": "倒吊人", "number": 12, "element": "water", "astrology": "Neptune",
     "up": ["牺牲", "新视角", "等待"], "down": ["拖延", "无意义牺牲", "固执"],
     "m_up": "猫倒挂在沙发背上，悠然自得——暂停脚步，换个角度看世界。",
     "m_down": "猫卡在树上不下来了——无意义的拖延或执迷不悟。"},
    {"id": "major_13", "name": "Death", "name_zh": "死神", "number": 13, "element": "water", "astrology": "Scorpio",
     "up": ["结束", "转变", "重生"], "down": ["抗拒改变", "停滞", "恐惧结束"],
     "m_up": "猫把花瓶从桌上推下去——旧事物的结束为新生命腾出空间。",
     "m_down": "猫咪拼命护住旧纸箱不肯换新的——抗拒必然的改变。"},
    {"id": "major_14", "name": "Temperance", "name_zh": "节制", "number": 14, "element": "fire", "astrology": "Sagittarius",
     "up": ["平衡", "和谐", "耐心"], "down": ["失衡", "过度", "急躁"],
     "m_up": "猫优雅地用爪子拨弄水流——平衡与节制，在对立中找到和谐。",
     "m_down": "猫一口气吃了三碗猫粮——过度或失衡，需要回归中道。"},
    {"id": "major_15", "name": "The Devil", "name_zh": "恶魔", "number": 15, "element": "earth", "astrology": "Capricorn",
     "up": ["束缚", "欲望", "阴影"], "down": ["解放", "打破束缚", "觉醒"],
     "m_up": "猫对激光笔上瘾，追个不停——被欲望或不良习惯束缚，需要正视阴影面。",
     "m_down": "猫咪终于对激光笔失去兴趣了——从束缚中解脱，重获自由。"},
    {"id": "major_16", "name": "The Tower", "name_zh": "塔", "number": 16, "element": "fire", "astrology": "Mars",
     "up": ["突变", "崩塌", "觉醒"], "down": ["逃避灾难", "恐惧改变", "缓慢衰退"],
     "m_up": "猫把整个书架推倒了——突如其来的剧变摧毁了虚假的安全感，但真相终将浮现。",
     "m_down": "书架摇摇欲坠但还没倒——逃避必要的改变，反而延长了痛苦。"},
    {"id": "major_17", "name": "The Star", "name_zh": "星星", "number": 17, "element": "air", "astrology": "Aquarius",
     "up": ["希望", "灵感", "宁静"], "down": ["失望", "脱离现实", "信心丧失"],
     "m_up": "猫在阳光下打盹，肚皮朝天——希望与灵感如星光降临，内心充满宁静。",
     "m_down": "猫咪望着窗外叹气——希望的破灭或脱离现实的幻想。"},
    {"id": "major_18", "name": "The Moon", "name_zh": "月亮", "number": 18, "element": "water", "astrology": "Pisces",
     "up": ["幻觉", "潜意识", "不安"], "down": ["释放恐惧", "真相显现", "走出迷雾"],
     "m_up": "猫对着月亮嚎叫——深层的恐惧与幻觉浮现，潜意识的力量需要被正视。",
     "m_down": "猫咪终于从床底出来了——迷雾散去，恐惧开始消退。"},
    {"id": "major_19", "name": "The Sun", "name_zh": "太阳", "number": 19, "element": "fire", "astrology": "Sun",
     "up": ["快乐", "成功", "活力"], "down": ["暂时的低潮", "过度乐观", "内在小孩受阻"],
     "m_up": "猫在阳光下打滚，快乐得呼噜呼噜——光明、喜悦与成功的能量环绕。",
     "m_down": "猫咪躲在阴凉处——暂时的低潮，但阳光终将回来。"},
    {"id": "major_20", "name": "Judgement", "name_zh": "审判", "number": 20, "element": "fire", "astrology": "Pluto",
     "up": ["觉醒", "重生", "反思"], "down": ["自我怀疑", "逃避反省", "无法释怀"],
     "m_up": "猫听到开罐头的声音，从沉睡中一跃而起——深刻的觉醒与重生时刻。",
     "m_down": "猫咪假装没听到开罐头的声音——逃避自我反省，无法释怀过去。"},
    {"id": "major_21", "name": "The World", "name_zh": "世界", "number": 21, "element": "earth", "astrology": "Saturn",
     "up": ["圆满", "完成", "成就"], "down": ["不完整", "延迟", "缺乏收尾"],
     "m_up": "猫终于钻进了那个完美尺寸的纸箱——一个完整周期的圆满完成，万物归一。",
     "m_down": "纸箱太小了，猫钻不进去——旅程尚未完成，还有未了的事务。"},
]

MINOR_SUITS = {
    "cups": {"element": "water", "astrology": "Cancer", "theme": "情感与关系"},
    "wands": {"element": "fire", "astrology": "Aries", "theme": "行动与激情"},
    "swords": {"element": "air", "astrology": "Gemini", "theme": "思想与冲突"},
    "pentacles": {"element": "earth", "astrology": "Taurus", "theme": "物质与实际"},
}

RANK_NAMES = {
    1: ("Ace", "王牌"),
    2: ("Two", "二"),
    3: ("Three", "三"),
    4: ("Four", "四"),
    5: ("Five", "五"),
    6: ("Six", "六"),
    7: ("Seven", "七"),
    8: ("Eight", "八"),
    9: ("Nine", "九"),
    10: ("Ten", "十"),
    11: ("Page", "侍从"),
    12: ("Knight", "骑士"),
    13: ("Queen", "王后"),
    14: ("King", "国王"),
}

SUIT_ZH = {"cups": "圣杯", "wands": "权杖", "swords": "宝剑", "pentacles": "星币"}

MINOR_MEANINGS = {
    "cups": {
        1: (["新感情", "灵感", "心灵开放"], ["情感封闭", "空虚", "压抑感情"],
            "猫咪发现了一个全新的水碗——新的情感体验与心灵觉醒的开始。",
            "猫咪对新水碗嗤之以鼻——情感上的封闭或空虚。"),
        2: (["连结", "吸引", "平衡"], ["不和谐", "疏离", "沟通不畅"],
            "两只猫在窗台上互相依偎——深厚的情感连结与吸引。",
            "两只猫背对背坐着——关系中的疏离感或沟通不畅。"),
        3: (["庆祝", "友谊", "创意合作"], ["过度社交", "孤立", "缺乏分享"],
            "三只猫围在食盆旁其乐融融——友谊与庆祝的时刻。",
            "猫咪独自躲在角落——社交生活中的孤立或缺乏分享。"),
        4: (["倦怠", "不满", "冥想"], ["新鲜感", "重新投入", "打破常规"],
            "猫对满屋的玩具无动于衷——情感上的倦怠与不满，需要新鲜感。",
            "猫咪发现了旧玩具的新玩法——重新找回热情。"),
        5: (["失落", "悲伤", "遗憾"], ["接受", "走出低谷", "新的希望"],
            "猫蹲在打翻的牛奶前一脸哀伤——情感的失落与遗憾，但并非全部都失去了。",
            "猫咪发现旁边还有一碗牛奶——开始接受现实，走出情感低谷。"),
        6: (["怀旧", "童年", "善意"], ["固执于过去", "不切实际", "过度依赖"],
            "猫回到小时候待过的纸箱——美好的回忆与童真，也可能暗示怀旧。",
            "猫咪守着旧纸箱不肯换——过于沉溺过去，无法面对现实。"),
        7: (["幻想", "选择", "迷惑"], ["清醒", "做出选择", "面对现实"],
            "猫对着鱼缸里的鱼发呆——不切实际的幻想，需要在多个选择中清醒过来。",
            "猫咪终于意识到鱼缸里的鱼吃不到——从幻想中清醒。"),
        8: (["放弃", "离开", "寻求更多"], ["停滞", "恐惧改变", "逃避内心"],
            "猫咪头也不回地走向远方——为了追求更深层的满足，勇敢地放弃已不再适合的事物。",
            "猫咪在门口犹豫不决——恐惧改变，不敢迈出那一步。"),
        9: (["满足", "愿望成真", "丰盛"], ["不满足", "贪婪", "缺乏感恩"],
            "猫躺在满满的零食柜前——内心的满足与愿望成真。",
            "猫咪盯着别人的零食——得到了很多却不知感恩。"),
        10: (["家庭圆满", "幸福", "和谐"], ["家庭矛盾", "情感耗竭", "不和"],
            "一窝小猫和猫妈妈温馨地挤在一起——家庭的圆满与情感的和谐。",
            "猫咪们为了一个猫窝吵成一团——家庭关系中的矛盾与不和。"),
        11: (["好奇", "敏感", "内在消息"], ["不成熟", "情绪化", "缺乏自律"],
            "小猫好奇地用爪子碰水面——敏感、好奇，内心深处的消息浮现。",
            "小猫把手伸进水里又害怕地缩回来——情绪化与不成熟。"),
        12: (["追求", "浪漫", "行动"], ["不切实际", "嫉妒", "情感冲动"],
            "猫优雅地迈向心仪的对象——浪漫的追求与情感上的行动。",
            "猫咪对着镜子里的自己哈气——不切实际的幻想或嫉妒。"),
        13: (["关怀", "直觉", "倾听"], ["缺乏安全感", "情感依赖", "过度敏感"],
            "猫妈妈温柔地注视着小猫——深度的关怀与直觉的智慧。",
            "猫咪紧张地躲在主人身后——缺乏安全感或过度依赖。"),
        14: (["成熟", "掌控", "智慧"], ["情绪不稳定", "操控", "缺乏同理心"],
            "猫王稳坐窗台最高处——情感的成熟与内在的掌控力。",
            "猫咪心情阴晴不定——情绪的不稳定或缺乏内在力量。"),
    },
    "wands": {
        1: (["新机遇", "灵感", "行动力"], ["缺乏动力", "错失机会", "拖延"],
            "猫咪发现了一根新逗猫棒——新的灵感与行动力的迸发。",
            "猫咪对新逗猫棒毫无兴趣——缺乏动力或错失了机遇。"),
        2: (["规划", "未来愿景", "决定"], ["缺乏规划", "恐惧未知", "犹豫不决"],
            "猫站在高处，眺望远方的领地——规划与展望未来。",
            "猫咪不敢从高处跳下来——对未知的恐惧导致犹豫不决。"),
        3: (["进展", "远见", "探索"], ["延迟", "障碍", "缺乏远见"],
            "猫沿着墙头探索新的路线——远见与探索精神，事情正在朝好的方向发展。",
            "猫在墙头迷路了——进展受阻或缺乏明确方向。"),
        4: (["庆祝", "稳定", "归属"], ["不稳定", "缺乏安全感", "过渡期"],
            "猫终于在新家安顿下来——稳定的归属感与值得庆祝的成就。",
            "猫咪躲在床底下不肯出来——缺乏安全感和归属感。"),
        5: (["竞争", "冲突", "挑战"], ["避免冲突", "内部斗争", "妥协"],
            "两只猫为了领地竖起全身的毛——竞争与冲突，但也代表成长的机会。",
            "猫咪选择躲起来避免冲突——逃避竞争或妥协太多。"),
        6: (["胜利", "认可", "骄傲"], ["失败感", "不被认可", "自我怀疑"],
            "猫骄傲地叼着捕获的玩具老鼠——胜利与被认可，你的努力得到了回报。",
            "猫咪把老鼠弄丢了——缺乏自信或感觉不被认可。"),
        7: (["坚持", "防御", "毅力"], ["屈服", "放弃", "压力过大"],
            "猫在十只狗面前依然保持镇定——面对挑战的坚持与勇气。",
            "猫咪被吓得炸毛逃走——在压力面前屈服或放弃。"),
        8: (["快速行动", "变化", "急促"], ["延迟", "挫败", "进展缓慢"],
            "猫以闪电般的速度冲向目标——事态快速发展，需要快速行动。",
            "猫咪在路上停下来舔毛——进展缓慢或行动被拖延。"),
        9: (["韧性", "勇气", "坚守"], ["疲惫", "放弃", "不堪重负"],
            "猫受了伤但依然优雅行走——韧性与内在的勇气，在逆境中坚持。",
            "猫咪趴在地上不想动了——疲惫不堪或准备放弃。"),
        10: (["负担", "责任", "努力"], ["释放压力", "委派", "减少负担"],
            "猫试图一次搬运所有小猫——沉重的负担与责任，需要寻求帮助。",
            "猫咪终于接受了主人的帮助——学会释放压力。"),
        11: (["探索", "自由", "热情"], ["缺乏方向", "冲动", "不成熟"],
            "小猫第一次探索院子——充满热情的自由探索精神。",
            "小猫跑出门又吓得跑回来——缺乏方向或过于冲动。"),
        12: (["冒险", "活力", "直觉行动"], ["鲁莽", "冲动", "不切实际"],
            "猫从高处纵身一跃——充满活力的冒险精神与直觉行动。",
            "猫咪跳到了不稳定的架子上——过于鲁莽或冲动。"),
        13: (["自信", "魅力", "热情"], ["嫉妒", "占有欲", "操控"],
            "猫在阳光下优雅地伸展身体——自信与魅力的展现，充满热情。",
            "猫咪不允许别的猫靠近它的领地——嫉妒或占有欲过强。"),
        14: (["领导力", "远见", "魄力"], ["独断", "霸道", "缺乏远见"],
            "猫王站在高处俯瞰领地——天生的领导力与远见卓识。",
            "猫咪欺负其他猫——独断专行或缺乏包容。"),
    },
    "swords": {
        1: (["突破", "清晰", "真理"], ["混乱", "缺乏清晰", "滥用力量"],
            "猫一爪子划破了阻挡视线的窗帘——思想的突破与真理的显现。",
            "猫咪的爪子被布缠住了——思维混乱或力量被滥用。"),
        2: (["平衡", "艰难选择", "僵局"], ["做出决定", "打破平衡", "真相大白"],
            "猫在两个阳光斑之间来回犹豫——两难之间的抉择与僵持。",
            "猫咪终于选择了一个阳光斑——打破了犹豫，做出决定。"),
        3: (["心碎", "悲伤", "分离"], ["疗愈", "释放痛苦", "走出阴影"],
            "猫咪蹲在紧闭的门前——心痛与分离的哀伤。",
            "门终于开了——痛苦的释放与疗愈开始。"),
        4: (["休息", "恢复", "冥想"], ["疲惫", "过度劳累", "无法放松"],
            "猫蜷成一团沉睡——必要的休息与恢复，为下一阶段积蓄力量。",
            "猫咪在睡梦中还在抽动——无法真正放松或过度劳累。"),
        5: (["冲突", "失败", "恶意"], ["和解", "放下", "重建"],
            "猫打架后独自舔伤口——冲突与失败后的失落感。",
            "猫咪试探性地走向对手——和解的可能性与放下过去。"),
        6: (["过渡", "远离痛苦", "旅行"], ["停滞", "无法前行", "反复"],
            "猫坐车去新家——离开熟悉的环境，向更好的地方过渡。",
            "猫咪在猫包里叫个不停——对改变的抵抗或无法前行。"),
        7: (["策略", "欺骗", "机智"], ["坦白", "重新思考", "放弃欺骗"],
            "猫偷偷把另一只猫的零食据为己有——策略与机智，但需警惕欺骗。",
            "猫咪被当场抓住——策略失败，需要坦诚面对。"),
        8: (["束缚", "困境", "自我限制"], ["释放", "转变视角", "突破限制"],
            "猫被毛线团缠住——感到被困与自我设限，但束缚可能来自内心。",
            "猫咪轻轻一挣就脱身了——限制是自我设想的，突破近在咫尺。"),
        9: (["焦虑", "恐惧", "噩梦"], ["恢复", "面对恐惧", "走出焦虑"],
            "猫在半夜突然惊醒——深层的焦虑与恐惧，但最坏的情况往往只存在于想象中。",
            "猫咪发现只是做了个噩梦——开始面对恐惧，焦虑消退。"),
        10: (["终结", "背叛", "低谷"], ["重生", "触底反弹", "接受结束"],
            "猫的尾巴被踩了——痛苦的终结，但这也意味着触底反弹的起点。",
            "猫咪的尾巴慢慢恢复了——痛苦的结束与重生的开始。"),
        11: (["好奇", "好学", "新思想"], ["缺乏专注", "幼稚", "好奇心过盛"],
            "小猫研究一只蚂蚁——对知识的好奇与探索新思想的渴望。",
            "小猫被蝴蝶分心了——缺乏专注力或过于分散精力。"),
        12: (["行动", "冲动", "果断"], ["不谨慎", "鲁莽", "不计后果"],
            "猫毫不犹豫地跳向目标——果断的行动力，但需要警惕冲动。",
            "猫咪跳到了关闭的窗户上——行动前缺乏思考。"),
        13: (["独立", "敏锐", "清晰"], ["冷漠", "刻薄", "孤立"],
            "猫独自坐在窗台，眼神锐利——独立的思考与敏锐的观察力。",
            "猫咪对所有人哈气——过于冷漠或尖锐的言辞。"),
        14: (["判断力", "权威", "决断"], ["不公正", "冷酷", "滥用权力"],
            "老猫审视着领地上的一切——清晰的判断力与理智的权威。",
            "猫咪对下属态度恶劣——不公正或滥用权威。"),
    },
    "pentacles": {
        1: (["新机遇", "财富", "根基"], ["失去机会", "缺乏规划", "物质焦虑"],
            "猫咪发现了一个藏零食的秘密地点——新的物质机遇与财富的开端。",
            "猫咪错过了那个秘密地点——错失机会或对物质过于焦虑。"),
        2: (["平衡", "适应", "灵活"], ["失衡", "过度", "捉襟见肘"],
            "猫在两个食盆之间优雅地走平衡木——在多个目标间灵活平衡。",
            "猫咪从窄墙上掉了下来——失去平衡或顾此失彼。"),
        3: (["合作", "技能", "团队"], ["缺乏合作", "质量低劣", "独自作业"],
            "三只猫合力推倒柜子——团队合作与技能的结合，共建美好事物。",
            "猫咪们各推各的方向——缺乏合作或团队配合不佳。"),
        4: (["安全", "节约", "控制"], ["贪婪", "不愿分享", "物质执念"],
            "猫紧紧护住自己的零食——对物质安全的需求与储蓄的智慧。",
            "猫咪藏了一屋子零食还不满足——贪婪或对物质的过度执着。"),
        5: (["困难", "孤独", "物质匮乏"], ["恢复", "找到帮助", "走出困境"],
            "流浪猫在寒风中瑟瑟发抖——物质上的困难与孤独，但帮助可能就在身边。",
            "有人打开门让流浪猫进来了——困境中出现转机。"),
        6: (["慷慨", "分享", "帮助"], ["自私", "债务", "过度施舍"],
            "猫把猎物叼给主人——慷慨分享与互帮互助的美德。",
            "猫咪只顾自己吃——自私或对他人需求的忽视。"),
        7: (["投资", "耐心", "长期回报"], ["急躁", "投资失误", "目光短浅"],
            "猫耐心地守在老鼠洞口——耐心等待长期投资的回报。",
            "猫咪等不及跑了——缺乏耐心或短视近利。"),
        8: (["专注", "精通", "匠心"], ["完美主义", "缺乏灵感", "倦怠"],
            "猫专注地用爪子拨弄拼图——精湛的技艺与对工作的专注。",
            "猫咪把拼图推到一边——完美主义导致的倦怠。"),
        9: (["丰盛", "独立", "享受"], ["过度依赖", "虚荣", "失去联系"],
            "猫在丰盛的花园中悠闲散步——物质上的丰盛与独立自主。",
            "猫咪在花园里迷路了——过度依赖物质或与内在失去联系。"),
        10: (["传承", "家族", "长久稳固"], ["家庭纷争", "传统束缚", "代际冲突"],
            "猫咪家族世代居住在同一个屋檐下——家族的传承与长久的稳固。",
            "小猫和老猫为争夺猫窝吵架——家庭内部的纷争。"),
        11: (["学习", "务实", "新的可能"], ["缺乏目标", "懒散", "浪费机会"],
            "小猫认真地观察主人开罐头——务实的学习精神与对物质世界的好奇。",
            "小猫只顾玩不想学——懒散或浪费成长机会。"),
        12: (["可靠", "勤奋", "踏实"], ["懒惰", "不可靠", "拖延"],
            "猫每天准时在门口等候——可靠与勤奋，脚踏实地的努力。",
            "猫咪在应该守门的时候睡大觉——不可靠或懒惰。"),
        13: (["滋养", "丰盛", "关怀"], ["缺乏安全感", "自我忽视", "物质焦虑"],
            "猫在温暖的毯子上舒适地打盹——物质的滋养与丰盛的关怀。",
            "猫咪在空空的食盆前焦虑——物质上的不安全感。"),
        14: (["财富", "成功", "安全"], ["贪婪", "物质主义", "缺乏内在"],
            "猫在自己的领地上悠然自得——物质上的成功与稳固的安全感。",
            "猫咪守着一堆囤积的零食——过度的物质主义。"),
    },
}


def generate():
    cards = []
    # Major Arcana
    for m in MAJOR_ARCANA:
        cards.append({
            "id": m["id"],
            "name": m["name"],
            "name_zh": m["name_zh"],
            "arcana": "major",
            "number": m["number"],
            "element": m["element"],
            "astrology": m["astrology"],
            "keywords_upright": m["up"],
            "keywords_reversed": m["down"],
            "meaning_upright": m["m_up"],
            "meaning_reversed": m["m_down"],
        })

    # Minor Arcana
    for suit, info in MINOR_SUITS.items():
        suit_zh = SUIT_ZH[suit]
        for rank in range(1, 15):
            en_rank, zh_rank = RANK_NAMES[rank]
            name = f"{en_rank} of {suit.capitalize()}"
            name_zh = f"{suit_zh}{zh_rank}"
            meaning = MINOR_MEANINGS[suit][rank]
            cards.append({
                "id": f"{suit}_{rank:02d}",
                "name": name,
                "name_zh": name_zh,
                "arcana": suit,
                "number": rank,
                "element": info["element"],
                "astrology": info["astrology"],
                "keywords_upright": meaning[0],
                "keywords_reversed": meaning[1],
                "meaning_upright": meaning[2],
                "meaning_reversed": meaning[3],
            })

    return cards


if __name__ == "__main__":
    cards = generate()
    out = Path(__file__).parent.parent / "data" / "card_meanings.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        yaml.dump(cards, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"Generated {len(cards)} cards → {out}")
```

- [ ] **Step 2: 运行脚本生成 YAML**

Run: `python scripts/generate_card_data.py`
Expected: `Generated 78 cards → data/card_meanings.yaml`

- [ ] **Step 3: 写测试**

```python
# tests/unit/test_data.py
from pathlib import Path

import pytest

from nekomata.card.data import load_all_cards
from nekomata.card.types import Arcana


DATA_PATH = Path(__file__).parent.parent.parent / "data" / "card_meanings.yaml"


def test_load_returns_78_cards():
    cards = load_all_cards(DATA_PATH)
    assert len(cards) == 78


def test_all_cards_have_required_fields():
    cards = load_all_cards(DATA_PATH)
    for card in cards:
        assert card.id
        assert card.name
        assert card.name_zh
        assert card.arcana in Arcana
        assert card.number >= 0
        assert card.element
        assert card.astrology
        assert len(card.keywords_upright) > 0
        assert len(card.keywords_reversed) > 0
        assert card.meaning_upright
        assert card.meaning_reversed


def test_major_arcana_count():
    cards = load_all_cards(DATA_PATH)
    major = [c for c in cards if c.arcana == Arcana.MAJOR]
    assert len(major) == 22


def test_minor_arcana_count():
    cards = load_all_cards(DATA_PATH)
    for suit in [Arcana.CUPS, Arcana.WANDS, Arcana.SWORDS, Arcana.PENTACLES]:
        suit_cards = [c for c in cards if c.arcana == suit]
        assert len(suit_cards) == 14, f"{suit} should have 14 cards, got {len(suit_cards)}"


def test_no_duplicate_ids():
    cards = load_all_cards(DATA_PATH)
    ids = [c.id for c in cards]
    assert len(ids) == len(set(ids))


def test_major_arcana_numbering():
    cards = load_all_cards(DATA_PATH)
    major = sorted([c for c in cards if c.arcana == Arcana.MAJOR], key=lambda c: c.number)
    assert [c.number for c in major] == list(range(22))
```

- [ ] **Step 4: 运行测试确认失败**

Run: `pytest tests/unit/test_data.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nekomata.card.data'`

- [ ] **Step 5: 实现 data.py**

```python
# src/nekomata/card/data.py
from __future__ import annotations

from pathlib import Path

import yaml

from nekomata.card.types import Arcana, Card


def load_card_meanings(path: Path | None = None) -> list[dict]:
    if path is None:
        path = Path(__file__).resolve().parents[3] / "data" / "card_meanings.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_all_cards(path: Path | None = None) -> list[Card]:
    entries = load_card_meanings(path)
    cards = []
    for e in entries:
        cards.append(Card(
            id=e["id"],
            name=e["name"],
            name_zh=e["name_zh"],
            arcana=Arcana(e["arcana"]),
            number=e["number"],
            element=e["element"],
            astrology=e["astrology"],
            keywords_upright=tuple(e["keywords_upright"]),
            keywords_reversed=tuple(e["keywords_reversed"]),
            meaning_upright=e["meaning_upright"],
            meaning_reversed=e["meaning_reversed"],
        ))
    return cards
```

- [ ] **Step 6: 运行测试确认通过**

Run: `pytest tests/unit/test_data.py -v`
Expected: 6 passed

- [ ] **Step 7: 提交**

```bash
git add scripts/ data/ src/nekomata/card/data.py tests/unit/test_data.py
git commit -m "feat: add card meanings YAML (78 cards) and data loader"
```

---

### Task 4: 牌组逻辑（deck.py）

**Files:**
- Create: `src/nekomata/card/deck.py`
- Test: `tests/unit/test_deck.py`

- [ ] **Step 1: 写测试**

```python
# tests/unit/test_deck.py
import random

import pytest

from nekomata.card.deck import Deck
from nekomata.card.types import Arcana, Card


def make_test_cards(n: int = 5) -> list[Card]:
    return [
        Card(
            id=f"test_{i:02d}", name=f"Card {i}", name_zh=f"测试{i}",
            arcana=Arcana.MAJOR, number=i, element="air", astrology="Uranus",
            keywords_upright=("a",), keywords_reversed=("b",),
            meaning_upright="up", meaning_reversed="down",
        )
        for i in range(n)
    ]


def test_deck_has_78_cards():
    deck = Deck()
    assert deck.remaining == 78


def test_deck_draw_reduces_count():
    deck = Deck(make_test_cards(5))
    deck.draw()
    assert deck.remaining == 4


def test_deck_draw_returns_card_and_reversal():
    deck = Deck(make_test_cards(5))
    card, is_reversed = deck.draw()
    assert isinstance(card, Card)
    assert isinstance(is_reversed, bool)


def test_deck_draw_all_exhausts():
    cards = make_test_cards(5)
    deck = Deck(cards)
    drawn = []
    for _ in range(5):
        drawn.append(deck.draw())
    assert deck.remaining == 0
    with pytest.raises(IndexError):
        deck.draw()


def test_deck_draw_no_duplicates():
    deck = Deck()
    drawn_ids = set()
    for _ in range(78):
        card, _ = deck.draw()
        assert card.id not in drawn_ids
        drawn_ids.add(card.id)
    assert len(drawn_ids) == 78


def test_deck_shuffle_changes_order():
    cards = make_test_cards(20)
    random.seed(42)
    deck1 = Deck(cards)
    deck1.shuffle()
    order1 = [deck1.draw()[0].id for _ in range(20)]
    random.seed(99)
    deck2 = Deck(cards)
    deck2.shuffle()
    order2 = [deck2.draw()[0].id for _ in range(20)]
    assert order1 != order2


def test_deck_reversal_probability():
    deck = Deck(make_test_cards(1000))
    deck.shuffle()
    reversed_count = sum(1 for _ in range(1000) if deck.draw()[1])
    assert 400 < reversed_count < 600  # ~50% with margin


def test_deck_reset():
    cards = make_test_cards(5)
    deck = Deck(cards)
    deck.draw()
    deck.draw()
    assert deck.remaining == 3
    deck.reset()
    assert deck.remaining == 5
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/test_deck.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 deck.py**

```python
# src/nekomata/card/deck.py
from __future__ import annotations

import random

from nekomata.card.types import Card


class Deck:
    def __init__(self, cards: list[Card] | None = None):
        if cards is None:
            from nekomata.card.data import load_all_cards
            cards = load_all_cards()
        self._original = list(cards)
        self._cards = list(cards)

    @property
    def remaining(self) -> int:
        return len(self._cards)

    def shuffle(self) -> None:
        random.shuffle(self._cards)

    def draw(self, reversal_prob: float = 0.5) -> tuple[Card, bool]:
        if not self._cards:
            raise IndexError("No cards left in deck")
        card = self._cards.pop()
        is_reversed = random.random() < reversal_prob
        return card, is_reversed

    def reset(self) -> None:
        self._cards = list(self._original)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/test_deck.py -v`
Expected: 8 passed

- [ ] **Step 5: 提交**

```bash
git add src/nekomata/card/deck.py tests/unit/test_deck.py
git commit -m "feat: add Deck with shuffle, draw, reversal, and reset"
```

---

### Task 5: 牌阵系统（base + single + three_card）

**Files:**
- Create: `src/nekomata/spread/base.py`
- Create: `src/nekomata/spread/single.py`
- Create: `src/nekomata/spread/three_card.py`
- Test: `tests/unit/test_spread.py`

- [ ] **Step 1: 写测试**

```python
# tests/unit/test_spread.py
import pytest

from nekomata.card.deck import Deck
from nekomata.card.types import Card, Arcana
from nekomata.spread.base import Spread
from nekomata.spread.single import SingleCardSpread
from nekomata.spread.three_card import PastPresentFuture, SituationActionResult


def make_deck(n: int = 10) -> Deck:
    cards = [
        Card(
            id=f"s_{i:02d}", name=f"S{i}", name_zh=f"牌{i}",
            arcana=Arcana.MAJOR, number=i, element="air", astrology="Uranus",
            keywords_upright=("a",), keywords_reversed=("b",),
            meaning_upright="up", meaning_reversed="down",
        )
        for i in range(n)
    ]
    return Deck(cards)


class TestSingleCardSpread:
    def test_name(self):
        s = SingleCardSpread()
        assert s.name == "Single Card"
        assert s.name_zh == "单牌"

    def test_position_count(self):
        s = SingleCardSpread()
        assert len(s.positions) == 1

    def test_draw(self):
        spread = SingleCardSpread()
        deck = make_deck()
        spread.draw(deck)
        assert len(spread.drawn_cards) == 1
        assert spread.drawn_cards[0].position.name_zh == "今日指引"
        assert deck.remaining == 9


class TestThreeCardSpreads:
    def test_past_present_future(self):
        s = PastPresentFuture()
        assert len(s.positions) == 3
        assert s.positions[0].name_zh == "过去"
        assert s.positions[1].name_zh == "现在"
        assert s.positions[2].name_zh == "未来"

    def test_situation_action_result(self):
        s = SituationActionResult()
        assert len(s.positions) == 3
        assert s.positions[0].name_zh == "处境"
        assert s.positions[1].name_zh == "行动"
        assert s.positions[2].name_zh == "结果"

    def test_draw_three(self):
        spread = PastPresentFuture()
        deck = make_deck()
        spread.draw(deck)
        assert len(spread.drawn_cards) == 3
        assert deck.remaining == 7


def test_draw_populates_drawn_cards():
    spread = SingleCardSpread()
    deck = make_deck()
    assert len(spread.drawn_cards) == 0
    spread.draw(deck)
    dc = spread.drawn_cards
    assert len(dc) == 1
    assert dc[0].card is not None
    assert dc[0].position is not None


def test_redraw_clears_previous():
    spread = SingleCardSpread()
    deck = make_deck(20)
    spread.draw(deck)
    first = spread.drawn_cards[0].card.id
    spread.draw(deck)
    second = spread.drawn_cards[0].card.id
    assert first != second
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/test_spread.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 base.py**

```python
# src/nekomata/spread/base.py
from __future__ import annotations

from nekomata.card.deck import Deck
from nekomata.card.types import DrawnCard, Position


class Spread:
    name: str = ""
    name_zh: str = ""

    def __init__(self) -> None:
        self._drawn_cards: list[DrawnCard] = []
        self._positions: list[Position] = []

    @property
    def positions(self) -> list[Position]:
        return self._positions

    @property
    def drawn_cards(self) -> list[DrawnCard]:
        return list(self._drawn_cards)

    def draw(self, deck: Deck) -> None:
        self._drawn_cards.clear()
        for pos in self._positions:
            card, is_reversed = deck.draw()
            self._drawn_cards.append(
                DrawnCard(card=card, position=pos, is_reversed=is_reversed)
            )
```

- [ ] **Step 4: 实现 single.py**

```python
# src/nekomata/spread/single.py
from __future__ import annotations

from nekomata.card.types import Position
from nekomata.spread.base import Spread


class SingleCardSpread(Spread):
    name = "Single Card"
    name_zh = "单牌"

    def __init__(self) -> None:
        super().__init__()
        self._positions = [
            Position(name="Daily Guidance", name_zh="今日指引", description="今日的灵感与指引"),
        ]
```

- [ ] **Step 5: 实现 three_card.py**

```python
# src/nekomata/spread/three_card.py
from __future__ import annotations

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
```

- [ ] **Step 6: 运行测试确认通过**

Run: `pytest tests/unit/test_spread.py -v`
Expected: 9 passed

- [ ] **Step 7: 提交**

```bash
git add src/nekomata/spread/ tests/unit/test_spread.py
git commit -m "feat: add Spread system with single card and three-card spreads"
```

---

### Task 6: 文字牌面渲染 + 卡牌预览（card_renderer.py）

**Files:**
- Create: `src/nekomata/render/card_renderer.py`
- Test: `tests/unit/test_renderer.py`

- [ ] **Step 1: 写测试**

```python
# tests/unit/test_renderer.py
from pathlib import Path

from rich.panel import Panel

from nekomata.card.types import Arcana, Card, DrawnCard, Position
from nekomata.render.card_renderer import (
    render_card_text,
    render_card_detail,
    render_reading_summary,
    get_preview_path,
)


def make_drawn(reversed: bool = False) -> DrawnCard:
    card = Card(
        id="major_00", name="The Fool", name_zh="愚者",
        arcana=Arcana.MAJOR, number=0, element="air", astrology="Uranus",
        keywords_upright=("新开始", "天真", "冒险"),
        keywords_reversed=("鲁莽", "冒失", "停滞"),
        meaning_upright="一段新旅程的开始。",
        meaning_reversed="过于鲁莽。",
    )
    pos = Position(name="Daily", name_zh="今日指引", description="今日灵感")
    return DrawnCard(card=card, position=pos, is_reversed=reversed)


def test_render_card_text_returns_panel():
    dc = make_drawn()
    result = render_card_text(dc)
    assert isinstance(result, Panel)


def test_render_card_text_contains_name():
    dc = make_drawn()
    result = render_card_text(dc)
    renderable_str = str(result.renderable)
    assert "愚者" in renderable_str
    assert "The Fool" in renderable_str


def test_render_card_text_reversed():
    dc = make_drawn(reversed=True)
    result = render_card_text(dc)
    renderable_str = str(result.renderable)
    assert "逆位" in renderable_str


def test_render_card_text_upright():
    dc = make_drawn(reversed=False)
    result = render_card_text(dc)
    renderable_str = str(result.renderable)
    assert "正位" in renderable_str


def test_render_card_text_position_in_title():
    dc = make_drawn()
    result = render_card_text(dc)
    assert "今日指引" in str(result.title)


def test_render_reading_summary():
    cards = [make_drawn(False), make_drawn(True)]
    result = render_reading_summary(cards, "今天运势如何？")
    assert isinstance(result, Panel)


# --- 预览渲染测试 ---

def test_render_card_detail_returns_panel():
    dc = make_drawn()
    result = render_card_detail(dc)
    assert isinstance(result, Panel)


def test_render_card_detail_shows_full_info():
    dc = make_drawn()
    result = render_card_detail(dc)
    s = str(result.renderable)
    assert "愚者" in s
    assert "air" in s
    assert "Uranus" in s
    assert "新开始" in s
    assert "鲁莽" in s
    assert "一段新旅程的开始" in s


def test_render_card_detail_reversed_shows_reversed_info():
    dc = make_drawn(reversed=True)
    result = render_card_detail(dc)
    s = str(result.renderable)
    assert "逆位" in s
    assert "过于鲁莽" in s


def test_get_preview_path():
    card = Card(
        id="major_00", name="The Fool", name_zh="愚者",
        arcana=Arcana.MAJOR, number=0, element="air", astrology="Uranus",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_00.png"),
    )
    assert get_preview_path(card) == Path("assets/cards/major/major_00_detail.png")


def test_get_preview_path_no_image():
    card = Card(
        id="major_00", name="The Fool", name_zh="愚者",
        arcana=Arcana.MAJOR, number=0, element="air", astrology="Uranus",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
    )
    assert get_preview_path(card) is None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/test_renderer.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 card_renderer.py**

```python
# src/nekomata/render/card_renderer.py
from __future__ import annotations

from pathlib import Path

from rich.panel import Panel
from rich.text import Text

from nekomata.card.types import Card, DrawnCard


def get_preview_path(card: Card) -> Path | None:
    """根据 card.image_path 推导预览图路径（{_id}_detail.png）。"""
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
    """卡牌预览详情：展示正逆位全部信息、元素、星座等。Phase 2 可在此处叠加 128×192 PNG。"""
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
        title=f"🔍 {drawn.position.name_zh} — {card.name_zh}",
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/test_renderer.py -v`
Expected: 11 passed

- [ ] **Step 5: 提交**

```bash
git add src/nekomata/render/card_renderer.py tests/unit/test_renderer.py
git commit -m "feat: add text card renderer with detail preview and preview path helper"
```

---

### Task 7: 配置管理（config.py）

**Files:**
- Create: `src/nekomata/storage/config.py`
- Create: `config.toml`
- Test: `tests/unit/test_config.py`

- [ ] **Step 1: 写测试**

```python
# tests/unit/test_config.py
import tomllib
from pathlib import Path

from nekomata.storage.config import AppConfig


def test_default_config():
    config = AppConfig()
    assert config.ai_backend == "template"
    assert config.display_animation is True
    assert config.reversal_prob == 0.5


def test_load_from_file(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        '[ai]\nbackend = "ollama"\nmodel = "llama3"\n\n'
        '[display]\nanimation = false\n'
        "[reversal]\nprobability = 0.3\n",
        encoding="utf-8",
    )
    config = AppConfig.load(config_file)
    assert config.ai_backend == "ollama"
    assert config.ai_model == "llama3"
    assert config.display_animation is False
    assert config.reversal_prob == 0.3


def test_load_missing_file_uses_defaults(tmp_path: Path):
    config = AppConfig.load(tmp_path / "nonexistent.toml")
    assert config.ai_backend == "template"


def test_load_partial_config(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('[ai]\nbackend = "openai_compatible"\n', encoding="utf-8")
    config = AppConfig.load(config_file)
    assert config.ai_backend == "openai_compatible"
    assert config.display_animation is True  # default preserved
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/test_config.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 config.py**

```python
# src/nekomata/storage/config.py
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    ai_backend: str = "template"
    ai_model: str = ""
    ai_base_url: str = "http://localhost:11434"
    ai_api_key: str | None = None
    ai_timeout: float = 60.0
    ai_style: str = "mystical"
    ai_max_retries: int = 2
    ai_fallback: bool = True
    display_animation: bool = True
    display_theme: str = "dark"
    reversal_prob: float = 0.5

    @classmethod
    def load(cls, path: Path | None = None) -> AppConfig:
        defaults = cls()
        if path is None:
            path = Path("config.toml")
        if not path.exists():
            return defaults
        with open(path, "rb") as f:
            data = tomllib.load(f)

        ai = data.get("ai", {})
        display = data.get("display", {})
        reversal = data.get("reversal", {})

        return cls(
            ai_backend=ai.get("backend", defaults.ai_backend),
            ai_model=ai.get("model", defaults.ai_model),
            ai_base_url=ai.get("base_url", defaults.ai_base_url),
            ai_api_key=ai.get("api_key", defaults.ai_api_key),
            ai_timeout=ai.get("timeout", defaults.ai_timeout),
            ai_style=ai.get("style", defaults.ai_style),
            ai_max_retries=ai.get("max_retries", defaults.ai_max_retries),
            ai_fallback=ai.get("fallback_to_template", defaults.ai_fallback),
            display_animation=display.get("animation", defaults.display_animation),
            display_theme=display.get("theme", defaults.display_theme),
            reversal_prob=reversal.get("probability", defaults.reversal_prob),
        )
```

- [ ] **Step 4: 创建默认 config.toml**

```toml
# config.toml — Nekomata 用户配置

[ai]
backend = "template"            # template | ollama | openai_compatible
model = ""
base_url = "http://localhost:11434"
api_key = ""
timeout = 60.0
style = "mystical"              # mystical | warm | direct
max_retries = 2
fallback_to_template = true

[display]
animation = true
theme = "dark"

[reversal]
probability = 0.5
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/unit/test_config.py -v`
Expected: 4 passed

- [ ] **Step 6: 提交**

```bash
git add src/nekomata/storage/config.py config.toml tests/unit/test_config.py
git commit -m "feat: add TOML config with AI backend, display, and reversal settings"
```

---

### Task 8: 日志存储（journal.py）

**Files:**
- Create: `src/nekomata/storage/journal.py`
- Test: `tests/unit/test_journal.py`

- [ ] **Step 1: 写测试**

```python
# tests/unit/test_journal.py
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from nekomata.card.types import Arcana, Card, DrawnCard, Position, Reading
from nekomata.storage.journal import Journal


def make_reading(question: str = "测试问题") -> Reading:
    card = Card(
        id="major_00", name="The Fool", name_zh="愚者",
        arcana=Arcana.MAJOR, number=0, element="air", astrology="Uranus",
        keywords_upright=("新开始",), keywords_reversed=("鲁莽",),
        meaning_upright="新旅程", meaning_reversed="鲁莽",
    )
    pos = Position(name="Daily", name_zh="今日指引", description="今日灵感")
    return Reading(
        id=uuid4(),
        timestamp=datetime.now(),
        question=question,
        spread_name="Single Card",
        spread_name_zh="单牌",
        drawn_cards=[DrawnCard(card=card, position=pos, is_reversed=False)],
        interpretation="这是一个新的开始。",
    )


def test_save_and_load(tmp_path: Path):
    journal = Journal(tmp_path / "test.db")
    reading = make_reading()
    journal.save(reading)

    loaded = journal.load_recent(limit=1)
    assert len(loaded) == 1
    assert loaded[0].question == "测试问题"
    assert loaded[0].spread_name == "Single Card"
    assert loaded[0].interpretation == "这是一个新的开始。"


def test_load_recent_order(tmp_path: Path):
    journal = Journal(tmp_path / "test.db")
    for i in range(5):
        journal.save(make_reading(f"问题{i}"))
    loaded = journal.load_recent(limit=3)
    assert len(loaded) == 3
    assert loaded[0].question == "问题4"  # most recent first


def test_save_multiple_drawn_cards(tmp_path: Path):
    journal = Journal(tmp_path / "test.db")
    cards = [
        Card(
            id=f"major_{i:02d}", name=f"Card{i}", name_zh=f"牌{i}",
            arcana=Arcana.MAJOR, number=i, element="air", astrology="Uranus",
            keywords_upright=("a",), keywords_reversed=("b",),
            meaning_upright="up", meaning_reversed="down",
        )
        for i in range(3)
    ]
    positions = [
        Position("Past", "过去", "过去"),
        Position("Present", "现在", "现在"),
        Position("Future", "未来", "未来"),
    ]
    reading = Reading(
        id=uuid4(), timestamp=datetime.now(), question="三牌阵测试",
        spread_name="Past/Present/Future", spread_name_zh="过去·现在·未来",
        drawn_cards=[
            DrawnCard(card=c, position=p, is_reversed=i == 1)
            for i, (c, p) in enumerate(zip(cards, positions))
        ],
    )
    journal.save(reading)
    loaded = journal.load_recent(limit=1)
    assert len(loaded[0].drawn_cards) == 3
    assert loaded[0].drawn_cards[1].is_reversed is True


def test_init_creates_db(tmp_path: Path):
    db_path = tmp_path / "subdir" / "test.db"
    Journal(db_path)
    assert db_path.exists()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/test_journal.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 journal.py**

```python
# src/nekomata/storage/journal.py
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import UUID

from nekomata.card.types import Arcana, Card, DrawnCard, Position, Reading


class Journal:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()

    def _init_db(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS readings (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                question TEXT NOT NULL,
                spread_name TEXT NOT NULL,
                spread_name_zh TEXT NOT NULL,
                interpretation TEXT,
                cards_json TEXT NOT NULL
            )
        """)

    def save(self, reading: Reading) -> None:
        cards_data = []
        for dc in reading.drawn_cards:
            cards_data.append({
                "card_id": dc.card.id,
                "card_name": dc.card.name,
                "card_name_zh": dc.card.name_zh,
                "card_arcana": dc.card.arcana.value,
                "position_name": dc.position.name,
                "position_name_zh": dc.position.name_zh,
                "position_description": dc.position.description,
                "is_reversed": dc.is_reversed,
                "keywords": list(
                    dc.card.keywords_reversed if dc.is_reversed else dc.card.keywords_upright
                ),
                "meaning": (
                    dc.card.meaning_reversed if dc.is_reversed else dc.card.meaning_upright
                ),
            })
        self._conn.execute(
            "INSERT INTO readings VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                str(reading.id),
                reading.timestamp.isoformat(),
                reading.question,
                reading.spread_name,
                reading.spread_name_zh,
                reading.interpretation,
                json.dumps(cards_data, ensure_ascii=False),
            ),
        )
        self._conn.commit()

    def load_recent(self, limit: int = 10) -> list[Reading]:
        rows = self._conn.execute(
            "SELECT * FROM readings ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        readings = []
        for row in rows:
            id_str, ts_str, question, spread_name, spread_name_zh, interp, cards_json = row
            cards_data = json.loads(cards_json)
            drawn_cards = []
            for cd in cards_data:
                card = Card(
                    id=cd["card_id"],
                    name=cd["card_name"],
                    name_zh=cd["card_name_zh"],
                    arcana=Arcana(cd["card_arcana"]),
                    number=0,
                    element="",
                    astrology="",
                    keywords_upright=tuple(cd["keywords"]),
                    keywords_reversed=tuple(cd["keywords"]),
                    meaning_upright=cd["meaning"],
                    meaning_reversed=cd["meaning"],
                )
                pos = Position(
                    name=cd["position_name"],
                    name_zh=cd["position_name_zh"],
                    description=cd["position_description"],
                )
                drawn_cards.append(DrawnCard(card=card, position=pos, is_reversed=cd["is_reversed"]))
            readings.append(Reading(
                id=UUID(id_str),
                timestamp=datetime.fromisoformat(ts_str),
                question=question,
                spread_name=spread_name,
                spread_name_zh=spread_name_zh,
                drawn_cards=drawn_cards,
                interpretation=interp,
            ))
        return readings
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/test_journal.py -v`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add src/nekomata/storage/journal.py tests/unit/test_journal.py
git commit -m "feat: add Journal with SQLite save/load for readings"
```

---

### Task 9: 模板解读（interpreter.py + prompts.py）

**Files:**
- Create: `src/nekomata/ai/interpreter.py`
- Create: `src/nekomata/ai/prompts.py`
- Test: `tests/unit/test_interpreter.py`

- [ ] **Step 1: 写测试**

```python
# tests/unit/test_interpreter.py
from nekomata.card.types import Arcana, Card, DrawnCard, Position
from nekomata.ai.interpreter import template_interpret


def make_drawn_cards(n: int, reversed_idx: set[int] | None = None) -> list[DrawnCard]:
    reversed_idx = reversed_idx or set()
    result = []
    positions = [
        Position("Past", "过去", "过去的影响"),
        Position("Present", "现在", "当前状况"),
        Position("Future", "未来", "未来发展"),
    ]
    for i in range(n):
        card = Card(
            id=f"major_{i:02d}", name=f"Card{i}", name_zh=f"牌{i}",
            arcana=Arcana.MAJOR, number=i, element="air", astrology="Uranus",
            keywords_upright=(f"正位关键词{i}",),
            keywords_reversed=(f"逆位关键词{i}",),
            meaning_upright=f"正位含义{i}",
            meaning_reversed=f"逆位含义{i}",
        )
        result.append(DrawnCard(
            card=card, position=positions[i], is_reversed=(i in reversed_idx)
        ))
    return result


def test_template_interpret_contains_question():
    cards = make_drawn_cards(1)
    result = template_interpret(cards, "今天运势如何？")
    assert "今天运势如何？" in result


def test_template_interpret_single_card():
    cards = make_drawn_cards(1)
    result = template_interpret(cards, "test")
    assert "牌0" in result
    assert "正位关键词0" in result


def test_template_interpret_reversed():
    cards = make_drawn_cards(3, reversed_idx={1})
    result = template_interpret(cards, "test")
    assert "逆位" in result
    assert "逆位关键词1" in result


def test_template_interpret_three_cards():
    cards = make_drawn_cards(3)
    result = template_interpret(cards, "三牌阵测试")
    assert "过去" in result
    assert "现在" in result
    assert "未来" in result
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/test_interpreter.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 prompts.py**

```python
# src/nekomata/ai/prompts.py
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
```

- [ ] **Step 4: 实现 interpreter.py**

```python
# src/nekomata/ai/interpreter.py
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
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/unit/test_interpreter.py -v`
Expected: 4 passed

- [ ] **Step 6: 提交**

```bash
git add src/nekomata/ai/ tests/unit/test_interpreter.py
git commit -m "feat: add template-based card interpretation"
```

---

### Task 10: Textual App + 首页（app.py + home.py）

**Files:**
- Create: `src/nekomata/app.py`
- Create: `src/nekomata/screens/home.py`
- Test: `tests/integration/test_app.py`

- [ ] **Step 1: 写测试**

```python
# tests/integration/test_app.py
import pytest

from nekomata.app import NekomataApp


@pytest.mark.asyncio
async def test_app_starts():
    app = NekomataApp()
    async with app.run_test() as pilot:
        assert app.screen is not None


@pytest.mark.asyncio
async def test_home_screen_has_start_button():
    app = NekomataApp()
    async with app.run_test() as pilot:
        start_btn = app.screen.query_one("#start-reading")
        assert start_btn is not None


@pytest.mark.asyncio
async def test_home_screen_has_title():
    app = NekomataApp()
    async with app.run_test() as pilot:
        title = app.screen.query_one("#title")
        assert title is not None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/integration/test_app.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 app.py**

```python
# src/nekomata/app.py
from __future__ import annotations

from textual.app import App

from nekomata.screens.home import HomeScreen


class NekomataApp(App):
    TITLE = "🐱 Nekomata — 猫又塔罗"
    CSS_PATH = None

    def __init__(self) -> None:
        super().__init__()
        self.question: str = ""
        self.spread_name: str = ""
        self.spread_name_zh: str = ""

    def on_mount(self) -> None:
        self.push_screen(HomeScreen())


def main() -> None:
    app = NekomataApp()
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 实现 home.py**

```python
# src/nekomata/screens/home.py
from __future__ import annotations

from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static


BANNER = r"""
  ███╗   ██╗███████╗ ██████╗ ███╗   ██╗
  ████╗  ██║██╔════╝██╔═══██╗████╗  ██║
  ██╔██╗ ██║█████╗  ██║   ██║██╔██╗ ██║
  ██║╚██╗██║██╔══╝  ██║   ██║██║╚██╗██║
  ██║ ╚████║███████╗╚██████╔╝██║ ╚████║
  ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
        🐱 猫又塔罗 · 像素风猫咪占卜 🌙
"""


class HomeScreen(Screen):
    DEFAULT_CSS = """
    HomeScreen {
        align: center middle;
    }
    HomeScreen #banner {
        text-align: center;
        margin-bottom: 2;
    }
    HomeScreen Vertical {
        width: auto;
        height: auto;
    }
    HomeScreen Button {
        width: 30;
        margin-bottom: 1;
    }
    """

    def compose(self):
        with Center():
            yield Static(BANNER, id="title")
            with Vertical():
                yield Button("🔮 开始占卜", id="start-reading", variant="primary")
                yield Button("📚 牌库浏览", id="card-browser")
                yield Button("📓 历史记录", id="journal")
                yield Button("❌ 退出", id="quit")
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/integration/test_app.py -v`
Expected: 3 passed

- [ ] **Step 6: 提交**

```bash
git add src/nekomata/app.py src/nekomata/screens/home.py tests/integration/test_app.py
git commit -m "feat: add Textual app entry and home screen with banner"
```

---

### Task 11: 选牌阵 Screen（spread_select.py）

**Files:**
- Create: `src/nekomata/screens/spread_select.py`
- Modify: `src/nekomata/screens/home.py`（添加导航）
- Modify: `tests/integration/test_app.py`

- [ ] **Step 1: 写测试**

```python
# 添加到 tests/integration/test_app.py

@pytest.mark.asyncio
async def test_navigate_to_spread_select():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#start-reading")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)


@pytest.mark.asyncio
async def test_spread_select_has_options():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#start-reading")
        await pilot.pause()
        buttons = app.screen.query("Button")
        ids = [b.id for b in buttons if b.id]
        assert "spread-single" in ids
        assert "spread-past-present-future" in ids
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/integration/test_app.py::test_navigate_to_spread_select -v`
Expected: FAIL

- [ ] **Step 3: 实现 spread_select.py**

```python
# src/nekomata/screens/spread_select.py
from __future__ import annotations

from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static


SPREADS = [
    ("single", "spread-single", "单牌", "每日灵感"),
    ("past_present_future", "spread-past-present-future", "过去·现在·未来", "时间线三牌阵"),
    ("situation_action_result", "spread-situation-action-result", "处境·行动·结果", "问题分析"),
]


class SpreadSelectScreen(Screen):
    DEFAULT_CSS = """
    SpreadSelectScreen {
        align: center middle;
    }
    SpreadSelectScreen #prompt {
        text-align: center;
        margin-bottom: 2;
    }
    SpreadSelectScreen Button {
        width: 40;
        margin-bottom: 1;
    }
    """

    def compose(self):
        with Center():
            yield Static("请选择牌阵：", id="prompt")
            with Vertical():
                for key, btn_id, name, desc in SPREADS:
                    yield Button(f"{name} — {desc}", id=btn_id)
                yield Button("↩ 返回", id="back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        for key, btn_id, name, desc in SPREADS:
            if event.button.id == btn_id:
                self.app.dismiss(key)
                return
```

- [ ] **Step 4: 更新 home.py 添加导航**

```python
# 在 home.py 的 HomeScreen 类中添加：
    def on_button_pressed(self, event: Button.Pressed) -> None:
        from nekomata.screens.spread_select import SpreadSelectScreen

        match event.button.id:
            case "start-reading":
                self.app.push_screen(SpreadSelectScreen(), callback=self._on_spread_selected)
            case "quit":
                self.app.exit()

    def _on_spread_selected(self, spread_key: str) -> None:
        from nekomata.screens.question import QuestionScreen
        self.app.push_screen(QuestionScreen(spread_key))
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/integration/test_app.py -v`
Expected: 5 passed

- [ ] **Step 6: 提交**

```bash
git add src/nekomata/screens/spread_select.py src/nekomata/screens/home.py tests/integration/test_app.py
git commit -m "feat: add spread selection screen with navigation"
```

---

### Task 12: 问题输入 Screen（question.py）

**Files:**
- Create: `src/nekomata/screens/question.py`
- Test: 修改 `tests/integration/test_app.py`

- [ ] **Step 1: 写测试**

```python
# 添加到 tests/integration/test_app.py

@pytest.mark.asyncio
async def test_question_screen_has_input():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#start-reading")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.question import QuestionScreen
        assert isinstance(app.screen, QuestionScreen)
        inp = app.screen.query_one("#question-input")
        assert inp is not None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/integration/test_app.py::test_question_screen_has_input -v`
Expected: FAIL

- [ ] **Step 3: 实现 question.py**

```python
# src/nekomata/screens/question.py
from __future__ import annotations

from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static


class QuestionScreen(Screen):
    DEFAULT_CSS = """
    QuestionScreen {
        align: center middle;
    }
    QuestionScreen #prompt {
        text-align: center;
        margin-bottom: 2;
    }
    QuestionScreen Input {
        width: 50;
        margin-bottom: 1;
    }
    QuestionScreen Button {
        width: 20;
        margin-bottom: 1;
    }
    """

    def __init__(self, spread_key: str) -> None:
        super().__init__()
        self.spread_key = spread_key

    def compose(self):
        with Center():
            yield Static("请输入你的问题：", id="prompt")
            with Vertical():
                yield Input(placeholder="例如：今天运势如何？", id="question-input")
                yield Button("🔮 开始抽牌", id="submit", variant="primary")
                yield Button("↩ 返回", id="back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id == "submit":
            inp = self.query_one("#question-input", Input)
            question = inp.value.strip()
            if not question:
                question = "请为我指引方向。"
            self.app.question = question
            self.app.spread_key = self.spread_key
            from nekomata.screens.reading import ReadingScreen
            self.app.push_screen(ReadingScreen(self.spread_key, question))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "question-input":
            question = event.value.strip() or "请为我指引方向。"
            self.app.question = question
            self.app.spread_key = self.spread_key
            from nekomata.screens.reading import ReadingScreen
            self.app.push_screen(ReadingScreen(self.spread_key, question))
```

注意：需要给 `NekomataApp` 添加 `spread_key` 属性。

- [ ] **Step 4: 更新 app.py 添加 spread_key**

在 `NekomataApp.__init__` 中添加 `self.spread_key: str = ""`。

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/integration/test_app.py -v`
Expected: 6 passed

- [ ] **Step 6: 提交**

```bash
git add src/nekomata/screens/question.py src/nekomata/app.py tests/integration/test_app.py
git commit -m "feat: add question input screen with text input"
```

---

### Task 13: 揭牌展示 Screen + 卡牌预览（reading.py）

**Files:**
- Create: `src/nekomata/screens/reading.py`
- Test: 修改 `tests/integration/test_app.py`

- [ ] **Step 1: 写测试**

```python
# 添加到 tests/integration/test_app.py

@pytest.mark.asyncio
async def test_reading_screen_shows_cards():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#start-reading")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        q_inp = app.screen.query_one("#question-input")
        q_inp.value = "测试问题"
        await pilot.click("#submit")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)


@pytest.mark.asyncio
async def test_reading_screen_card_preview():
    """点击卡牌可显示预览详情面板。"""
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#start-reading")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        q_inp = app.screen.query_one("#question-input")
        q_inp.value = "预览测试"
        await pilot.click("#submit")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)
        preview = app.screen.query_one("#card-preview")
        assert preview is not None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/integration/test_app.py::test_reading_screen_shows_cards -v`
Expected: FAIL

- [ ] **Step 3: 实现 reading.py**

左右分栏布局：左侧牌面列表（可点击），右侧预览详情面板。

```python
# src/nekomata/screens/reading.py
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, VerticalScroll, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Static

from nekomata.card.deck import Deck
from nekomata.card.types import DrawnCard
from nekomata.render.card_renderer import render_card_text, render_card_detail
from nekomata.spread.base import Spread
from nekomata.spread.single import SingleCardSpread
from nekomata.spread.three_card import PastPresentFuture, SituationActionResult


def get_spread(key: str) -> Spread:
    spreads = {
        "single": SingleCardSpread,
        "past_present_future": PastPresentFuture,
        "situation_action_result": SituationActionResult,
    }
    return spreads[key]()


class CardWidget(Static):
    """可点击的卡牌缩略组件。"""

    class Selected(Message):
        def __init__(self, drawn_card: DrawnCard) -> None:
            super().__init__()
            self.drawn_card = drawn_card

    def __init__(self, drawn: DrawnCard) -> None:
        super().__init__(render_card_text(drawn))
        self._drawn = drawn

    def on_click(self) -> None:
        self.post_message(self.Selected(self._drawn))


class ReadingScreen(Screen):
    DEFAULT_CSS = """
    ReadingScreen {
        align: center top;
    }
    ReadingScreen #question-display {
        text-align: center;
        margin: 1 0;
    }
    ReadingScreen #main-area {
        height: 1fr;
    }
    ReadingScreen #cards-container {
        width: 1fr;
        height: 1fr;
    }
    ReadingScreen #card-preview {
        width: 1fr;
        height: 1fr;
        border: round $primary;
        padding: 1 2;
    }
    ReadingScreen #actions {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    ReadingScreen Button {
        width: 24;
        margin: 0 1;
    }
    """

    def __init__(self, spread_key: str, question: str) -> None:
        super().__init__()
        self._spread_key = spread_key
        self._question = question
        self._drawn_cards: list[DrawnCard] = []

    def compose(self) -> ComposeResult:
        yield Static(f"🔮 {self._question}", id="question-display")
        with Horizontal(id="main-area"):
            with VerticalScroll(id="cards-container"):
                pass
            with Vertical(id="card-preview"):
                yield Static("点击左侧卡牌查看详情", id="preview-placeholder")
        with Center(id="actions"):
            yield Button("📖 解读", id="interpret", variant="primary")
            yield Button("🏠 返回首页", id="home")

    def on_mount(self) -> None:
        spread = get_spread(self._spread_key)
        deck = Deck()
        deck.shuffle()
        spread.draw(deck)
        self._drawn_cards = spread.drawn_cards

        container = self.query_one("#cards-container")
        for dc in self._drawn_cards:
            container.mount(CardWidget(dc))

        self.app.spread_name = spread.name
        self.app.spread_name_zh = spread.name_zh

    def on_card_widget_selected(self, event: CardWidget.Selected) -> None:
        preview = self.query_one("#card-preview")
        preview.remove_children()
        preview.mount(Static(render_card_detail(event.drawn_card)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "home":
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
        elif event.button.id == "interpret":
            from nekomata.ai.interpreter import template_interpret
            from nekomata.screens.interpretation import InterpretationScreen
            interp = template_interpret(self._drawn_cards, self._question)
            self.app.push_screen(InterpretationScreen(interp, self._drawn_cards, self._question))
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/integration/test_app.py -v`
Expected: 8 passed

- [ ] **Step 5: 提交**

```bash
git add src/nekomata/screens/reading.py tests/integration/test_app.py
git commit -m "feat: add reading screen with card selection and detail preview panel"
```

---

### Task 14: 解读展示 Screen（interpretation.py）

**Files:**
- Create: `src/nekomata/screens/interpretation.py`
- Test: 修改 `tests/integration/test_app.py`

- [ ] **Step 1: 写测试**

```python
# 添加到 tests/integration/test_app.py

@pytest.mark.asyncio
async def test_full_flow_to_interpretation():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#start-reading")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        q_inp = app.screen.query_one("#question-input")
        q_inp.value = "完整流程测试"
        await pilot.click("#submit")
        await pilot.pause()
        await pilot.click("#interpret")
        await pilot.pause()
        from nekomata.screens.interpretation import InterpretationScreen
        assert isinstance(app.screen, InterpretationScreen)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/integration/test_app.py::test_full_flow_to_interpretation -v`
Expected: FAIL

- [ ] **Step 3: 实现 interpretation.py**

```python
# src/nekomata/screens/interpretation.py
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from textual.containers import Center, Vertical
from textual.screen import Screen
from pathlib import Path

from textual.widgets import Button, Static
from rich.markdown import Markdown

from nekomata.card.types import Reading
from nekomata.storage.journal import Journal


class InterpretationScreen(Screen):
    DEFAULT_CSS = """
    InterpretationScreen {
        align: center top;
    }
    InterpretationScreen #interp-content {
        margin: 1 2;
    }
    InterpretationScreen #actions {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    InterpretationScreen Button {
        width: 24;
        margin: 0 1;
    }
    """

    def __init__(
        self,
        interpretation: str,
        drawn_cards: list,
        question: str,
    ) -> None:
        super().__init__()
        self._interpretation = interpretation
        self._drawn_cards = drawn_cards
        self._question = question
        self._saved = False

    def compose(self):
        with Vertical():
            yield Static(Markdown(self._interpretation), id="interp-content")
            with Center(id="actions"):
                yield Button("💾 保存记录", id="save", variant="success")
                yield Button("🏠 返回首页", id="home")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "home":
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
        elif event.button.id == "save" and not self._saved:
            reading = Reading(
                id=uuid4(),
                timestamp=datetime.now(),
                question=self._question,
                spread_name=self.app.spread_name,
                spread_name_zh=self.app.spread_name_zh,
                drawn_cards=self._drawn_cards,
                interpretation=self._interpretation,
            )
            journal = Journal(Path("data/journal.db"))
            journal.save(reading)
            self._saved = True
            save_btn = self.query_one("#save")
            save_btn.label = "已保存 ✓"
            save_btn.disabled = True
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/integration/test_app.py -v`
Expected: 8 passed

- [ ] **Step 5: 提交**

```bash
git add src/nekomata/screens/interpretation.py tests/integration/test_app.py
git commit -m "feat: add interpretation screen with save-to-journal"
```

---

### Task 15: 端到端集成测试

**Files:**
- Create: `tests/integration/test_flow.py`

- [ ] **Step 1: 写完整流程测试**

```python
# tests/integration/test_flow.py
"""端到端集成测试：完整的占卜流程。"""
import pytest

from nekomata.app import NekomataApp


@pytest.mark.asyncio
async def test_single_card_full_flow():
    """测试完整单牌占卜流程：首页 → 选牌阵 → 输入问题 → 揭牌 → 解读。"""
    app = NekomataApp()
    async with app.run_test() as pilot:
        # 1. 首页存在
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)

        # 2. 点击开始占卜
        await pilot.click("#start-reading")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)

        # 3. 选择单牌
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.question import QuestionScreen
        assert isinstance(app.screen, QuestionScreen)

        # 4. 输入问题
        q_inp = app.screen.query_one("#question-input")
        q_inp.value = "今天适合做什么？"
        await pilot.click("#submit")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)

        # 5. 解读
        await pilot.click("#interpret")
        await pilot.pause()
        from nekomata.screens.interpretation import InterpretationScreen
        assert isinstance(app.screen, InterpretationScreen)


@pytest.mark.asyncio
async def test_three_card_flow():
    """测试三牌阵流程。"""
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#start-reading")
        await pilot.pause()
        await pilot.click("#spread-past-present-future")
        await pilot.pause()
        q_inp = app.screen.query_one("#question-input")
        q_inp.value = "未来发展如何？"
        await pilot.click("#submit")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)
        # 三牌阵应该显示3张牌
        cards = app.screen.query("Static")
        assert len(cards) >= 3


@pytest.mark.asyncio
async def test_back_navigation():
    """测试返回导航。"""
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#start-reading")
        await pilot.pause()
        await pilot.click("#back")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)
```

- [ ] **Step 2: 运行全部测试**

Run: `pytest tests/ -v`
Expected: 所有测试通过（单元测试 + 集成测试）

- [ ] **Step 3: 验证 CLI 启动**

Run: `nekomata`
Expected: TUI 应用启动，显示猫又塔罗标题和菜单

按 `Ctrl+C` 退出。

- [ ] **Step 4: 提交**

```bash
git add tests/integration/test_flow.py
git commit -m "test: add end-to-end integration tests for full reading flow"
```

---

## 自审清单

### 1. 架构文档覆盖

| 需求 | 对应任务 |
|------|---------|
| 78 张牌数据模型 | Task 2 (types.py) + Task 3 (YAML + data.py) |
| 牌组逻辑（洗牌、抽牌、逆位） | Task 4 (deck.py) |
| 牌阵（单牌、三牌阵） | Task 5 (spread/) |
| 牌面渲染（文字模式）+ 预览详情 | Task 6 (card_renderer.py) |
| 预览图路径推导（`_detail.png`） | Task 6 (get_preview_path) |
| 用户配置 | Task 7 (config.py + config.toml) |
| Journal 存储 | Task 8 (journal.py) |
| AI 解牌（模板降级） | Task 9 (interpreter.py) |
| Textual Screen 流程 | Task 10-14 (app + screens) |
| 卡牌选中 + 预览面板 | Task 13 (reading.py, 左右分栏) |
| 端到端集成 | Task 15 |
| 凯尔特十字牌阵 | Phase 3（不在 MVP 范围） |
| 像素牌面渲染（64×96 + 128×192 PNG） | Phase 2（框架已在 Task 6 预留） |
| 动画效果 | Phase 3（不在 MVP 范围） |
| AI 后端集成 | Phase 4（不在 MVP 范围） |
| 牌库浏览 Screen | Phase 3（不在 MVP 范围） |
| Journal Screen | Phase 5（不在 MVP 范围） |

### 2. 类型一致性检查

- `Card.keywords_upright/keywords_reversed`：全部使用 `tuple[str, ...]`（types.py 定义，data.py 转换，renderer 使用） ✅
- `DrawnCard`：组合模式持有 `Card` + `Position`，非继承 ✅
- `Spread.drawn_cards`：返回 `list[DrawnCard]`（base.py 定义，reading.py 使用） ✅
- `Deck.draw()`：返回 `tuple[Card, bool]`（deck.py 定义，spread base 使用） ✅
- `Reading.drawn_cards`：类型为 `list[DrawnCard]`（types.py 定义，journal.py 读写） ✅
- `AppConfig.load()`：返回 `AppConfig`（config.py 定义，后续各处使用） ✅
- `get_preview_path(card)` → `Path | None`：从 `card.image_path` 推导 `_detail.png`，Phase 2 data.py 加载时设置 image_path ✅
- `CardWidget.Selected` 消息携带 `DrawnCard`：reading.py 定义 + 消费 ✅

### 3. 占位符扫描

- 所有 Task 步骤均包含具体代码 ✅
- 无 "TBD"、"TODO"、"implement later" ✅
- 无 "类似 Task N" 的引用 ✅
- 无 "添加适当的错误处理" 等模糊描述 ✅
