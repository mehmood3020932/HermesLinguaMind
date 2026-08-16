# Contributing to Hermes LinguaMind

Thank you for helping build Hermes. The project welcomes code, tests, language packs, lesson content, accessibility improvements, design work, documentation, and infrastructure contributions.

## Before you start

1. Read the README and relevant architecture docs.
2. Search existing issues and pull requests.
3. For large changes, open a design issue first.
4. Never commit secrets, private keys, user data, model weights, or unlicensed media.

## Development workflow

```bash
git clone https://github.com/your-org/hermes-linguamind.git
cd hermes-linguamind
make setup
make doctor
```

For backend changes:

```bash
make backend-test
```

For Flutter changes:

```bash
cd mobile_app
flutter pub get
flutter analyze
flutter test
```

## Pull requests

A good PR should:

- solve one focused problem;
- include tests when practical;
- update documentation when behavior/configuration changes;
- avoid unrelated formatting churn;
- explain trade-offs and known limitations;
- include screenshots/video for meaningful UI changes.

## Language-pack contributions

Language content should identify:

- source language;
- target language;
- proficiency level;
- learning objective;
- source/reference where factual claims matter;
- pronunciation/TTS assumptions;
- license for contributed assets.

## Avatar contributions

Only contribute avatars, voices, images, motion assets, and model weights that you have the right to redistribute. Do not submit celebrity likenesses, private-person likenesses, or copyrighted assets without appropriate permission.

## Commit style

Prefer concise conventional prefixes:

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `test:` tests
- `refactor:` refactor
- `build:` tooling/dependency/build
- `chore:` maintenance

## Maintainer review

Maintainers may request security, licensing, accessibility, performance, or test changes before merge. A passing CI job is necessary but not sufficient for merge.
