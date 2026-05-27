# 构建桌面应用

从零开始在 macOS / Windows 上构建 Nekomata 桌面应用。

## 前置条件

| 依赖 | 最低版本 | 说明 |
|------|---------|------|
| Python | 3.13+ | Windows 桌面打包使用 3.13 以兼容 pywebview WinForms / pythonnet |
| uv | latest | 包管理器，用于安装依赖 |

## macOS

### 1. 安装环境

```bash
# Python（Homebrew）
brew install python@3.14

# uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 安装项目依赖

```bash
cd Nekomata
uv sync --extra desktop
```

### 3. 构建

```bash
python scripts/build_desktop.py
```

产物：`dist/Nekomata.app` + `dist/Nekomata.dmg`

打开 DMG 后将 Nekomata.app 拖入 Applications 文件夹即可使用。

### 4. 清理重建

```bash
python scripts/build_desktop.py --clean
```

---

## Windows

### 1. 安装环境

```powershell
# Python（打包推荐 3.13，兼容 pywebview 的 Windows 后端）
winget install Python.Python.3.13

# uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 安装项目依赖

```powershell
cd Nekomata
$env:UV_PROJECT_ENVIRONMENT = ".venv-win"
uv sync --python 3.13 --extra desktop
```

### 3. 构建

```powershell
.\.venv-win\Scripts\python.exe scripts\build_desktop.py
```

产物：`dist/Nekomata.exe`，单文件运行，不需要外部 `_internal` 目录。

### 4. 清理重建

```powershell
.\.venv-win\Scripts\python.exe scripts\build_desktop.py --clean
```

---

## 注意事项

- **WebView 引擎**：pywebview 在 macOS 使用 WKWebView（系统自带），在 Windows 使用 WinForms + Edge WebView2（Win10/11 自带，旧版 Windows 需单独安装 [Evergreen Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)）
- **Windows Python 版本**：Windows 打包使用 Python 3.13；Python 3.14 下 pythonnet 暂不兼容，会导致 WinForms 后端初始化失败
- **产物大小**：约 50-60 MB（牌面资源占大头，已排除 `_origin.png` 和 `contact_sheet`）；Windows 为单文件 exe，启动时 PyInstaller 会解包到临时目录
- **TUI 相关依赖**（textual、rich、PIL 等）在打包时被排除，桌面应用不依赖终端渲染
- **spec 文件**：构建配置在 `nekomata.spec`，如需调整打包内容（图标、隐藏导入等）修改此文件
