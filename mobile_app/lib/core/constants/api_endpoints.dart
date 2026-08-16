/// Backend API endpoint definitions.
/// All endpoints route through the API Gateway (port 8000).
library;

class ApiEndpoints {
  ApiEndpoints._();

  // Base
  static const String base = '/v1';

  // Auth
  static const String register = '$base/auth/register';
  static const String login = '$base/auth/login';
  static const String refresh = '$base/auth/refresh';
  static const String me = '$base/auth/me';

  // Chat / Orchestrator (single entrypoint)
  static const String chat = '$base/chat';

  // Companion voice pipeline (speech-to-text / text-to-speech)
  static const String speechToText = '$base/stt';
  static const String textToSpeech = '$base/tts';

  // Avatar (OpenTalking real-avatar WebRTC session) — served from
  // AppConstants.avatarServiceBaseUrl, NOT `base`/apiBaseUrl, so these
  // are relative to that different root. See avatar_adapter.dart.
  static const String avatarSessions = '$base/sessions';
  static String avatarSessionMessage(final String sessionId) =>
      '$base/sessions/$sessionId/message';
  static String avatarSessionAudio(final String sessionId) =>
      '$base/sessions/$sessionId/audio';
  static String avatarSessionInterrupt(final String sessionId) =>
      '$base/sessions/$sessionId/interrupt';
  static String avatarSession(final String sessionId) =>
      '$base/sessions/$sessionId';

  // Services (via Gateway)
  static const String leaderboard = '$base/leaderboard';
  static const String submitScore = '$base/submit-score';
  static const String socialMatch = '$base/match';
  static const String socialProfile = '$base/profile';
  static const String socialReport = '$base/report';

  // Health
  static const String health = '/health';
  static const String services = '$base/services';
  static const String rateLimit = '$base/rate-limit';
}
