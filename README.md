# Nekomata

终端里的像素风猫咪塔罗占卜应用。78 张牌全部融入猫咪元素，搭配 AI 个性化解牌。

## 截图

> TODO: 添加应用截图

## 功能

- 78 张像素风猫咪塔罗牌（大阿尔卡纳 + 四小阿尔卡纳）
- 多种牌阵：单牌、三牌阵、五牌阵、凯尔特十字
- 牌面像素渲染，按终端尺寸自适应
- AI 解牌（支持 Ollama / 远程 API / 本地模板降级）
- 占卜历史记录（SQLite）
- 可配置用户设置（TOML）
- Web UI：浏览器内占卜界面（`--web` 启动）

## 安装

需要 [uv](https://docs.astral.sh/uv/) 和 Python 3.14+。

```bash
git clone https://github.com/ce1an69/Nekomata.git
cd Nekomata
uv python pin 3.14    # 首次：固定 Python 版本
uv sync               # 安装运行时依赖
```

## 使用

```bash
nekomata           # 终端 TUI 模式
nekomata --web     # 浏览器 Web UI 模式（默认端口 8080）
nekomata --web --port 3000  # 指定端口
```

### 键盘快捷键（TUI 模式）

| 按键 | 功能 |
|------|------|
| `q` | 返回 / 退出 |
| `↑` `↓` | 选择牌阵 / 浏览牌面 |

## 配置

编辑 `config.toml` 可配置 AI 后端、主题等。AI 后端支持：

- **Ollama** — 本地运行，无需网络
- **远程 API** — OpenAI 兼容接口
- **本地模板** — 无需 AI 的离线降级方案

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.14+ |
| TUI 框架 | Textual |
| 牌面渲染 | rich-pixels |
| 图像处理 | Pillow |
| AI 解牌 | OpenAI-compatible 接口 |
| Web UI | FastAPI + vanilla JS |
| 牌义数据 | YAML |
| 历史记录 | SQLite |
| 用户配置 | TOML |

## 项目结构

```
src/nekomata/
  screens/        # Textual Screen（首页、选牌阵、解读等）
  card/           # 牌组逻辑、数据模型、牌义加载
  spread/         # 牌阵（单牌、三牌阵、凯尔特十字等）
  render/         # PNG 渲染、动画、主题
  ai/             # AI 解牌接口 + prompt 模板
  storage/        # Journal SQLite + TOML 配置读写
  web/            # FastAPI Web UI 服务
    static/       # 前端静态文件（HTML/JS/CSS）
assets/
  cards/          # 78 张像素风猫咪塔罗牌 PNG
  ui/             # UI 装饰像素图
data/
  card_meanings.yaml  # 78 张牌正逆位释义
  ui_strings.json     # 共享 UI 文案（加载提示、装饰符等）
config.toml           # 用户配置
```

## 开发

```bash
uv sync --extra dev   # 安装开发依赖（pytest 等）
uv sync --extra web   # 安装 Web UI 依赖（FastAPI 等）
uv run pytest         # 运行测试
```

## 许可证

- 代码：[MIT License](LICENSE)
- 美术资源（`assets/cards/`、`assets/ui/` 下所有 PNG）：[CC BY-NC-SA 4.0](LICENSE-ASSETS.md)
