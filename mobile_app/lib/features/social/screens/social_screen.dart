import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/constants/app_routes.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/widgets/glass_card.dart';
import 'package:hermes_linguamind/core/widgets/loading_shimmer.dart';
import 'package:hermes_linguamind/features/social/providers/social_provider.dart';
import 'package:hermes_linguamind/features/social/widgets/social_profile_card.dart';

class SocialScreen extends ConsumerStatefulWidget {
  const SocialScreen({super.key});

  @override
  ConsumerState<SocialScreen> createState() => _SocialScreenState();
}

class _SocialScreenState extends ConsumerState<SocialScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(socialProvider.notifier).loadProfiles());
  }

  @override
  Widget build(final BuildContext context) {
    final state = ref.watch(socialProvider);

    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      body: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(
            child: Padding(
              padding: EdgeInsets.all(16.w),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Community', style: AppTheme.displayLarge),
                  SizedBox(height: 8.h),
                  Text(
                    'Connect with language learners worldwide',
                    style: AppTheme.bodyMedium,
                  ),
                  SizedBox(height: 24.h),
                  _buildMatchCard(context, ref),
                  SizedBox(height: 24.h),
                  Text('Active Learners', style: AppTheme.headlineLarge),
                  SizedBox(height: 16.h),
                ],
              ),
            ),
          ),
          if (state.isLoading)
            const SliverToBoxAdapter(child: ListShimmer(itemCount: 3))
          else if (state.error != null)
            SliverToBoxAdapter(
              child: Center(
                child: Padding(
                  padding: EdgeInsets.all(32.w),
                  child: Text(
                    state.error!,
                    style: AppTheme.bodyMedium.copyWith(color: AppTheme.error),
                  ),
                ),
              ),
            )
          else
            SliverList(
              delegate: SliverChildBuilderDelegate((
                final context,
                final index,
              ) {
                final profile = state.profiles[index];
                return SocialProfileCard(
                      profile: profile,
                      onTap: () => context.push(
                        '${AppRoutes.match}?matchId=${profile.userId}',
                      ),
                    )
                    .animate(delay: Duration(milliseconds: index * 100))
                    .fadeIn()
                    .slideY(begin: 0.2, end: 0);
              }, childCount: state.profiles.length),
            ),
          SliverPadding(padding: EdgeInsets.only(bottom: 32.h)),
        ],
      ),
    );
  }

  Widget _buildMatchCard(final BuildContext context, final WidgetRef ref) {
    return GlassCard(
      padding: EdgeInsets.all(20.w),
      glowIntensity: 0.2,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 48.w,
                height: 48.h,
                decoration: BoxDecoration(
                  gradient: AppTheme.primaryGradient,
                  borderRadius: BorderRadius.circular(14.r),
                ),
                child: Icon(
                  Icons.people_alt_rounded,
                  size: 24.w,
                  color: AppTheme.textInverse,
                ),
              ),
              SizedBox(width: 16.w),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Find a Partner', style: AppTheme.headlineMedium),
                    SizedBox(height: 4.h),
                    Text(
                      'Match with someone learning the same language',
                      style: AppTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
          ),
          SizedBox(height: 16.h),
          Container(
            width: double.infinity,
            padding: EdgeInsets.symmetric(vertical: 14.h),
            decoration: BoxDecoration(
              gradient: AppTheme.primaryGradient,
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: GestureDetector(
              onTap: () => ref
                  .read(socialProvider.notifier)
                  .findMatch('user_test_1', 'en'),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.shuffle_rounded,
                    size: 20.w,
                    color: AppTheme.textInverse,
                  ),
                  SizedBox(width: 8.w),
                  Text(
                    'Start Matching',
                    style: AppTheme.labelLarge.copyWith(
                      color: AppTheme.textInverse,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
