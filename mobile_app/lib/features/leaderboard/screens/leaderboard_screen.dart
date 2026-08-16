import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/utils/extensions.dart';
import 'package:hermes_linguamind/core/widgets/animated_counter.dart';
import 'package:hermes_linguamind/core/widgets/glass_card.dart';
import 'package:hermes_linguamind/core/widgets/loading_shimmer.dart';
import 'package:hermes_linguamind/features/leaderboard/providers/leaderboard_provider.dart';
import 'package:hermes_linguamind/features/leaderboard/widgets/leaderboard_entry_tile.dart';

class LeaderboardScreen extends ConsumerWidget {
  const LeaderboardScreen({super.key});

  static const List<String> _periods = [
    'daily',
    'weekly',
    'monthly',
    'all_time',
  ];

  @override
  Widget build(final BuildContext context, final WidgetRef ref) {
    final state = ref.watch(leaderboardProvider);

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
                  Text('Leaderboard', style: AppTheme.displayLarge),
                  SizedBox(height: 16.h),
                  _buildPeriodSelector(ref, state.selectedPeriod),
                  SizedBox(height: 24.h),
                  if (state.currentUserRank > 0) _buildUserRankCard(state),
                  SizedBox(height: 16.h),
                ],
              ),
            ),
          ),
          if (state.isLoading && state.entries.isEmpty)
            const SliverToBoxAdapter(child: ListShimmer())
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
                if (index >= state.entries.length) {
                  if (state.hasMore) {
                    ref.read(leaderboardProvider.notifier).loadLeaderboard();
                    return const Center(child: CircularProgressIndicator());
                  }
                  return SizedBox(height: 32.h);
                }
                final entry = state.entries[index];
                return LeaderboardEntryTile(entry: entry, index: index)
                    .animate(delay: Duration(milliseconds: index * 50))
                    .fadeIn()
                    .slideX(begin: -0.1, end: 0);
              }, childCount: state.entries.length + (state.hasMore ? 1 : 0)),
            ),
        ],
      ),
    );
  }

  Widget _buildPeriodSelector(final WidgetRef ref, final String selected) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: _periods.map((final period) {
          final isSelected = period == selected;
          return GestureDetector(
            onTap: () =>
                ref.read(leaderboardProvider.notifier).setPeriod(period),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              margin: EdgeInsets.only(right: 8.w),
              padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
              decoration: BoxDecoration(
                gradient: isSelected ? AppTheme.primaryGradient : null,
                color: isSelected ? null : AppTheme.darkSurface,
                borderRadius: BorderRadius.circular(20.r),
                border: Border.all(
                  color: isSelected
                      ? Colors.transparent
                      : AppTheme.borderSubtle,
                ),
              ),
              child: Text(
                period.replaceAll('_', ' ').titleCase,
                style: AppTheme.labelMedium.copyWith(
                  color: isSelected
                      ? AppTheme.textInverse
                      : AppTheme.textSecondary,
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildUserRankCard(final LeaderboardState state) {
    return GlassCard(
      padding: EdgeInsets.all(16.w),
      glowIntensity: 0.3,
      child: Row(
        children: [
          RankBadge(rank: state.currentUserRank, size: 48),
          SizedBox(width: 16.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Your Rank', style: AppTheme.labelMedium),
                SizedBox(height: 4.h),
                Text(
                  state.currentUserRank.ordinal,
                  style: AppTheme.headlineLarge.copyWith(
                    color: AppTheme.violet,
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
            decoration: BoxDecoration(
              color: AppTheme.success.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(20.r),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.trending_up_rounded,
                  size: 14.w,
                  color: AppTheme.success,
                ),
                SizedBox(width: 4.w),
                Text(
                  '+3',
                  style: AppTheme.labelSmall.copyWith(color: AppTheme.success),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
