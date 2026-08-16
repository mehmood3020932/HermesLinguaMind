import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/widgets/glass_card.dart';
import 'package:hermes_linguamind/core/widgets/primary_button.dart';
import 'package:hermes_linguamind/data/models/social_models.dart';
import 'package:hermes_linguamind/features/social/providers/social_provider.dart';

class MatchScreen extends ConsumerWidget {
  const MatchScreen({required this.matchId, super.key});
  final String matchId;

  @override
  Widget build(final BuildContext context, final WidgetRef ref) {
    final state = ref.watch(socialProvider);
    final match = state.currentMatch;

    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
          onPressed: context.pop,
        ),
        title: Text('Match', style: AppTheme.headlineLarge),
      ),
      body: match == null
          ? const Center(child: CircularProgressIndicator())
          : SafeArea(
              child: Padding(
                padding: EdgeInsets.all(24.w),
                child: Column(
                  children: [
                    _buildMatchProfile(match),
                    SizedBox(height: 32.h),
                    _buildCompatibility(match),
                    SizedBox(height: 32.h),
                    _buildCommonLanguages(match),
                    const Spacer(),
                    PrimaryButton(
                      label: 'Start Conversation',
                      onPressed: () {
                        // Navigate to conversation
                      },
                    ),
                    SizedBox(height: 12.h),
                    TextButton(
                      onPressed: () {
                        ref.read(socialProvider.notifier).clearMatch();
                        ref
                            .read(socialProvider.notifier)
                            .findMatch('user_test_1', 'en');
                      },
                      child: Text(
                        'Find Another Match',
                        style: AppTheme.labelMedium.copyWith(
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildMatchProfile(final MatchResult match) {
    return Column(
      children: [
        Container(
          width: 100.w,
          height: 100.h,
          decoration: BoxDecoration(
            gradient: AppTheme.primaryGradient,
            borderRadius: BorderRadius.circular(30.r),
            boxShadow: [
              BoxShadow(
                color: AppTheme.violet.withValues(alpha: 0.3),
                blurRadius: 20,
                spreadRadius: 5,
              ),
            ],
          ),
          child: Center(
            child: Text(
              match.partner.displayName.isNotEmpty
                  ? match.partner.displayName[0].toUpperCase()
                  : '?',
              style: AppTheme.displayLarge.copyWith(
                color: AppTheme.textInverse,
              ),
            ),
          ),
        ),
        SizedBox(height: 16.h),
        Text(match.partner.displayName, style: AppTheme.headlineLarge),
        SizedBox(height: 4.h),
        Text('@${match.partner.username}', style: AppTheme.bodyMedium),
      ],
    );
  }

  Widget _buildCompatibility(final MatchResult match) {
    final score = (match.compatibilityScore * 100).toInt();
    return GlassCard(
      padding: EdgeInsets.all(20.w),
      child: Column(
        children: [
          Text('Compatibility', style: AppTheme.labelMedium),
          SizedBox(height: 12.h),
          Stack(
            alignment: Alignment.center,
            children: [
              SizedBox(
                width: 120.w,
                height: 120.h,
                child: CircularProgressIndicator(
                  value: match.compatibilityScore,
                  strokeWidth: 8,
                  backgroundColor: AppTheme.darkElevated,
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    AppTheme.violet,
                  ),
                ),
              ),
              Text(
                '$score%',
                style: AppTheme.displayMedium.copyWith(color: AppTheme.violet),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCommonLanguages(final MatchResult match) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Common Languages', style: AppTheme.labelMedium),
        SizedBox(height: 12.h),
        Wrap(
          spacing: 8.w,
          children: match.commonLanguages.map((final String lang) {
            return Chip(
              label: Text(
                lang.toUpperCase(),
                style: AppTheme.labelSmall.copyWith(color: AppTheme.violet),
              ),
              backgroundColor: AppTheme.violet.withValues(alpha: 0.1),
              side: BorderSide(color: AppTheme.violet.withValues(alpha: 0.3)),
            );
          }).toList(),
        ),
      ],
    );
  }
}
