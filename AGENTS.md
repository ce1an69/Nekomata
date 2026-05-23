# AGENTS.md — Nekomata 项目指南

## 项目简介

Nekomata（猫又）是终端里的像素风猫咪塔罗占卜应用，78 张牌全部融入猫咪元素，搭配 AI 个性化解牌。

## 技术栈

| 组件     | 技术                                                                 |
| -------- | -------------------------------------------------------------------- |
| 语言     | Python 3.14+                                                         |
| TUI 框架 | Textual                                                              |
| 牌面渲染 | rich-pixels                                                          |
| 图像处理 | Pillow                                                               |
| AI 解牌  | OpenAI-compatible 接口（远程 API）                                   |
| Web UI   | FastAPI + vanilla JS（`--web` 启动，可选依赖 `uv sync --extra web`） |
| 牌义数据 | YAML                                                                 |
| 用户配置 | JSON（`.neko/settings.json`，首次运行引导）                          |

## 目录结构要点

- `src/nekomata/` — 主代码包
  - `screens/` — Textual Screen（首页、选牌阵、抽牌、解读、牌库浏览、首次配置）
  - `card/` — 牌组逻辑、数据模型、牌义加载
  - `spread/` — 牌阵（单牌、三牌阵、五牌阵等）
  - `render/` — PNG 渲染、动画、主题
  - `ai/` — AI 解牌接口 + prompt 模板
  - `storage/` — JSON 配置读写
  - `web/` — FastAPI Web UI 服务（`static/` 下为前端文件）
- `assets/cards/` — 像素风猫咪塔罗牌 PNG
- `data/card_meanings.yaml` — 78 张牌正逆位释义
- `data/ui_strings.json` — 共享 UI 文案（加载提示、装饰符、流式速度等）
- `.neko/settings.json` — 用户配置（API 地址、密钥、模型）
- `tests/` — 测试（unit / integration）

## 项目规范

- **代码许可证**：MIT
- **美术资源**：CC BY-NC-SA 4.0（`assets/cards/` 下所有 PNG）
  - 生成牌面时不引用具体商业牌组名称或风格描述
  - 提示词仅使用"像素风 + 猫咪 + 塔罗元素"等通用描述
- **牌面规格**：64×96 像素，RGBA，NEAREST 插值缩放
- **渲染分级**：按终端尺寸动态选择（全尺寸 64×96 / 中等 48×72 / 紧凑 32×48 / 预览 56×84 / 纯文字）
- **动画**：使用 Textual `offset`/`opacity` 属性动画，不依赖浏览器式 3D 翻转
- **DrawnCard** 使用组合模式（持有 `Card` 引用），不继承 `Card`

## 测试要求

- 使用 pytest + pytest-asyncio
- Textual 交互测试用 `app.run_test()` (pilot)
- AI 后端测试用 mock
- 核心覆盖：牌组完整性、洗牌无重复、逆位概率、牌阵位置数

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

# 架构指南

## 核心模块

### 1. Card 模块 (`src/nekomata/card/`)

**职责**：塔罗牌数据模型和牌组管理

**关键类型**：

- `Card`：不可变数据类，包含牌的所有信息（ID、名称、牌组、编号、元素、占星、关键词、释义）
- `DrawnCard`：组合模式，持有 `Card` 引用，添加位置和正逆位状态
- `Position`：牌阵中的位置定义
- `Arcana`：枚举类型（MAJOR, CUPS, WANDS, SWORDS, PENTACLES）

**设计模式**：

- `Card` 使用 `frozen=True` 数据类，确保不可变性
- `DrawnCard` 使用组合而非继承，便于扩展状态

### 2. Spread 模块 (`src/nekomata/spread/`)

**职责**：牌阵定义和管理

**关键类**：

- `Spread`：基类，定义牌阵接口
- `SingleSpread`：单牌阵
- `ThreeCardSpread`：三牌阵（过去-现在-未来）
- `FiveCardSpread`：五牌阵

**设计模式**：

- 使用注册表模式（`SPREAD_REGISTRY`）管理牌阵
- 牌阵文案从 `data/spread_strings.json` 加载
- 支持自定义 `display_order` 控制视觉布局

### 3. Render 模块 (`src/nekomata/render/`)

**职责**：终端渲染、主题、动画

**关键组件**：

- `card_renderer.py`：牌面渲染，支持多种渲染模式
- `terminal.py`：终端尺寸检测和渲染模式选择
- `themes.py`：Catppuccin 配色主题
- `styles.py`：样式常量定义
- `animations.py`：Textual 动画工具

**渲染模式**：

- `full`：64×96 全尺寸
- `medium`：48×72 中等尺寸
- `compact`：32×48 紧凑尺寸
- `preview`：56×84 预览尺寸
- `text`：纯文字模式

### 4. AI 模块 (`src/nekomata/ai/`)

**职责**：AI 解牌接口

**关键类**：

- `AIInterpreter`：协议类，定义解牌接口
- `OpenAIInterpreter`：OpenAI-compatible 实现
- `InterpretationError`：解牌错误类型
- `StreamChunk`：流式输出片段

**设计模式**：

- 使用 Protocol 定义接口，便于扩展
- 支持流式和非流式两种模式
- 错误类型区分可重试和不可重试

### 5. Screens 模块 (`src/nekomata/screens/`)

**职责**：Textual 用户界面

**关键屏幕**：

- `HomeScreen`：首页，显示应用标题和菜单
- `SpreadSelectScreen`：牌阵选择界面
- `DrawScreen`：抽牌界面
- `DrawDetailScreen`：牌面详情和 AI 解读
- `CardBrowserScreen`：牌库浏览
- `SetupScreen`：首次运行配置

**设计模式**：

- 每个屏幕独立管理状态
- 使用 Textual 的 `push_screen` / `pop_screen` 导航
- 通过 `callback` 传递结果

### 6. Storage 模块 (`src/nekomata/storage/`)

**职责**：配置管理

**关键类**：

- `AppConfig`：配置数据类
- 支持加载、保存、验证配置
- 配置文件路径：`.neko/settings.json`

### 7. Web 模块 (`src/nekomata/web/`)

**职责**：Web UI 服务

**关键组件**：

- `server.py`：FastAPI 服务器
- `static/`：前端静态文件（HTML/JS/CSS）

**API 端点**：

- `GET /`：Web UI 首页
- `GET /api/config`：获取配置
- `POST /api/config`：保存配置
- `GET /api/cards`：获取所有牌
- `GET /api/spreads`：获取所有牌阵
- `POST /api/interpret`：AI 解牌（流式）

## 数据流

### TUI 模式

```
用户输入 → Textual 事件 → Screen 处理 → 更新 UI
                ↓
        选择牌阵 → 抽牌 → 显示牌面 → AI 解读
                ↓
        加载配置 → 调用 AI API → 流式显示结果
```

### Web UI 模式

```
浏览器请求 → FastAPI 路由 → 处理逻辑
                ↓
        获取数据 → 返回 JSON / 流式响应
                ↓
        前端渲染 → 用户交互 → 发送请求
```

## 关键设计决策

### 1. 不可变数据模型

- `Card` 使用 `frozen=True`，确保牌数据不被意外修改
- `DrawnCard` 使用组合模式，便于扩展状态

### 2. 渲染自适应

- 根据终端尺寸动态选择渲染模式
- 支持从全尺寸到纯文字的多种模式

### 3. AI 接口抽象

- 使用 Protocol 定义接口，便于扩展不同 AI 后端
- 支持流式和非流式两种模式

### 4. 配置管理

- 配置文件支持多级查找（当前目录、用户目录）
- 首次运行自动引导配置

### 5. 主题系统

- 使用 Catppuccin Mocha 配色
- 统一的样式常量定义

---

# 开发工作流

## 添加新功能

1. **理解需求**：明确功能目标和验收标准
2. **设计接口**：确定数据模型和 API
3. **实现代码**：遵循现有代码风格
4. **编写测试**：单元测试 + 集成测试
5. **更新文档**：README.md 和 AGENTS.md

## 修复 Bug

1. **复现问题**：编写能复现的测试
2. **定位原因**：分析代码逻辑
3. **实现修复**：最小化改动
4. **验证修复**：确保测试通过
5. **回归测试**：确保不引入新问题

## 重构代码

1. **理解现状**：分析现有代码结构
2. **设计目标**：确定重构后的架构
3. **逐步重构**：小步快跑，频繁测试
4. **保持兼容**：确保外部接口不变
5. **更新文档**：记录架构变化

## 测试策略

### 单元测试

- 测试单个函数/方法
- Mock 外部依赖
- 覆盖边界条件

### 集成测试

- 测试模块间交互
- 使用 Textual pilot 测试 UI
- 测试完整流程

### 测试覆盖率

- 核心逻辑：100% 覆盖
- UI 代码：主要路径覆盖
- 工具脚本：可选覆盖

---

# 常见任务

## 添加新牌阵

1. 在 `src/nekomata/spread/` 创建新文件
2. 继承 `Spread` 基类
3. 在 `data/spread_strings.json` 添加文案
4. 在 `src/nekomata/spread/__init__.py` 注册
5. 编写测试

## 添加新牌义

1. 编辑 `data/card_meanings.yaml`
2. 运行 `python scripts/generate_card_data.py`
3. 运行测试验证

## 修改 UI 样式

1. 编辑 `src/nekomata/render/styles.py`
2. 更新相关屏幕的 CSS
3. 测试不同渲染模式

## 扩展 AI 功能

1. 在 `src/nekomata/ai/interpreter.py` 添加新方法
2. 更新 `src/nekomata/ai/prompts.py` 提示词
3. 在 Web API 中暴露新功能
4. 编写测试

---

# 注意事项

## 代码风格

- 使用 Python 3.14+ 语法
- 遵循 PEP 8
- 使用类型注解
- 编写文档字符串

## 性能考虑

- 牌面渲染使用缓存
- AI 解牌使用流式输出
- 配置文件懒加载

## 安全考虑

- API 密钥不提交到代码库
- 配置文件在 `.gitignore` 中
- 用户输入需要验证

## 兼容性

- 支持 Python 3.14+
- 支持主流终端（iTerm2, Windows Terminal, GNOME Terminal 等）
- Web UI 支持现代浏览器
