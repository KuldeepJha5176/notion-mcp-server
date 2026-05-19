# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability, please email:
**ranacjha@gmail.com**

Please do **NOT** open public GitHub issues for security concerns.

We'll respond within 48 hours and work with you on a fix.

## User Data Security

- Each user manages their own Notion integration token
- Tokens are stored locally in user's environment (never on our servers)
- This server never collects, stores, or transmits user data to third parties
- All API calls go directly: User's machine → Notion API
- No analytics, telemetry, or tracking

## Best Practices for Users

1. **Never share your `NOTION_TOKEN`** — it's like a password
2. **Add `.env` to `.gitignore`** — never commit secrets
3. **Use private integrations** for personal use
4. **Revoke unused integrations** at notion.so/my-integrations
5. **Limit shared pages** — only share what's necessary

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x | ✅ Yes |