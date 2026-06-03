# 安装指南

通过 PyPI 安装 Nekomata，或从源码构建开发环境。

**[English](../en/INSTALLATION.md)**

---

## 通过 PyPI 安装

最简单的方式：

```bash
pip install nekomata-tarot
```

> 需要 **Python 3.13+**。如果没有 Python，前往 [python.org](https://www.python.org/) 或使用系统包管理器安装。

安装后启动：

```bash
nekomata-tarot            # TUI 模式（默认）
nekomata-tarot -c         # CLI 模式
nekomata-tarot --desktop  # 桌面模式（需要额外依赖，见下文）
```

### 桌面模式

桌面模式需要额外依赖，安装方式：

```bash
pip install "nekomata-tarot[desktop]"
```

---

## 从源码安装

用于开发或获取最新未发布版本。

### 前置条件

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)**（推荐的包管理器）

### 步骤

```bash
git clone https://github.com/ce1an69/Nekomata.git
cd Nekomata
uv sync
```

完整开发环境（桌面 + 开发工具）：

```bash
uv sync --extra desktop --extra dev
```

### 可选依赖组

| 依赖组 | 安装命令 | 内容 |
|--------|---------|------|
| `desktop` | `uv sync --extra desktop` | PyWebView、FastAPI、uvicorn、PyInstaller |
| `dev` | `uv sync --extra dev` | pytest、pytest-asyncio、pytest-mock、pyright |

---

## 验证安装

```bash
nekomata-tarot --help
```

看到帮助输出即安装成功。

## 常见问题

### `command not found: nekomata-tarot`

确认 Python 的 `bin/` 目录在 `PATH` 中。使用 `uv` 时也可以直接运行：

```bash
uv run nekomata-tarot
```

### `ImportError: no module named 'textual'`

重新安装：

```bash
pip install --force-reinstall nekomata-tarot
```

### TUI 只显示文字牌面

终端可能不支持 Kitty Graphics Protocol 或 Sixel。最佳体验请使用 **Kitty**、**Ghostty** 或 **Contour**。完整兼容性表格见 [README](../../README.md)。
