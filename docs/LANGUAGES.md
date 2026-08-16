# Language Architecture

Hermes should treat language learning as a matrix rather than a fixed pair.

```text
User profile
├── native_language
├── ui_language
├── target_language
├── proficiency_level
└── preferred_tutor

Runtime
├── STT language
├── explanation language
├── practice language
├── TTS voice
└── lesson/content locale
```

## Starter voice set

The current consolidated Compose configuration initializes a small Piper starter set: English (US), Spanish (Spain), French (France), and German. More voices can be added through the voice initialization script after verifying model licenses.

## Desired learner behavior

For an Urdu-speaking learner studying English:

1. Explain difficult grammar in Urdu when requested or when the learner is clearly confused.
2. Present practice prompts primarily in English.
3. Correct the learner in a supportive way.
4. Speak English for immersion, with Urdu fallback.
5. Persist vocabulary, mistakes, and mastery.

This behavior should be implemented as explicit learner profile state and orchestration rules rather than relying on a single prompt.
