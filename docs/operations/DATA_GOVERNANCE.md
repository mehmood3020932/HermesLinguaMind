# Privacy & Data Governance

Hermes should be privacy-conscious by design, especially because speech and learning history can be sensitive.

## Defaults

- Do not retain raw microphone audio unless a feature explicitly requires it.
- Prefer derived transcripts/feedback with configurable retention.
- Separate product analytics from user content.
- Give users a clear account deletion path.
- Document every external AI provider and what data leaves the deployment.
- Allow local-only mode where practical.

## Consent

Explicit consent should be required for:

- recording/retaining audio;
- public community posts;
- sharing progress publicly;
- using user content for model improvement;
- third-party processing beyond the local deployment.

## Data classification

**Public:** documentation, open-source code, public language packs.

**Internal:** operational metrics and non-public roadmaps.

**Sensitive:** account data, private conversations, audio, learning history, credentials.

Production controls must be selected according to the jurisdiction and business model in which Hermes is deployed.
