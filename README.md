# Nekomata

**[English](README_EN.md)** | 中文

> Nekomata 取自日语"猫又"——传说中的二尾妖猫，擅长变化与预知。

终端里的像素风猫咪塔罗占卜应用。78 张牌全部融入猫咪元素，搭配 AI 个性化解牌。

支持三种运行模式：**TUI**（终端界面）、**Web UI**（浏览器）、**Desktop**（原生窗口）。

## 功能特性

### 塔罗牌系统

- **完整 78 张牌**：22 张大阿尔卡纳 + 56 张小阿尔卡纳（圣杯、权杖、宝剑、星币）
- **像素风牌面**：64×96 像素，RGBA 格式，NEAREST 插值缩放
- **自适应渲染**：根据终端尺寸自动选择渲染模式（full / medium / compact / preview / text）
- **正逆位系统**：可配置逆位概率（默认 50%）

### 牌阵系统

- **单牌阵**：快速占卜，适合日常问题
- **过去-现在-未来**：时间线分析
- **现状-行动-结果**：行动指引
- **身-心-灵**：内在探索
- **五牌十字**：多维度深度解读

### AI 解牌

- **OpenAI 兼容接口**：支持任意 OpenAI-compatible API
- **流式输出**：实时显示解牌过程
- **追问功能**：对解读结果进一步追问
- **结构化提示词**：每种牌阵独立的 prompt 模板
- **无 SDK 依赖**：基于 urllib 轻量实现

### 多模式界面

- **TUI 模式**：基于 Textual 的终端界面，Catppuccin Mocha 配色
- **CLI 模式**：纯命令行交互，支持单行占卜
- **Web UI 模式**：基于 FastAPI 的浏览器界面
- **Desktop 模式**：PyWebView 原生窗口
- **国际化**：支持中文 / 英文切换

## 安装

### 前置条件

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)（推荐）或 pip

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/ce1an69/Nekomata.git
cd Nekomata

# 使用 uv 安装（推荐）
uv sync

# 或使用 pip 安装
pip install -e .
```

### 可选依赖

```bash
# Web UI 依赖
uv sync --extra web

# Desktop 依赖（含 Web UI）
uv sync --extra desktop

# 开发依赖（测试等）
uv sync --extra dev

# 安装所有依赖
uv sync --extra desktop --extra dev
```

## 使用

### TUI 模式（默认）

```bash
nekomata
# 或
uv run nekomata
```

### CLI 模式

```bash
# 交互式
nekomata --cli
nekomata -c

# 单行占卜
nekomata -c -q "今天运势如何？" -S past_present_future -y

# 指定随机种子（可复现）
nekomata -c -q "我的问题" -s 42
```

### Web UI 模式

```bash
nekomata --web              # 默认端口 8080
nekomata --web --port 3000  # 指定端口
```

### Desktop 模式

```bash
nekomata-desktop            # 打开原生窗口
nekomata-desktop --debug    # 调试模式
```

### 命令行参数

| 参数                | 说明                        |
| ------------------- | --------------------------- |
| `--web`             | 启动 Web UI 模式            |
| `--port PORT`       | Web 服务器端口（默认 8080） |
| `--cli` / `-c`      | 启动 CLI 模式               |
| `-q` / `--question` | 占卜问题（CLI 模式）        |
| `-s` / `--seed`     | 随机种子（可复现抽牌）      |
| `-S` / `--spread`   | 牌阵类型 key                |
| `-y` / `--yes`      | 跳过确认，直接开始解读      |

### 键盘快捷键（TUI 模式）

| 按键            | 功能                   |
| --------------- | ---------------------- |
| `q` / `Esc`     | 返回 / 退出            |
| `↑` `↓` `←` `→` | 导航                   |
| `Enter`         | 确认 / 选择            |
| `Tab`           | 切换焦点面板           |
| `1`–`6`         | 快速选择牌阵           |
| `i`             | AI 解读                |
| `d`             | 显示 / 隐藏详情        |
| `r`             | 切换正逆位（牌库浏览） |

## 配置

### 首次运行

首次启动时会进入引导界面，配置 AI 后端：

- API 地址（默认：`https://api.openai.com/v1`）
- API 密钥
- 模型名称
- 语言（中文 / English）

### 配置文件

配置保存在 `.neko/settings.json`（当前目录或 `~/.neko/`）：

```json
{
  "api_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "model": "gpt-4",
  "lang": "zh"
}
```

### 环境变量

支持通过环境变量覆盖配置：

- `NEKOMATA_API_URL`：API 地址
- `NEKOMATA_API_KEY`：API 密钥
- `NEKOMATA_MODEL`：模型名称

## 技术栈

| 组件     | 技术                 | 说明                         |
| -------- | -------------------- | ---------------------------- |
| 语言     | Python 3.13+         | 主要开发语言                 |
| TUI 框架 | Textual              | 终端用户界面框架             |
| 牌面渲染 | textual-image        | 终端图像渲染                 |
| 图像处理 | Pillow               | PNG 图像处理与导出           |
| AI 解牌  | OpenAI-compatible    | urllib 轻量实现，无 SDK 依赖 |
| Web UI   | FastAPI + vanilla JS | 浏览器界面                   |
| Desktop  | PyWebView            | 原生窗口                     |
| 国际化   | 自研 i18n            | 支持 en/zh                   |
| 牌义数据 | YAML                 | 78 张牌正逆位释义            |
| 用户配置 | JSON                 | 用户设置存储                 |

## 项目结构

```
Nekomata/
├── src/nekomata/           # 主代码包
│   ├── app.py              # TUI 入口 + argparse
│   ├── cli.py              # 纯 CLI 模式
│   ├── desktop.py          # PyWebView 桌面入口
│   ├── _paths.py           # 路径解析
│   ├── i18n.py             # 国际化
│   ├── clipboard.py        # 剪贴板操作
│   ├── card/               # 牌组逻辑（types / deck / data）
│   ├── spread/             # 牌阵系统（5 种牌阵 + 注册表）
│   ├── render/             # 渲染系统（renderer / export / themes / animations）
│   ├── ai/                 # AI 解牌（interpreter / prompts）
│   ├── screens/            # Textual 屏幕（15 个模块）
│   ├── storage/            # 配置管理
│   └── web/                # Web UI（FastAPI + vanilla JS）
├── assets/
│   ├── cards/              # 78 张牌 × 3 变体 PNG
│   ├── cats/real/          # 6 只猫咪占卜师照片
│   └── icon/               # 应用图标
├── data/
│   ├── card_meanings.yaml  # 78 张牌释义
│   ├── locales/            # i18n（en/zh）
│   └── prompts/            # AI prompt 模板
├── scripts/                # 构建和工具脚本
├── tests/                  # 测试（unit / integration）
├── pyproject.toml          # 项目配置
└── nekomata.spec           # PyInstaller 构建
```

## 开发

```bash
# 安装所有依赖
uv sync --extra desktop --extra dev

# 运行测试
uv run pytest

# 运行单元测试
uv run pytest tests/unit/

# 运行集成测试
uv run pytest tests/integration/

# 生成覆盖率报告
uv run pytest --cov=nekomata
```

## 神秘猫咪占卜师

Nekomata 的塔罗占卜由六只神秘猫咪主持：

| 名字   | 品种           | 性别 | 特征                     |
| ------ | -------------- | ---- | ------------------------ |
| 狗肉   | 暹罗猫         | 女   | 性格呆萌                 |
| 皮胖子 | 乳白色扁脸英短 | 男   | 体型偏胖                 |
| 金龙鱼 | 中长毛白猫     | 男   | 毛发蓬松                 |
| 煤球   | 黑脸暹罗猫     | 男   | 脸部深色区域比狗肉大很多 |
| 花花   | 三花狸猫       | 女   | 三色花纹                 |
| 韦恩   | 奶牛猫         | 男   | 黑白双色                 |

## 许可证

- **代码**：[MIT License](LICENSE)
- **美术资源**（`assets/cards/` 下所有 PNG）：[CC BY-NC-SA 4.0](LICENSE-ASSETS.md)

## 致谢

- [Textual](https://textual.textualize.io/) - 终端用户界面框架
- [textual-image](https://github.com/sarusso/textual-image) - 终端图像渲染
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Catppuccin](https://github.com/catppuccin/catppuccin) - 配色方案
- [PyWebView](https://pywebview.flowrl.com/) - 原生窗口
