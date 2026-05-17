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

## 安装

需要 Python 3.12+。

```bash
git clone https://github.com/celan/Nekomata.git
cd Nekomata
uv sync
```

## 使用

```bash
nekomata
```

### 键盘快捷键

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
| 语言 | Python 3.12+ |
| TUI 框架 | Textual |
| 牌面渲染 | rich-pixels |
| 图像处理 | Pillow |
| AI 解牌 | OpenAI-compatible 接口 |
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
assets/
  cards/          # 78 张像素风猫咪塔罗牌 PNG
  ui/             # UI 装饰像素图
data/
  card_meanings.yaml  # 78 张牌正逆位释义
config.toml           # 用户配置
```

## 开发

```bash
uv sync --group dev
pytest
```

## 许可证

- 代码：[MIT License](LICENSE)
- 美术资源（`assets/cards/`、`assets/ui/` 下所有 PNG）：[CC BY-NC-SA 4.0](LICENSE-ASSETS.md)
