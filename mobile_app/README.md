# Hermes LinguaMind — Consolidated Build

This is a merged, repaired build of the 4 uploaded phases (6, 7, 8, 9),
built on the Phase 8 codebase (the most architecturally complete of the
four — full auth flow, providers, repositories) with Phase 9's better
companion-character renderer and iOS/l10n folders merged in.

## What was actually broken (found + fixed)

These aren't cosmetic — they're compile/runtime failures that existed in
the uploaded zips:

1. **Duplicate declaration lines** — `enum MouthShape {`, `enum EmotionState {`,
   `class ApiEndpoints {`, and two more `class` declarations were each
   written twice in a row (e.g. `class ApiEndpoints {\nclass ApiEndpoints {`).
   This is a hard syntax error. Fixed in 5 files.
2. **Missing import** — `companion_screen.dart` used `ChatMessage` /
   `MessageRole` without importing `chat_models.dart`. Fixed.
3. **Phase 9's `companion_character.dart`** imported a `chat_models.dart`
   that didn't exist anywhere in that zip at all. (Not used in this
   build — Phase 8's companion feature was used instead, which is
   internally consistent.)
4. **`Firebase.initializeApp()` called with no config file** — this
   would crash the app on first launch on a real device, since no
   `google-services.json` / `GoogleService-Info.plist` was included and
   no Firebase project is assumed. Replaced with local logging
   (`TelemetryService`); swap it back in if you set up your own Firebase
   project later.
5. **`Hive` cache store used without `Hive.initFlutter()`** — added the
   missing init call in `main.dart`.
6. **`pubspec.yaml` referenced `SpaceGrotesk-Regular.ttf` / `-Medium.ttf`**,
   which don't exist in `assets/fonts/` (only SemiBold + Bold do) — this
   fails the build. Trimmed to the fonts that actually exist.
7. **Unused/conflicting dependencies removed**: `drift`, `drift_flutter`,
   `sqlite3_flutter_libs`, `slang`, `slang_flutter`, `speech_to_text`,
   `flutter_tts`, `firebase_*` — none were referenced in code (verified
   by grep across the whole `lib/` tree), and several would have needed
   extra native setup that wasn't included.
8. **The "Live Conversation" screen was fully fake** — it used
   `Future.delayed()` timers to simulate listening/thinking and returned
   a hardcoded reply. This build's companion flow is real: it records
   real microphone audio, sends it to your backend's STT endpoint, sends
   the transcribed text to your chat/LLM endpoint, and plays back real
   TTS audio with lip-sync driven by the timing your backend returns —
   no simulated delays.

## What was verified, and how (no Flutter SDK was available in the
   environment this was built in — no compiler, no network)

- Every relative import in all 102 `.dart` files resolves to a real file
  (scripted check — zero broken imports).
- Brace/paren/bracket balance checked across every file (catches gross
  structural breakage).
- Every `package:` import in the code cross-checked against
  `pubspec.yaml` — no missing or orphaned dependencies.
- Test files cross-checked against the APIs they call.

**This is not a substitute for actually compiling it.** Before you trust
this as "0 errors", run these yourself — I could not run them here:

```bash
flutter pub get
flutter analyze
flutter test
```

If `flutter analyze` turns up anything (it may — I did a careful manual
pass, not a real type-check), it'll almost certainly be small/local,
not architectural, given the checks above.

## Connecting your backend

Since you already have your own backend, point the app at it with:

```bash
flutter run --dart-define=API_BASE_URL=https://your-backend.example.com
```

(Default is `http://localhost:8000` — see `lib/core/constants/app_constants.dart`.)

The app calls these endpoints (`lib/core/constants/api_endpoints.dart`):

| Endpoint | Method | Purpose | Request | Response |
|---|---|---|---|---|
| `/v1/auth/register` | POST | sign up | see `auth_models.dart` | user + tokens |
| `/v1/auth/login` | POST | sign in | email/password | user + tokens |
| `/v1/auth/refresh` | POST | refresh token | `{refresh_token}` | new tokens |
| `/v1/chat` | POST | AI companion reply | `{user_id, message, session_context}` | see `ChatResponse` below |
| `/v1/stt` | POST (multipart) | speech-to-text | field `audio` = recorded `.m4a` file | `{"text": "...", "confidence": 0.0}` |
| `/v1/tts` | POST | text-to-speech + lip-sync | `{"text": "...", "voice": "..."}` | `{"audio_base64": "...", "viseme_timeline": [{"time":0.12,"viseme":"aa"}, ...]}` |
| `/v1/leaderboard`, `/v1/match`, `/v1/profile`, `/v1/report` | — | social/leaderboard features | see respective adapters | — |

`ChatResponse` shape expected by the app (`lib/data/models/chat_models.dart`):
```json
{
  "success": true,
  "request_id": "...",
  "data": {
    "text": "assistant reply text",
    "audio_url": null,
    "viseme_timeline": [{"time": 0.0, "viseme": "sil"}, {"time": 0.12, "viseme": "aa"}],
    "gesture": "HAPPY",
    "coins_awarded": 10
  }
}
```
If your `/v1/chat` doesn't return `viseme_timeline`/audio directly, leave
it empty — the app automatically falls back to calling `/v1/tts`
separately to get voice + lip-sync for the reply text. Valid `viseme`
values match `lib/features/companion/character/viseme_mouth_shapes.dart`
(`sil, p, b, m, f, v, th, dh, t, d, s, z, n, l, aa, ah, ae, ao, aw, ow,
uw, uh, w, iy, ih, ey, eh, er, r, y, sh, zh, ch, jh, ng, k, g, hh`) and
`gesture` matches `EmotionState` in `emotion_body_states.dart` (`NEUTRAL,
HAPPY, SAD, EXCITED, CALM, ENCOURAGING, CORRECTIVE, CELEBRATORY`).

## Real AI companion — how it works end to end

1. User holds the mic button (`ChatInputBar`) → `AudioService.startRecording()`
   captures real microphone audio to a temp `.m4a` file.
2. On release → `CompanionVoiceAdapter.transcribe()` uploads that file to
   your `/v1/stt`.
3. The transcribed text goes through the normal `/v1/chat` flow (same as
   typed messages) → your LLM.
4. The reply's viseme timeline (from `/v1/chat` or, as fallback, from a
   dedicated `/v1/tts` call) drives `CompanionCharacter`'s mouth shape in
   real time via a `Timer.periodic` synced to actual elapsed playback
   time — not a fixed/simulated animation.
5. `AudioService.playBytes()` plays the real synthesized audio through
   the device speaker at the same time.
6. `gesture`/emotion from the backend changes the character's eyes/body
   language (`EmotionState`) — happy, encouraging, corrective, etc.

## Structure

```
lib/
  core/        theme, constants, widgets, utils — shared across features
  data/        models, adapters (API calls), repositories, services
  features/
    auth/      login, register, forgot password, onboarding, splash
    companion/ the AI character — screen, provider, character renderer
    learning/  curriculum, lesson player, lesson complete
    leaderboard/ social/ profile/ settings/ notifications/
test/          unit + widget tests
android/ ios/  platform projects (mic permission already configured)
```
