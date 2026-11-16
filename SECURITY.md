# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main`  | ✅        |
| tagged releases | ✅ (latest) |

## Reporting a Vulnerability

请**不要**在公开 Issue 中披露安全漏洞或粘贴密钥。

请通过 GitHub 私信 / Security Advisory 联系维护者 **jintao**（[@jintao0693](https://github.com/jintao0693)），或在仓库启用的 Security Advisories 中私下报告。

我们会尽快确认并给出修复时间预期。

## 本地开发注意

- 勿提交 `apps/api/.env`、`apps/web/.env.local`
- 生产环境务必更换 `SECRET_KEY`
- 火山方舟 API Key 仅通过设置页/租户配置写入，勿硬编码
