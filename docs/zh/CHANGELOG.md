# 更新日志

[English](../en/CHANGELOG.md)

本文件记录项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 变更

- 字体改用 WOFF2 格式替代 TTF，包体积减少约 40 MB
- 更新包元数据中的作者邮箱

### 修复

- 在 macOS 上禁用 Kitty 键盘协议以修复中文输入法问题
- 修复全屏对话框底部对齐和退出动画顺序
- 补全 draw_widgets 中缺失的 `SLOT_FLIP_*` 导入
- 修复 DrawScreen 鼠标点击时的 `AssertionError`

## [0.1.3] - 2026-05-31

### 修复

- 修正桌面构建产物的文件路径用于 Release 上传

## [0.1.2] - 2026-05-31

### 修复

- 修复桌面构建的 Release 工作流

## [0.1.1] - 2026-05-31

### 新增

- CLI 模式，支持流式 AI 解读（`nekomata-tarot --cli`）
- Desktop 模式，原生窗口（PyWebView）
- Web UI — FastAPI 服务端 + vanilla JS 单页应用（Desktop 模式使用）
- 追问系统，支持思考模式切换
- 解读的牌阵切换、文字复制和图片导出
- macOS DMG 和 Windows EXE 桌面端构建（PyInstaller）
- 完整的国际化支持，懒加载区域文件（英文 / 中文）
- 牌组浏览器，支持花色筛选和方向键导航
- 首次运行设置向导，支持方向键导航

### 变更

- PyPI 包名从 `nekomata` 改为 `nekomata-tarot`
- 所有返回/关闭快捷键从 `Q` 改为 `Esc`
- 精简各屏幕的命令和快捷键

### 修复

- 修复抽牌界面选完所有牌后卡死的问题
- 平滑牌组浏览器详情面板的过渡效果
- 修复 Web 端切换语言后牌阵未刷新的问题
- 重新进入设置时预填已有配置
- 修复流式内容中出现重复解读标题的问题
- Web UI 修复：国际化、端口回退、出错时跳转配置
- 修复 Windows 桌面构建兼容性（使用 edgechromium 后端）

## [0.1.0] - 2026-05-29

### 新增

- 78 张像素风猫咪塔罗牌，包含正位/逆位释义
- 5 种牌阵布局（单牌、过去-现在-未来、身-心-灵、五牌十字、处境-行动-结果）
- 通过 OpenAI 兼容 API 进行 AI 解读（SSE 流式传输）
- TUI 模式，Catppuccin Mocha 主题
- 牌组浏览器，支持按花色筛选
- 图片导出（Catppuccin 主题 PNG）
- 跨平台剪贴板支持
- 双语支持（英文 / 中文）

[Unreleased]: https://github.com/ce1an69/Nekomata/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/ce1an69/Nekomata/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/ce1an69/Nekomata/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/ce1an69/Nekomata/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ce1an69/Nekomata/releases/tag/v0.1.0
