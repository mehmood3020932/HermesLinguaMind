# 🔒 Security Policy

## Reporting a Vulnerability

**DO NOT** open a public issue for security vulnerabilities!

Please report privately via:
- GitHub Security Advisories (preferred): Security tab → Report a vulnerability
- Email: mehmood3020932@users.noreply.github.com

## Response Timeline

| Severity | Response Time | Fix Time |
|----------|---------------|----------|
| Critical | 24 hours | 48 hours |
| High | 48 hours | 1 week |
| Medium | 1 week | 2 weeks |
| Low | 2 weeks | Next release |

## Supported Versions

| Version | Supported |
|---------|-----------|
| v0.1.0-alpha | ✅ Yes |

## Security Measures

- ✅ Secret scanning enabled (TruffleHog + GitHub native)
- ✅ Dependabot alerts for dependencies
- ✅ All PRs require code review before merge
- ✅ CI tests must pass before merge
- ✅ No direct pushes to main branch

## What We Check in PRs

- [ ] No hardcoded secrets/credentials
- [ ] No malicious code patterns
- [ ] Tests included for new features
- [ ] Dependencies from trusted sources
- [ ] No breaking changes without discussion
