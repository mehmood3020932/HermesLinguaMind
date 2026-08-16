# Production Readiness Checklist

This is a checklist, not a claim that the current repository has completed every item.

## Application

- [ ] Domain and HTTPS configured
- [ ] Production CORS configured
- [ ] Secrets generated and stored outside Git
- [ ] Database migrations automated
- [ ] Backup and restore tested
- [ ] Rate limiting verified
- [ ] Error pages and graceful degradation tested

## AI

- [ ] Local model tested on target hardware
- [ ] Provider fallback policy documented
- [ ] Token/cost budgets enforced for hosted providers
- [ ] Prompt injection and tool-use boundaries reviewed
- [ ] User data retention policy documented

## Voice / avatar

- [ ] Microphone permissions tested on supported devices
- [ ] STT accuracy measured by language
- [ ] TTS voice licenses recorded
- [ ] Avatar model licenses recorded
- [ ] WebRTC TURN server deployed if required
- [ ] Reconnect and fallback tested

## Mobile

- [ ] Release signing configured outside source control
- [ ] Crash reporting configured with privacy review
- [ ] Android/iOS permission copy reviewed
- [ ] Offline/error states tested
- [ ] Accessibility pass completed

## Operations

- [ ] Prometheus/Grafana or equivalent deployed
- [ ] Structured logs collected
- [ ] Alerts configured
- [ ] Load test completed
- [ ] Security review completed
- [ ] Dependency update process established
