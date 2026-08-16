import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/constants/app_routes.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/widgets/primary_button.dart';
import 'package:smooth_page_indicator/smooth_page_indicator.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<_OnboardingPage> _pages = [
    const _OnboardingPage(
      icon: Icons.language_rounded,
      title: 'Learn Any Language',
      description:
          'Master new languages with AI-powered personalized lessons tailored to your level and goals.',
    ),
    const _OnboardingPage(
      icon: Icons.mic_rounded,
      title: 'Speak with Confidence',
      description:
          'Practice real conversations with our AI companion. Get instant feedback on pronunciation and grammar.',
    ),
    const _OnboardingPage(
      icon: Icons.people_rounded,
      title: 'Connect & Compete',
      description:
          'Join a global community. Match with language partners and climb the leaderboard.',
    ),
    const _OnboardingPage(
      icon: Icons.emoji_events_rounded,
      title: 'Track Your Progress',
      description:
          'Earn coins, maintain streaks, and watch your fluency grow with detailed analytics.',
    ),
  ];

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(final BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      body: SafeArea(
        child: Column(
          children: [
            Align(
              alignment: Alignment.topRight,
              child: TextButton(
                onPressed: () => context.go(AppRoutes.login),
                child: Text(
                  'Skip',
                  style: AppTheme.labelMedium.copyWith(
                    color: AppTheme.textTertiary,
                  ),
                ),
              ),
            ),
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                onPageChanged: (final index) =>
                    setState(() => _currentPage = index),
                itemCount: _pages.length,
                itemBuilder: (final context, final index) =>
                    _buildPage(_pages[index], index),
              ),
            ),
            Padding(
              padding: EdgeInsets.all(24.w),
              child: Column(
                children: [
                  SmoothPageIndicator(
                    controller: _pageController,
                    count: _pages.length,
                    effect: WormEffect(
                      dotWidth: 10.w,
                      dotHeight: 10.h,
                      spacing: 8.w,
                      dotColor: AppTheme.darkSurfaceHover,
                      activeDotColor: AppTheme.violet,
                    ),
                  ),
                  SizedBox(height: 32.h),
                  PrimaryButton(
                    label: _currentPage == _pages.length - 1
                        ? 'Get Started'
                        : 'Next',
                    onPressed: () {
                      if (_currentPage == _pages.length - 1) {
                        context.go(AppRoutes.login);
                      } else {
                        _pageController.nextPage(
                          duration: const Duration(milliseconds: 400),
                          curve: Curves.easeInOut,
                        );
                      }
                    },
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPage(final _OnboardingPage page, final int index) {
    return Padding(
      padding: EdgeInsets.all(32.w),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
                width: 160.w,
                height: 160.h,
                decoration: BoxDecoration(
                  gradient: AppTheme.primaryGradient,
                  borderRadius: BorderRadius.circular(40.r),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.violet.withValues(alpha: 0.3),
                      blurRadius: 40,
                      spreadRadius: 5,
                    ),
                  ],
                ),
                child: Icon(page.icon, size: 80.w, color: AppTheme.textInverse),
              )
              .animate()
              .scale(
                begin: const Offset(0.5, 0.5),
                end: const Offset(1, 1),
                duration: const Duration(milliseconds: 600),
                curve: Curves.elasticOut,
              )
              .fadeIn(duration: const Duration(milliseconds: 400)),
          SizedBox(height: 48.h),
          Text(
                page.title,
                style: AppTheme.displayMedium,
                textAlign: TextAlign.center,
              )
              .animate(delay: const Duration(milliseconds: 200))
              .fadeIn()
              .slideY(begin: 0.3, end: 0),
          SizedBox(height: 16.h),
          Text(
                page.description,
                style: AppTheme.bodyLarge.copyWith(
                  color: AppTheme.textSecondary,
                ),
                textAlign: TextAlign.center,
              )
              .animate(delay: const Duration(milliseconds: 400))
              .fadeIn()
              .slideY(begin: 0.3, end: 0),
        ],
      ),
    );
  }
}

class _OnboardingPage {
  const _OnboardingPage({
    required this.icon,
    required this.title,
    required this.description,
  });
  final IconData icon;
  final String title;
  final String description;
}
