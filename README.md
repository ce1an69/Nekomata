# Nekomata

**[English](README_EN.md)** | 中文

> Nekomata 取自日语"猫又"——传说中的二尾妖猫，擅长变化与预知。

终端里的像素风猫咪塔罗占卜应用。78 张牌全部融入猫咪元素，搭配 AI 个性化解牌。

支持四种运行模式：**TUI** / **CLI** / **Web UI** / **Desktop**。

## 功能

- **完整 78 张牌** — 22 大阿尔卡纳 + 56 小阿尔卡纳，像素风牌面，自适应渲染
- **5 种牌阵** — 单牌 / 过去-现在-未来 / 现状-行动-结果 / 身-心-灵 / 五牌十字
- **AI 解牌** — OpenAI 兼容接口，流式输出，支持追问，基于 urllib 无 SDK 依赖
- **多模式界面** — TUI（Catppuccin Mocha）/ CLI / Web UI（FastAPI）/ Desktop（PyWebView）
- **国际化** — 中文 / English

## 安装

Python 3.13+，推荐 [uv](https://docs.astral.sh/uv/)：

```bash
git clone https://github.com/ce1an69/Nekomata.git
cd Nekomata
uv sync
```

可选依赖：`--extra web` / `--extra desktop`（含 Web）/ `--extra dev`。

## 使用

```bash
nekomata                  # TUI 模式（默认）
nekomata -c               # CLI 交互模式
nekomata -c -q "今天运势如何？" -S past_present_future -y  # 单行占卜
nekomata --web            # Web UI，默认端口 8080
nekomata-desktop          # 原生桌面窗口
```

### 命令行参数

| 参数                | 说明                        |
| ------------------- | --------------------------- |
| `--web`             | 启动 Web UI                 |
| `--port PORT`       | Web 端口（默认 8080）       |
| `--cli` / `-c`      | CLI 模式                    |
| `-q` / `--question` | 占卜问题                    |
| `-s` / `--seed`     | 随机种子（可复现）          |
| `-S` / `--spread`   | 牌阵 key                    |
| `-y` / `--yes`      | 跳过确认                    |

### TUI 快捷键

`q`/`Esc` 返回 · `↑↓←→` 导航 · `Enter` 确认 · `Tab` 切换面板 · `1`-`6` 选牌阵 · `i` 解读 · `d` 详情 · `r` 正逆位

## 配置

首次启动进入引导界面，配置 AI 后端（API 地址 / 密钥 / 模型 / 语言）。

配置保存在 `.neko/settings.json`，也可通过环境变量覆盖：`NEKOMATA_API_URL` / `NEKOMATA_API_KEY` / `NEKOMATA_MODEL`。

## 技术栈

Python 3.13+ · Textual · textual-image · Pillow · FastAPI + vanilla JS · PyWebView · urllib（AI）· 自研 i18n

## 项目结构

```
src/nekomata/        主代码（app / cli / desktop / card / spread / render / ai / screens / web）
assets/              牌面（78×3 变体）、猫咪照片、图标、字体
data/                牌义 YAML、i18n JSON、prompt 模板
tests/               pytest 单元 + 集成测试
scripts/             构建脚本
```

## 开发

```bash
uv sync --extra desktop --extra dev
uv run pytest                  # 全部测试
uv run pytest --cov=nekomata   # 覆盖率
```

## 许可证

- **代码**：[MIT License](LICENSE)
- **美术资源**（`assets/cards/`）：[CC BY-NC-SA 4.0](LICENSE-ASSETS.md)

## 致谢

[Textual](https://textual.textualize.io/) · [textual-image](https://github.com/sarusso/textual-image) · [FastAPI](https://fastapi.tiangolo.com/) · [Catppuccin](https://github.com/catppuccin/catppuccin) · [PyWebView](https://pywebview.flowrl.com/)
