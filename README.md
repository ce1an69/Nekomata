# Nekomata

终端里的像素风猫咪塔罗占卜应用。78 张牌全部融入猫咪元素，搭配 AI 个性化解牌。

## 功能特性

### 塔罗牌系统

- **完整 78 张牌**：22 张大阿尔卡纳 + 56 张小阿尔卡纳（圣杯、权杖、宝剑、星币）
- **像素风牌面**：64×96 像素，RGBA 格式，NEAREST 插值缩放
- **自适应渲染**：根据终端尺寸自动选择渲染模式（全尺寸 / 中等 / 紧凑 / 预览 / 纯文字）
- **正逆位系统**：可配置逆位概率（默认 50%）

### 牌阵系统

- **单牌阵**：快速占卜，适合日常问题
- **三牌阵**：过去-现在-未来，适合时间线分析
- **五牌阵**：多维度解读，适合复杂问题
- **自定义牌阵**：通过 `data/spread_strings.json` 扩展

### AI 解牌

- **OpenAI 兼容接口**：支持任意 OpenAI-compatible API
- **流式输出**：实时显示解牌过程
- **多模型支持**：可配置不同 AI 模型
- **结构化提示词**：针对不同牌阵优化的 prompt 模板

### 用户界面

- **TUI 模式**：基于 Textual 的终端用户界面
- **Web UI 模式**：基于 FastAPI 的浏览器界面
- **首次运行引导**：自动检测并引导配置 AI 后端
- **牌库浏览**：查看所有 78 张牌的详细信息

## 安装

### 前置条件

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)（推荐）或 pip

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/ce1an69/Nekomata.git
cd Nekomata

# 使用 uv 安装（推荐）
uv python pin 3.14    # 首次：固定 Python 版本
uv sync               # 安装运行时依赖

# 或使用 pip 安装
pip install -e .
```

### 可选依赖

```bash
# Web UI 依赖
uv sync --extra web

# 开发依赖（测试等）
uv sync --extra dev

# 安装所有依赖
uv sync --extra web --extra dev
```

## 使用

### TUI 模式（默认）

```bash
nekomata
# 或
uv run nekomata
```

### Web UI 模式

```bash
nekomata --web              # 默认端口 8080
nekomata --web --port 3000  # 指定端口
# 或
uv run nekomata --web
```

### 命令行参数

| 参数          | 说明                        |
| ------------- | --------------------------- |
| `--web`       | 启动 Web UI 模式            |
| `--port PORT` | Web 服务器端口（默认 8080） |

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

### 配置文件

配置保存在 `.neko/settings.json`（当前目录或 `~/.neko/`）：

```json
{
  "api_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "model": "gpt-4"
}
```

### 环境变量

支持通过环境变量覆盖配置：

- `NEKOMATA_API_URL`：API 地址
- `NEKOMATA_API_KEY`：API 密钥
- `NEKOMATA_MODEL`：模型名称

## 技术栈

| 组件     | 技术                 | 说明              |
| -------- | -------------------- | ----------------- |
| 语言     | Python 3.14+         | 主要开发语言      |
| TUI 框架 | Textual              | 终端用户界面框架  |
| 牌面渲染 | rich-pixels          | 终端像素渲染      |
| 图像处理 | Pillow               | PNG 图像处理      |
| AI 解牌  | OpenAI-compatible    | 远程 API 接口     |
| Web UI   | FastAPI + vanilla JS | 浏览器界面        |
| 牌义数据 | YAML                 | 78 张牌正逆位释义 |
| 用户配置 | JSON                 | 用户设置存储      |

## 项目结构

```
Nekomata/
├── src/nekomata/           # 主代码包
│   ├── app.py              # 应用入口
│   ├── card/               # 牌组逻辑
│   │   ├── types.py        # 数据类型定义
│   │   ├── deck.py         # 牌组管理
│   │   └── data.py         # 牌义数据加载
│   ├── spread/             # 牌阵系统
│   │   ├── base.py         # 牌阵基类
│   │   ├── single.py       # 单牌阵
│   │   ├── three_card.py   # 三牌阵
│   │   └── five_card.py    # 五牌阵
│   ├── render/             # 渲染系统
│   │   ├── card_renderer.py # 牌面渲染
│   │   ├── terminal.py     # 终端检测
│   │   ├── themes.py       # 主题系统
│   │   └── styles.py       # 样式定义
│   ├── ai/                 # AI 解牌
│   │   ├── interpreter.py  # 解牌器实现
│   │   └── prompts.py      # 提示词模板
│   ├── screens/            # Textual 屏幕
│   │   ├── home.py         # 首页
│   │   ├── spread_select.py # 牌阵选择
│   │   ├── draw.py         # 抽牌界面
│   │   ├── draw_detail.py  # 牌面详情
│   │   ├── card_browser.py # 牌库浏览
│   │   └── setup.py        # 首次配置
│   ├── storage/            # 存储系统
│   │   └── config.py       # 配置管理
│   └── web/                # Web UI
│       ├── server.py       # FastAPI 服务器
│       └── static/         # 前端静态文件
├── assets/
│   └── cards/              # 像素风猫咪塔罗牌 PNG
├── data/
│   ├── card_meanings.yaml  # 78 张牌正逆位释义
│   ├── spread_strings.json # 牌阵文案
│   └── ui_strings.json     # 共享 UI 文案
├── tests/                  # 测试代码
│   ├── unit/               # 单元测试
│   └── integration/        # 集成测试
├── scripts/                # 工具脚本
│   ├── generate_card_data.py      # 生成牌义数据
│   └── generate_runtime_card_images.py # 生成运行时牌面
├── pyproject.toml          # 项目配置
├── CATS.md                 # 神秘猫咪角色设定
├── LICENSE                 # MIT 许可证
└── LICENSE-ASSETS.md       # 美术资源许可证
```

## 开发

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/ce1an69/Nekomata.git
cd Nekomata

# 安装依赖
uv sync --extra web --extra dev

# 运行测试
uv run pytest

# 运行特定测试
uv run pytest tests/unit/
uv run pytest tests/integration/
```

### 测试

项目使用 pytest 进行测试：

```bash
# 运行所有测试
uv run pytest

# 运行单元测试
uv run pytest tests/unit/

# 运行集成测试
uv run pytest tests/integration/

# 生成覆盖率报告
uv run pytest --cov=nekomata
```

### 代码规范

- 使用 Python 3.14+ 语法
- 遵循 PEP 8 代码风格
- 使用类型注解
- 编写文档字符串

### 添加新牌阵

1. 在 `src/nekomata/spread/` 创建新文件
2. 继承 `Spread` 基类
3. 在 `data/spread_strings.json` 添加文案
4. 在 `src/nekomata/spread/__init__.py` 注册

### 添加新牌义

1. 编辑 `data/card_meanings.yaml`
2. 运行 `python scripts/generate_card_data.py` 更新数据
3. 运行测试验证

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

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 贡献指南

- 遵循现有代码风格
- 添加适当的测试
- 更新文档
- 确保所有测试通过

## 致谢

- [Textual](https://textual.textualize.io/) - 终端用户界面框架
- [rich-pixels](https://github.com/Textualize/rich-pixels) - 终端像素渲染
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Catppuccin](https://github.com/catppuccin/catppuccin) - 配色方案

## 联系方式

- GitHub: [ce1an69/Nekomata](https://github.com/ce1an69/Nekomata)
- Issues: [GitHub Issues](https://github.com/ce1an69/Nekomata/issues)
