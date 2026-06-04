# Security Policy

[中文](../zh/SECURITY.md)

## API Key Handling

Nekomata stores your AI API key locally in `~/.neko/settings.json` (or `.neko/settings.json` in the project directory). This file is excluded from version control via `.gitignore`.

### Best Practices

- **Never commit** your API key to a public repository
- Use environment variable `NEKOMATA_API_KEY` for CI/CD or shared environments
- Rotate your key immediately if it has been accidentally exposed

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately:

- Open a [GitHub Security Advisory](https://github.com/ce1an69/Nekomata/security/advisories/new)
- Or email the maintainer directly

Please **do not** file a public issue for security vulnerabilities.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Active |
