# 贡献指南

[English](../en/CONTRIBUTING.md)

感谢你对 Nekomata 的关注！以下是快速上手指南。

## 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/ce1an69/Nekomata.git
cd Nekomata

# 安装开发依赖（需要 uv）
uv sync --extra dev

# 安装 pre-commit 钩子
uv run pre-commit install
```

## 提交变更

1. 创建功能分支：`git checkout -b feat/my-feature`
2. 进行修改
3. 运行检查：

```bash
uv run pytest                    # 测试
uv run ruff check src/ tests/    # 代码检查
uv run ruff format src/ tests/   # 格式化
uv run pyright                   # 类型检查
```

4. 使用清晰的提交信息（推荐 conventional commits：`feat:`、`fix:`、`docs:` 等）
5. 向 `main` 分支提交 Pull Request

## 代码风格

- Python 3.13+，所有函数签名必须带类型注解
- 使用 **ruff** 格式化（替代 black + isort）
- 行宽上限：120 字符
- 使用 isort 排序导入（通过 ruff）

## 添加 / 修改 UI 文案

所有用户可见的文案位于 `data/locales/{en,zh}.json`（TUI 和 Web 共享）。
牌阵相关文案位于 `data/locales/spreads_{en,zh}.json`。

## 运行测试

```bash
# 所有测试
uv run pytest

# 仅单元测试
uv run pytest tests/unit/

# 仅集成测试
uv run pytest tests/integration/

# 带覆盖率
uv run pytest --cov=nekomata --cov-report=term-missing
```

## 报告问题

请使用 [GitHub Issue](https://github.com/ce1an69/Nekomata/issues) 并包含：

- 操作系统、Python 版本、终端模拟器
- 复现步骤
- 期望行为 vs 实际行为
