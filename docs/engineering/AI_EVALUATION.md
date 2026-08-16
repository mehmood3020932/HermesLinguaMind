# AI Evaluation & Quality Gates

A language tutor needs more than a generic LLM benchmark. Hermes should maintain a repeatable evaluation suite.

## Evaluation dimensions

### Tutor quality
- factual correctness
- pedagogical appropriateness
- level alignment
- explanation clarity
- correction usefulness
- hallucination rate

### Language quality
- translation adequacy
- grammar correctness
- target-language consistency
- native-language explanation quality
- pronunciation feedback quality

### Safety
- prompt injection resistance
- disallowed content handling
- privacy leakage tests
- age-appropriate behavior
- impersonation/deepfake safeguards for avatars

### Product quality
- first response latency
- speech-to-response latency
- avatar fallback success
- crash-free sessions
- session completion rate

## Release gate

A release should not be promoted solely because unit tests pass. Production promotion should require:

1. automated tests passing;
2. migration validation;
3. security checks passing;
4. AI regression suite within agreed thresholds;
5. smoke test on the real deployment;
6. rollback path verified.
