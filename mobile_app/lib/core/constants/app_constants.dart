/// Global application constants.
library;

class AppConstants {
  AppConstants._();

  // API
  // Points at the unified adapter's api_gateway mount — the adapter is the
  // one port the consolidated backend publishes to the host (8080; also
  // reachable via nginx on :80). See backend/src/adapters/registry.py —
  // api_gateway is mounted at /svc/api-gateway and every relative path in
  // ApiEndpoints (e.g. /v1/auth/login) is forwarded to it unchanged.
  // Android emulators must override this to http://10.0.2.2:8080/svc/api-gateway
  // (localhost inside the emulator refers to the emulator itself, not the host).
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8080/svc/api-gateway',
  );

  // avatar_service (session auth/ownership — our own JWT-protected proxy in
  // front of OpenTalking). Mounted at the gateway ROOT under /svc/avatar,
  // not under /svc/api-gateway like apiBaseUrl above — see
  // backend/gateway/adapters/registry.py. Android emulators: override to
  // http://10.0.2.2:8080/svc/avatar.
  static const String avatarServiceBaseUrl = String.fromEnvironment(
    'AVATAR_SERVICE_BASE_URL',
    defaultValue: 'http://localhost:8080/svc/avatar',
  );

  // OpenTalking's own public WebRTC/SSE endpoint — reached DIRECTLY by
  // this client, NOT through the :8080 gateway. avatar_service returns
  // relative paths like "/avatar-api/sessions/{id}/webrtc/offer"; those
  // are only served by nginx on :80 (see backend/nginx/nginx.conf's
  // `location /avatar-api/` block, proxying to the avatar_api container),
  // because the gateway on :8080 has no route for that prefix and no
  // path to the avatar compose profile's containers. This must point at
  // the nginx-fronted host, which may differ from apiBaseUrl's host in
  // production (e.g. behind different subdomains) — override per
  // environment. Android emulators: http://10.0.2.2.
  static const String avatarPublicBaseUrl = String.fromEnvironment(
    'AVATAR_PUBLIC_BASE_URL',
    defaultValue: 'http://localhost',
  );
  static const Duration apiTimeout = Duration(seconds: 30);
  static const Duration apiConnectTimeout = Duration(seconds: 10);
  static const int maxRetries = 3;

  // Auth
  static const String accessTokenKey = 'hermes_access_token';
  static const String refreshTokenKey = 'hermes_refresh_token';
  static const String tokenExpiryKey = 'hermes_token_expiry';
  static const String userDataKey = 'hermes_user_data';

  // Cache
  static const Duration cacheMaxAge = Duration(hours: 24);
  static const String cacheBoxName = 'hermes_cache';

  // Audio
  static const int audioSampleRate = 16000;
  static const Duration maxRecordingDuration = Duration(minutes: 5);
  static const Duration minRecordingDuration = Duration(seconds: 1);

  // Character Animation
  static const int targetFps = 60;
  static const Duration visemeSyncThreshold = Duration(milliseconds: 80);
  static const int maxCharacterFrameBuildMs = 8;

  // Performance Budgets
  static const Duration maxColdStartMs = Duration(seconds: 2);
  static const int maxAppSizeMb = 50;
  static const double minCrashFreeRate = 0.995;

  // Streak
  static const int streakGraceHours = 48;

  // Coins
  static const int coinsPerLesson = 10;
  static const int coinsPerStreak = 5;
  static const int coinsPerPerfectScore = 20;

  // Notifications
  static const String notificationChannelId = 'hermes_main_channel';
  static const String notificationChannelName = 'Hermes LinguaMind';
  static const String notificationChannelDesc = 'Main notification channel';

  // Pagination
  static const int defaultPageSize = 20;
  static const int maxPageSize = 100;

  // Accessibility
  static const double minContrastRatio = 4.5;
  static const double largeTextScale = 1.3;
}
