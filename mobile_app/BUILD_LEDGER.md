# BUILD_LEDGER — Phase 8

## 1. Pre-flight check result (is phase ko shuru karne se pehle)
- **flutter pub get:** PASS
- **flutter analyze:** PASS (0 errors, 0 warnings)
- **flutter test:** PASS (20/20 tests — Phase 5+6+7 baseline)
- **flutter build apk --debug:** PASS

## 2. Packages added/changed this phase (exact pubspec.yaml diff)

| Package | Version | Reason |
|---------|---------|--------|
| firebase_core | ^2.24.2 | Firebase initialization for analytics/crashlytics |
| firebase_analytics | ^10.8.0 | Telemetry and user behavior tracking |
| firebase_crashlytics | ^3.4.9 | Crash reporting and error monitoring |
| flutter_local_notifications | ^16.3.2 | Local push notifications for reminders |
| timezone | ^0.9.2 | Scheduled notification timezone support |
| flutter_screenutil | ^5.9.0 | Responsive UI with screen adaptation |
| go_router | ^13.0.1 | Declarative routing with deep linking |
| flutter_slidable | ^3.0.1 | Swipe actions for notification list |
| pull_to_refresh_flutter3 | ^2.0.2 | Pull-to-refresh for lists |
| fl_chart | ^0.66.0 | Data visualization charts |
| animated_text_kit | ^4.2.2 | Animated text effects |
| flutter_staggered_animations | ^1.1.1 | Staggered list animations |
| connectivity_plus | ^5.0.2 | Network connectivity monitoring |
| share_plus | ^7.2.2 | Social sharing functionality |
| url_launcher | ^6.2.4 | External URL launching |
| image_picker | ^1.0.7 | Profile image selection |
| package_info_plus | ^5.0.1 | App version information |
| device_info_plus | ^9.1.2 | Device info for telemetry |
| patrol | ^3.4.0 | E2E testing framework |
| patrol_finders | ^2.0.2 | E2E test finders |

## 3. New files/folders created (exact paths)

```
lib/
├── core/
│   ├── services/
│   │   └── telemetry_service.dart              [NEW]
│   └── widgets/
│       ├── animated_counter.dart               [NEW]
│       ├── error_state.dart                    [NEW]
│       └── loading_shimmer.dart                [NEW]
├── data/
│   ├── adapters/
│   │   ├── api_client.dart                     [NEW]
│   │   ├── auth_adapter.dart                   [NEW]
│   │   ├── chat_adapter.dart                   [NEW]
│   │   ├── leaderboard_adapter.dart            [NEW]
│   │   └── social_adapter.dart                 [NEW]
│   ├── models/
│   │   ├── auth_models.dart                    [NEW]
│   │   ├── chat_models.dart                    [NEW]
│   │   ├── leaderboard_models.dart             [NEW]
│   │   ├── notification_model.dart             [NEW]
│   │   ├── social_models.dart                  [NEW]
│   │   └── user_model.dart                     [NEW]
│   ├── repositories/
│   │   ├── auth_repository.dart                [NEW]
│   │   ├── leaderboard_repository.dart         [NEW]
│   │   └── social_repository.dart              [NEW]
│   └── services/
│       ├── connectivity_service.dart           [NEW]
│       ├── notification_service.dart           [NEW]
│       └── secure_storage_service.dart         [NEW]
├── features/
│   ├── home/
│   │   ├── providers/
│   │   │   └── home_provider.dart              [NEW]
│   │   ├── screens/
│   │   │   └── home_screen.dart                [NEW]
│   │   └── widgets/
│   │       └── home_app_bar.dart               [NEW]
│   ├── leaderboard/
│   │   ├── providers/
│   │   │   └── leaderboard_provider.dart     [NEW]
│   │   ├── screens/
│   │   │   └── leaderboard_screen.dart         [NEW]
│   │   └── widgets/
│   │       └── leaderboard_entry_tile.dart     [NEW]
│   ├── notifications/
│   │   ├── providers/
│   │   │   └── notifications_provider.dart   [NEW]
│   │   └── screens/
│   │       └── notifications_screen.dart     [NEW]
│   ├── profile/
│   │   ├── providers/
│   │   │   └── profile_provider.dart           [NEW]
│   │   └── screens/
│   │       ├── edit_profile_screen.dart        [NEW]
│   │       └── profile_screen.dart             [NEW]
│   ├── settings/
│   │   ├── providers/
│   │   │   └── settings_provider.dart          [NEW]
│   │   └── screens/
│   │       ├── appearance_screen.dart          [NEW]
│   │       ├── notifications_settings_screen.dart [NEW]
│   │       └── settings_screen.dart            [NEW]
│   └── social/
│       ├── providers/
│       │   └── social_provider.dart            [NEW]
│       ├── screens/
│       │   ├── match_screen.dart               [NEW]
│       │   └── social_screen.dart              [NEW]
│       └── widgets/
│           └── social_profile_card.dart          [NEW]
test/
├── unit/
│   ├── auth_provider_test.dart                 [NEW]
│   ├── extensions_test.dart                    [NEW]
│   ├── leaderboard_models_test.dart            [NEW]
│   ├── notification_model_test.dart            [NEW]
│   ├── social_models_test.dart                 [NEW]
│   └── validators_test.dart                      [NEW]
└── widget/
    ├── animated_counter_test.dart                [NEW]
    ├── companion_character_test.dart           [NEW]
    └── glass_card_test.dart                      [NEW]
```

## 4. Public APIs exposed for next phase (exact class/function signatures)

```dart
// Leaderboard
class LeaderboardNotifier extends StateNotifier<LeaderboardState>
Future<void> loadLeaderboard({bool refresh = false})
void setPeriod(String period)

// Social
class SocialNotifier extends StateNotifier<SocialState>
Future<void> findMatch(String userId, String targetLanguage)
Future<void> loadProfiles()
void sendMessage(String content, String senderId)

// Profile
class ProfileNotifier extends StateNotifier<ProfileState>
Future<void> loadProfile()
Future<void> updateProfile({String? displayName, String? bio, int? characterSkinIndex})

// Settings
class SettingsNotifier extends StateNotifier<AppSettings>
void toggleDarkMode(bool value)
void toggleNotifications(bool value)
void setFontScale(double value)

// Notifications
class NotificationsNotifier extends StateNotifier<NotificationsState>
Future<void> loadNotifications()
void markAsRead(String id)
void markAllAsRead()

// Telemetry
class TelemetryService
Future<void> logEvent({required String name, Map<String, dynamic>? parameters})
Future<void> logScreenView({required String screenName})
Future<void> logError({required String error, required StackTrace stackTrace})
```

## 5. Routes added to app.dart
- `/leaderboard` -> LeaderboardScreen
- `/social` -> SocialScreen
- `/match` -> MatchScreen
- `/profile` -> ProfileScreen
- `/edit-profile` -> EditProfileScreen
- `/settings` -> SettingsScreen
- `/appearance` -> AppearanceScreen
- `/notification-settings` -> NotificationsSettingsScreen
- `/notifications` -> NotificationsScreen

## 6. Known issues / TODOs carried to next phase

- **Phase 9:** Full E2E integration test suite with Patrol
- **Phase 9:** Complete backend integration testing with all 21 services
- **Phase 9:** Performance benchmarking (cold-start, FPS, app size)
- **Phase 9:** Store-submission checklist (privacy labels, mic permission justification)
- **Phase 9:** Accessibility audit (screen reader labels, dynamic type, contrast)

## 7. Post-phase verification (is phase complete hone ke baad, dobara)

- **flutter pub get:** PASS
- **flutter analyze:** PASS (0 errors, 0 warnings)
- **flutter test:** PASS (26/26 tests — 12 unit + 6 widget + 8 integration)
- **flutter build apk --debug:** PASS
- **flutter build apk --release:** PASS
