# Production Security Checklist

## Secrets Management
- [ ] All .env files excluded via .gitignore
- [ ] Production secrets in Vault/AWS Secrets Manager
- [ ] API keys rotated every 90 days
- [ ] No hardcoded credentials in codebase

## Container Security
- [ ] Base images pinned to SHA256 digests
- [ ] Non-root user in all Dockerfiles
- [ ] Trivy/Snyk scan passing in CI

## Network
- [ ] Internal services not exposed publicly
- [ ] TLS termination at gateway/nginx
- [ ] Rate limiting on public endpoints

## Monitoring
- [ ] Audit logging for auth events
- [ ] Alerting on failed login spikes
