import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/constants/app_routes.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/features/auth/providers/auth_provider.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    );
    _controller.forward();
    _navigateAfterDelay();
  }

  Future<void> _navigateAfterDelay() async {
    await Future<void>.delayed(const Duration(seconds: 3));
    if (!mounted) return;
    ref.read(authStateProvider).whenOrNull(
      data: (final state) {
        if (state.isAuthenticated) {
          context.go(AppRoutes.home);
        } else {
          context.go(AppRoutes.onboarding);
        }
      },
      error: (_, _) => context.go(AppRoutes.onboarding),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(final BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
                  width: 120.w,
                  height: 120.h,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(28.r),
                    boxShadow: [
                      BoxShadow(
                        color: AppTheme.violet.withValues(alpha: 0.45),
                        blurRadius: 36,
                        spreadRadius: 4,
                      ),
                    ],
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(28.r),
                    child: Image.asset(
                      'assets/images/app_icon_1024.png',
                      fit: BoxFit.cover,
                    ),
                  ),
                )
                .animate(controller: _controller)
                .scale(
                  begin: const Offset(0.5, 0.5),
                  end: const Offset(1, 1),
                  duration: const Duration(milliseconds: 800),
                  curve: Curves.elasticOut,
                )
                .then()
                .shimmer(duration: const Duration(milliseconds: 1200)),
            SizedBox(height: 32.h),
            Text(
                  'Hermes',
                  style: AppTheme.displayLarge.copyWith(
                    fontSize: 48.sp,
                    foreground: Paint()
                      ..shader = AppTheme.primaryGradient.createShader(
                        Rect.fromLTWH(0, 0, 200.w, 60.h),
                      ),
                  ),
                )
                .animate(delay: const Duration(milliseconds: 500))
                .fadeIn(duration: const Duration(milliseconds: 800)),
            SizedBox(height: 8.h),
            Text(
                  'LinguaMind',
                  style: AppTheme.headlineLarge.copyWith(
                    color: AppTheme.textSecondary,
                    letterSpacing: 4,
                  ),
                )
                .animate(delay: const Duration(milliseconds: 700))
                .fadeIn(duration: const Duration(milliseconds: 800)),
            SizedBox(height: 48.h),
            SizedBox(
              width: 40.w,
              height: 40.h,
              child: const CircularProgressIndicator(
                strokeWidth: 3,
                valueColor: AlwaysStoppedAnimation<Color>(AppTheme.violet),
              ),
            ).animate(delay: const Duration(milliseconds: 1000)).fadeIn(),
          ],
        ),
      ),
    );
  }
}
