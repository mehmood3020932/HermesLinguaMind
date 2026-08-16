import 'package:confetti/confetti.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/constants/app_routes.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/widgets/animated_counter.dart';
import 'package:hermes_linguamind/core/widgets/primary_button.dart';

class LessonCompleteScreen extends StatefulWidget {
  const LessonCompleteScreen({
    required this.lessonId,
    required this.xpEarned,
    required this.coinsEarned,
    required this.streakDays,
    super.key,
  });

  final String lessonId;
  final int xpEarned;
  final int coinsEarned;
  final int streakDays;

  @override
  State<LessonCompleteScreen> createState() => _LessonCompleteScreenState();
}

class _LessonCompleteScreenState extends State<LessonCompleteScreen> {
  late ConfettiController _confettiController;

  @override
  void initState() {
    super.initState();
    _confettiController = ConfettiController(
      duration: const Duration(seconds: 3),
    );
    Future<void>.delayed(const Duration(milliseconds: 300), () {
      _confettiController.play();
    });
  }

  @override
  void dispose() {
    _confettiController.dispose();
    super.dispose();
  }

  @override
  Widget build(final BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      body: Stack(
        alignment: Alignment.center,
        children: [
          SafeArea(
            child: Padding(
              padding: EdgeInsets.all(24.w),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 100.w,
                    height: 100.h,
                    decoration: BoxDecoration(
                      gradient: AppTheme.primaryGradient,
                      borderRadius: BorderRadius.circular(30.r),
                      boxShadow: [
                        BoxShadow(
                          color: AppTheme.violet.withValues(alpha: 0.4),
                          blurRadius: 30,
                          spreadRadius: 5,
                        ),
                      ],
                    ),
                    child: Icon(
                      Icons.check_rounded,
                      size: 50.w,
                      color: AppTheme.textInverse,
                    ),
                  ).animate().scale(
                    begin: Offset.zero,
                    end: const Offset(1, 1),
                    duration: const Duration(milliseconds: 600),
                    curve: Curves.elasticOut,
                  ),
                  SizedBox(height: 32.h),
                  Text('Lesson Complete!', style: AppTheme.displayLarge)
                      .animate(delay: const Duration(milliseconds: 200))
                      .fadeIn()
                      .slideY(begin: 0.3, end: 0),
                  SizedBox(height: 8.h),
                  Text(
                    'Great job! Keep up the momentum.',
                    style: AppTheme.bodyMedium,
                  ).animate(delay: const Duration(milliseconds: 400)).fadeIn(),
                  SizedBox(height: 48.h),
                  Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          _buildRewardCard(
                            icon: Icons.star_rounded,
                            value: widget.xpEarned,
                            label: 'XP Earned',
                            color: AppTheme.violet,
                          ),
                          SizedBox(width: 16.w),
                          _buildRewardCard(
                            icon: Icons.monetization_on_rounded,
                            value: widget.coinsEarned,
                            label: 'Coins',
                            color: AppTheme.aqua,
                          ),
                          SizedBox(width: 16.w),
                          _buildRewardCard(
                            icon: Icons.local_fire_department_rounded,
                            value: widget.streakDays,
                            label: 'Day Streak',
                            color: AppTheme.warning,
                          ),
                        ],
                      )
                      .animate(delay: const Duration(milliseconds: 600))
                      .fadeIn()
                      .slideY(begin: 0.3, end: 0),
                  SizedBox(height: 48.h),
                  PrimaryButton(
                    label: 'Continue',
                    onPressed: () => context.go(AppRoutes.home),
                  ).animate(delay: const Duration(milliseconds: 800)).fadeIn(),
                ],
              ),
            ),
          ),
          ConfettiWidget(
            confettiController: _confettiController,
            blastDirectionality: BlastDirectionality.explosive,
            emissionFrequency: 0.05,
            numberOfParticles: 50,
            colors: const [
              AppTheme.violet,
              AppTheme.aqua,
              AppTheme.warning,
              AppTheme.success,
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRewardCard({
    required final IconData icon,
    required final int value,
    required final String label,
    required final Color color,
  }) {
    return Container(
      width: 100.w,
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 28.w),
          SizedBox(height: 8.h),
          AnimatedCounter(
            value: value,
            style: AppTheme.headlineLarge.copyWith(color: color),
          ),
          SizedBox(height: 4.h),
          Text(label, style: AppTheme.labelSmall),
        ],
      ),
    );
  }
}
