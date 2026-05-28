# AGENTS.md

## 项目简介

Nekomata 是终端里的像素风猫咪塔罗占卜应用，78 张牌融入猫咪元素，搭配 AI 个性化解牌。

支持四种运行模式：TUI / CLI / Web UI / Desktop。

## 技术栈

Python 3.13+ / Textual / textual-image / Pillow / FastAPI + vanilla JS / PyWebView / urllib（无 AI SDK） / 自研 i18n（en/zh）

## 项目规范

- 渲染按终端尺寸分级：full / medium / compact / preview / text
- 动画用 Textual `offset`/`opacity`，不用 CSS 3D 翻转
- `Card` 是 `frozen=True` 数据类；`DrawnCard` 用组合持有 `Card`，不继承
- AI 客户端基于 urllib，无第三方 SDK
- i18n 从 `data/locales/` 懒加载，`_LazySection` 代理避免 import 时读文件

## 目录结构

```
src/nekomata/
├── app.py              # 入口 + argparse（调度 TUI/CLI/Web）
├── cli.py              # 纯 CLI 模式
├── desktop.py          # PyWebView 原生窗口
├── _paths.py           # 路径解析（dev / PyInstaller frozen）
├── i18n.py             # 国际化（en/zh）
├── clipboard.py        # 跨平台剪贴板
├── card/               # types.py · deck.py · data.py
├── spread/             # base.py · __init__.py（SPREAD_REGISTRY 5 种牌阵）
├── render/             # card_renderer · image_export · terminal · themes · styles · animations
├── ai/                 # interpreter.py（urllib SSE）· prompts.py
├── screens/            # home · spread_select · draw（拆为 8 子模块） · card_browser · setup
├── storage/            # config.py（.neko/ → ~/.neko/ 回退）
└── web/                # server.py（FastAPI） · static/（vanilla JS SPA）

data/
├── card_meanings.yaml  # 78 张牌释义
├── locales/            # en.json · zh.json · spreads_{en,zh}.json
└── prompts/            # system.md · user_template.md · {spread}.md（每牌阵一个）

assets/cards/           # 78 牌 × 3 变体，按 suit 分目录（major/cups/pentacles/swords/wands）
```

## 运行模式

| 模式    | 命令                    | 入口              |
| ------- | ----------------------- | ----------------- |
| TUI     | `nekomata`              | `app.py`          |
| CLI     | `nekomata -c`           | `cli.py`          |
| Web UI  | `nekomata --web`        | `web/server.py`   |
| Desktop | `nekomata-desktop`      | `desktop.py`      |

## Web API

`GET` `/api/cards` `/api/spreads` `/api/theme` `/api/strings` `/api/config`
`POST` `/api/config` `/api/interpret`（SSE） `/api/interpret/followup`（SSE） `/api/export-image`

## 测试

pytest + pytest-asyncio。`conftest.py` 自动创建临时 `.neko/settings.json` 防止 SetupScreen 弹出。TUI 测试用 `app.run_test()` (pilot)，AI 测试用 mock。

---

# 编码行为准则

> 核心原则：宁可多问一句，不要多做一步。

## 1. 动手前先想清楚

**不要假设，不要藏着困惑，把权衡摆出来。**

- 明确说出你的假设。不确定就问。
- 如果有多种理解，列出来让用户选，不要默默挑一个。
- 如果存在更简单的方案，说出来。该反驳时反驳。
- 遇到不清楚的地方，停下来，说清楚哪里不懂，然后问。

## 2. 简单至上

**用最少的代码解决问题，不为假设的未来写代码。**

- 不加没被要求的功能。
- 一次性的代码不做抽象。
- 没人要求的"灵活性"和"可配置性"不加。
- 不可能发生的场景不做错误处理。
- 如果 200 行能缩到 50 行，重写。

问自己："资深工程师会觉得这段代码过度复杂了吗？" 如果会，简化。

## 3. 精准改动

**只改必须改的，只清理自己弄乱的。**

- 不要顺手"优化"旁边的代码、注释或格式。
- 不要重构没坏的东西。
- 匹配现有风格，即使你自己会写得更不一样。
- 注意到无关的废弃代码时，提一句，不要删。

当你的改动产生了废弃代码：

- 移除你的改动导致的无用 import/变量/函数。
- 不要移除之前就存在的废弃代码，除非被要求。

检验标准：每一行改动都应该能追溯到用户的需求。

## 4. 目标驱动执行

**定义成功标准，循环直到验证通过。**

把任务转化为可验证的目标：

- "加验证" → "写非法输入的测试，然后让测试通过"
- "修 bug" → "写一个能复现的测试，然后让它通过"
- "重构 X" → "确保重构前后测试都通过"

多步任务先简述计划：

```
1. [步骤] → 验证: [检查方式]
2. [步骤] → 验证: [检查方式]
3. [步骤] → 验证: [检查方式]
```

成功标准清晰，就能独立迭代。标准模糊（"让它能用"），就得不停确认。

---

# 常见任务

## 修改 UI 文案

1. 编辑 `data/locales/{en,zh}.json`（TUI 和 Web 共享）
2. 牌阵文案改 `spreads_{en,zh}.json`
