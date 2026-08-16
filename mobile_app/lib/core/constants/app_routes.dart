/// Application route constants for deep linking and navigation.
library;

class AppRoutes {
  AppRoutes._();

  // Auth
  static const String splash = '/';
  static const String onboarding = '/onboarding';
  static const String login = '/login';
  static const String register = '/register';
  static const String forgotPassword = '/forgot-password';

  // Home & Core
  static const String home = '/home';
  static const String curriculum = '/curriculum';
  static const String lessonPlayer = '/lesson-player';
  static const String lessonComplete = '/lesson-complete';
  static const String companion = '/companion';

  // Social & Leaderboard
  static const String leaderboard = '/leaderboard';
  static const String social = '/social';
  static const String match = '/match';

  // Profile & Settings
  static const String profile = '/profile';
  static const String editProfile = '/edit-profile';
  static const String settings = '/settings';
  static const String appearance = '/appearance';
  static const String uiShowcase = '/ui-showcase';
  static const String notificationSettings = '/notification-settings';
  static const String notifications = '/notifications';
}
