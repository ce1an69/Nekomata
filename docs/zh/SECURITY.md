# 安全策略

[English](../en/SECURITY.md)

## API 密钥处理

Nekomata 将你的 AI API 密钥存储在本地的 `~/.neko/settings.json`（或项目目录下的 `.neko/settings.json`）。该文件已通过 `.gitignore` 排除在版本控制之外。

### 最佳实践

- **绝不要**将 API 密钥提交到公开仓库
- 在 CI/CD 或共享环境中使用环境变量 `NEKOMATA_API_KEY`
- 如果密钥意外泄露，请立即轮换

## 报告安全漏洞

如果你发现了安全漏洞，请通过以下方式私密报告：

- 提交 [GitHub 安全公告](https://github.com/ce1an69/Nekomata/security/advisories/new)
- 或直接发送邮件给维护者

请**不要**为安全漏洞提交公开 Issue。

## 支持的版本

| 版本  | 支持状态   |
|-------|-----------|
| 0.1.x | ✅ 活跃维护 |
