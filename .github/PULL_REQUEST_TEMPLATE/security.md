# Security-sensitive PR checklist

Use this template only when a PR changes authentication, secrets handling, permissions, public endpoints, user data, payments, moderation, or model/tool execution.

- [ ] Threat model considered
- [ ] Secrets remain outside source control
- [ ] Authorization boundaries tested
- [ ] Logs do not expose tokens or sensitive user data
- [ ] Rate limiting / abuse controls considered
- [ ] Relevant security documentation updated
