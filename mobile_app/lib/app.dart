import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/constants/app_routes.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/features/auth/providers/auth_provider.dart';
import 'package:hermes_linguamind/features/auth/screens/forgot_password_screen.dart';
import 'package:hermes_linguamind/features/auth/screens/login_screen.dart';
import 'package:hermes_linguamind/features/auth/screens/onboarding_screen.dart';
import 'package:hermes_linguamind/features/auth/screens/register_screen.dart';
import 'package:hermes_linguamind/features/auth/screens/splash_screen.dart';
import 'package:hermes_linguamind/features/companion/screens/companion_screen.dart';
import 'package:hermes_linguamind/features/home/screens/home_screen.dart';
import 'package:hermes_linguamind/features/leaderboard/screens/leaderboard_screen.dart';
import 'package:hermes_linguamind/features/learning/screens/curriculum_screen.dart';
import 'package:hermes_linguamind/features/learning/screens/lesson_complete_screen.dart';
import 'package:hermes_linguamind/features/learning/screens/lesson_player_screen.dart';
import 'package:hermes_linguamind/features/notifications/screens/notifications_screen.dart';
import 'package:hermes_linguamind/features/profile/screens/edit_profile_screen.dart';
import 'package:hermes_linguamind/features/profile/screens/profile_screen.dart';
import 'package:hermes_linguamind/features/settings/screens/appearance_screen.dart';
import 'package:hermes_linguamind/features/settings/screens/notifications_settings_screen.dart';
import 'package:hermes_linguamind/features/settings/screens/settings_screen.dart';
import 'package:hermes_linguamind/features/showcase/screens/ui_showcase_screen.dart';
import 'package:hermes_linguamind/features/social/screens/match_screen.dart';
import 'package:hermes_linguamind/features/social/screens/social_screen.dart';

class HermesApp extends ConsumerWidget {
  const HermesApp({super.key});

  @override
  Widget build(final BuildContext context, final WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return ScreenUtilInit(
      designSize: const Size(375, 812),
      minTextAdapt: true,
      splitScreenMode: true,
      builder: (final context, final child) {
        return MaterialApp.router(
          title: 'Hermes LinguaMind',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.darkTheme,
          darkTheme: AppTheme.darkTheme,
          themeMode: ThemeMode.dark,
          routerConfig: router,
          builder: (final context, final child) {
            return MediaQuery(
              data: MediaQuery.of(context).copyWith(
                textScaler: TextScaler.linear(
                  MediaQuery.of(context).textScaler.scale(1).clamp(0.8, 1.4),
                ),
              ),
              child: child!,
            );
          },
        );
      },
    );
  }
}

/// Bridges Riverpod's [authStateProvider] to GoRouter's `refreshListenable`
/// *without* rebuilding the [GoRouter] instance itself.
///
/// Bug this fixes: the router used to be built with
/// `final authState = ref.watch(authStateProvider);` directly inside the
/// `Provider<GoRouter>` body. Every auth state change (e.g. `loading` while
/// signing in, then `data` once signed in) made Riverpod recompute the
/// *entire* provider, which constructed a brand-new `GoRouter` — and a new
/// `GoRouter` always starts back at `initialLocation` (the splash screen).
/// From the outside this looked like "I type my password, hit Sign In, and
/// the app just jumps back to the very start" — the login network call was
/// actually succeeding, but the router underneath the screen was being
/// thrown away and recreated before anyone could see the result.
///
/// The fix: build [GoRouter] exactly once (`Provider` body only reads
/// `ref`, never watches anything), and instead pass a [ChangeNotifier]
/// that fires `notifyListeners()` on every auth change. GoRouter's
/// `refreshListenable` re-runs `redirect` on the *same* router/navigator
/// when that fires — which is what actually takes you from the login
/// screen to Home once `isAuthenticated` flips to true.
class _AuthRouterRefresh extends ChangeNotifier {
  _AuthRouterRefresh(this._ref) {
    _subscription = _ref.listen<AsyncValue<AuthState>>(
      authStateProvider,
      (final _, final _) => notifyListeners(),
    );
  }

  final Ref _ref;
  late final ProviderSubscription<AsyncValue<AuthState>> _subscription;

  @override
  void dispose() {
    _subscription.close();
    super.dispose();
  }
}

final routerProvider = Provider<GoRouter>((final ref) {
  final refresh = _AuthRouterRefresh(ref);
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: AppRoutes.splash,
    refreshListenable: refresh,
    redirect: (final context, final state) {
      // Read the CURRENT auth state at redirect-time — not a value
      // captured once when the router was built.
      final authState = ref.read(authStateProvider);
      final isAuthenticated = authState.valueOrNull?.isAuthenticated ?? false;
      final isAuthRoute =
          state.matchedLocation == AppRoutes.login ||
          state.matchedLocation == AppRoutes.register ||
          state.matchedLocation == AppRoutes.forgotPassword ||
          state.matchedLocation == AppRoutes.onboarding;

      if (!isAuthenticated &&
          !isAuthRoute &&
          state.matchedLocation != AppRoutes.splash) {
        return AppRoutes.login;
      }

      if (isAuthenticated && isAuthRoute) {
        return AppRoutes.home;
      }

      return null;
    },
    routes: [
      GoRoute(
        path: AppRoutes.splash,
        builder: (final context, final state) => const SplashScreen(),
      ),
      GoRoute(
        path: AppRoutes.onboarding,
        builder: (final context, final state) => const OnboardingScreen(),
      ),
      GoRoute(
        path: AppRoutes.login,
        builder: (final context, final state) => const LoginScreen(),
      ),
      GoRoute(
        path: AppRoutes.register,
        builder: (final context, final state) => const RegisterScreen(),
      ),
      GoRoute(
        path: AppRoutes.forgotPassword,
        builder: (final context, final state) => const ForgotPasswordScreen(),
      ),
      GoRoute(
        path: AppRoutes.home,
        builder: (final context, final state) => const HomeScreen(),
      ),
      GoRoute(
        path: AppRoutes.curriculum,
        builder: (final context, final state) => const CurriculumScreen(),
      ),
      GoRoute(
        path: AppRoutes.lessonPlayer,
        builder: (final context, final state) {
          final lessonId = state.uri.queryParameters['lessonId'] ?? '';
          return LessonPlayerScreen(lessonId: lessonId);
        },
      ),
      GoRoute(
        path: AppRoutes.lessonComplete,
        builder: (final context, final state) {
          final extra = state.extra as Map<String, dynamic>?;
          return LessonCompleteScreen(
            lessonId: extra?['lessonId'] as String? ?? '',
            xpEarned: extra?['xpEarned'] as int? ?? 0,
            coinsEarned: extra?['coinsEarned'] as int? ?? 0,
            streakDays: extra?['streakDays'] as int? ?? 0,
          );
        },
      ),
      GoRoute(
        path: AppRoutes.companion,
        builder: (final context, final state) => const CompanionScreen(),
      ),
      GoRoute(
        path: AppRoutes.leaderboard,
        builder: (final context, final state) => const LeaderboardScreen(),
      ),
      GoRoute(
        path: AppRoutes.social,
        builder: (final context, final state) => const SocialScreen(),
      ),
      GoRoute(
        path: AppRoutes.match,
        builder: (final context, final state) {
          final matchId = state.uri.queryParameters['matchId'] ?? '';
          return MatchScreen(matchId: matchId);
        },
      ),
      GoRoute(
        path: AppRoutes.profile,
        builder: (final context, final state) => const ProfileScreen(),
      ),
      GoRoute(
        path: AppRoutes.editProfile,
        builder: (final context, final state) => const EditProfileScreen(),
      ),
      GoRoute(
        path: AppRoutes.settings,
        builder: (final context, final state) => const SettingsScreen(),
      ),
      GoRoute(
        path: AppRoutes.appearance,
        builder: (final context, final state) => const AppearanceScreen(),
      ),
      GoRoute(
        path: AppRoutes.uiShowcase,
        builder: (final context, final state) => const UiShowcaseScreen(),
      ),
      GoRoute(
        path: AppRoutes.notificationSettings,
        builder: (final context, final state) =>
            const NotificationsSettingsScreen(),
      ),
      GoRoute(
        path: AppRoutes.notifications,
        builder: (final context, final state) => const NotificationsScreen(),
      ),
    ],
  );
});
