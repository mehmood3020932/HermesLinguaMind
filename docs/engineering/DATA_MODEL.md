# Data Model & Domain Boundaries

## Core entities

```text
User
 ├── Profile
 │    ├── native_language
 │    ├── learning_language
 │    ├── level
 │    └── preferences
 ├── LearningPlan
 ├── LessonSession
 ├── ProgressEvent
 ├── ConversationSession
 └── CompanionPreference

LanguagePack
 ├── locale
 ├── curriculum
 ├── vocabulary
 ├── grammar
 └── pronunciation metadata

Companion
 ├── identity
 ├── personality
 ├── media references
 ├── voice configuration
 └── capability flags
```

## Data principles

- Store only data required for the feature.
- Keep analytics events separate from sensitive profile data.
- Avoid raw audio retention by default.
- Give users deletion/export controls where legally and technically applicable.
- Encrypt secrets and sensitive data at rest in production infrastructure.
- Never log access tokens, passwords, raw model prompts containing sensitive user data, or raw audio unless explicitly required and consented.
