# Third-party notices

Hermes LinguaMind integrates or depends on third-party software, fonts, model runtimes, voice models, and upstream projects. Those components are **not automatically relicensed under the Hermes MIT license**.

Before redistributing a release, maintainers should inventory at least:

- Flutter/Dart packages from `mobile_app/pubspec.yaml`;
- Python packages from `backend/pyproject.toml`;
- Piper voice/model files downloaded by the voice initialization scripts;
- Ollama models pulled by Compose;
- OpenTalking source/model assets when the avatar profile is enabled;
- fonts under `mobile_app/assets/fonts/` and their included license notices;
- any generated avatar or media assets contributed by the community.

Keep the original license text and attribution required by each dependency/model/asset. Do not add proprietary or restricted assets to the repository merely because a tool can generate them.
