# Nekomata

终端里的像素风猫咪塔罗占卜应用。78 张牌全部融入猫咪元素，搭配 AI 个性化解牌。

## 截图

> TODO: 添加应用截图

## 功能

- 78 张像素风猫咪塔罗牌（大阿尔卡纳 + 四小阿尔卡纳）
- 多种牌阵：单牌、三牌阵、五牌阵
- 牌面像素渲染，按终端尺寸自适应
- AI 解牌（OpenAI 兼容接口）
- 首次运行引导配置（API 地址、密钥、模型）
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
| `q` / `Esc` | 返回 / 退出 |
| `↑` `↓` `←` `→` | 导航 |
| `Enter` | 确认 / 选择 |
| `Tab` | 切换焦点面板 |
| `1`–`6` | 快速选择牌阵 |
| `i` | AI 解读 |
| `d` | 显示 / 隐藏详情 |
| `r` | 切换正逆位（牌库浏览） |

## 配置

首次启动时会进入引导界面配置 AI 后端（API 地址、密钥、模型）。配置保存在 `.neko/settings.json`（当前目录或 `~/.neko/`）。

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.14+ |
| TUI 框架 | Textual |
| 牌面渲染 | rich-pixels |
| 图像处理 | Pillow |
| AI 解牌 | OpenAI-compatible 接口（远程 API） |
| Web UI | FastAPI + vanilla JS |
| 牌义数据 | YAML |
| 用户配置 | JSON（`.neko/settings.json`） |

## 项目结构

```
src/nekomata/
  screens/        # Textual Screen（首页、选牌阵、抽牌、解读、牌库浏览、首次配置）
  card/           # 牌组逻辑、数据模型、牌义加载
  spread/         # 牌阵（单牌、三牌阵、五牌阵等）
  render/         # PNG 渲染、动画、主题
  ai/             # AI 解牌接口 + prompt 模板
  storage/        # JSON 配置读写
  web/            # FastAPI Web UI 服务
    static/       # 前端静态文件（HTML/JS/CSS）
assets/
  cards/          # 像素风猫咪塔罗牌 PNG
data/
  card_meanings.yaml  # 78 张牌正逆位释义
  ui_strings.json     # 共享 UI 文案（加载提示、装饰符等）
.neko/settings.json   # 用户配置（API 地址、密钥、模型）
```

## 开发

```bash
uv sync --extra dev   # 安装开发依赖（pytest 等）
uv sync --extra web   # 安装 Web UI 依赖（FastAPI 等）
uv run pytest         # 运行测试
```

## 许可证

- 代码：[MIT License](LICENSE)
- 美术资源（`assets/cards/` 下所有 PNG）：[CC BY-NC-SA 4.0](LICENSE-ASSETS.md)
