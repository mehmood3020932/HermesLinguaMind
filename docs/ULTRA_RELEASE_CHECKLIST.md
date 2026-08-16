# Ultra Release Checklist

Before calling a release public:

- [ ] Replace donation placeholders with verified public addresses
- [ ] Confirm no secrets/private keys exist
- [ ] Run repository doctor
- [ ] Run backend tests
- [ ] Build Docker images
- [ ] Run health and smoke tests
- [ ] Build Flutter release
- [ ] Test website → gateway → `/v1/chat`
- [ ] Test native-language → target-language routing
- [ ] Test STT/TTS where configured
- [ ] Verify avatar mode is honestly labeled (mock/CPU/real)
- [ ] Review licenses and third-party assets
- [ ] Review privacy/security settings
- [ ] Publish release notes
