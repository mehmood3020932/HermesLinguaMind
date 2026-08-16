# 🔍 Code Review Checklist (For Maintainers)

Use this checklist before merging ANY PR:

## 1. Security Review (MOST IMPORTANT)
- [ ] No hardcoded passwords, API keys, or tokens
- [ ] No suspicious network calls or data exfiltration
- [ ] No eval(), exec(), or dynamic code execution
- [ ] Dependencies are from trusted sources
- [ ] No obfuscated or minified code added

## 2. Code Quality
- [ ] Code follows project style guidelines
- [ ] Functions have clear names and comments
- [ ] No unnecessary complexity
- [ ] Error handling is proper

## 3. Testing
- [ ] Tests added for new functionality
- [ ] All existing tests still pass
- [ ] CI pipeline is green

## 4. Documentation
- [ ] README updated if needed
- [ ] API docs updated for endpoint changes
- [ ] CHANGELOG entry added

## 5. Scope Check
- [ ] PR only changes what it claims to
- [ ] No unrelated files modified
- [ ] No large refactoring mixed with bug fixes

## 🚨 Red Flags (Reject Immediately)
- ❌ Changes to .github/workflows without discussion
- ❌ Adding new dependencies without justification
- ❌ Modifying authentication/authorization code casually
- ❌ Binary files or executables in PR
- ❌ Requests to disable security checks
