import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/utils/extensions.dart';
import 'package:hermes_linguamind/data/models/leaderboard_models.dart';

class LeaderboardEntryTile extends StatelessWidget {
  const LeaderboardEntryTile({
    required this.entry,
    required this.index,
    super.key,
  });

  final LeaderboardEntry entry;
  final int index;

  Color get _rankColor {
    if (entry.rank == 1) return const Color(0xFFFFD700);
    if (entry.rank == 2) return const Color(0xFFC0C0C0);
    if (entry.rank == 3) return const Color(0xFFCD7F32);
    return AppTheme.textSecondary;
  }

  @override
  Widget build(final BuildContext context) {
    final isTopThree = entry.rank <= 3;

    return Container(
      margin: EdgeInsets.symmetric(horizontal: 16.w, vertical: 4.h),
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: entry.isCurrentUser
            ? AppTheme.violet.withValues(alpha: 0.1)
            : AppTheme.darkSurface,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(
          color: entry.isCurrentUser
              ? AppTheme.violet.withValues(alpha: 0.3)
              : isTopThree
              ? _rankColor.withValues(alpha: 0.3)
              : AppTheme.borderSubtle,
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 36.w,
            height: 36.h,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isTopThree
                  ? _rankColor.withValues(alpha: 0.15)
                  : Colors.transparent,
              border: Border.all(
                color: isTopThree ? _rankColor : Colors.transparent,
                width: 2,
              ),
            ),
            child: Center(
              child: Text(
                entry.rank.toString(),
                style: AppTheme.labelLarge.copyWith(
                  color: isTopThree ? _rankColor : AppTheme.textSecondary,
                ),
              ),
            ),
          ),
          SizedBox(width: 16.w),
          Container(
            width: 44.w,
            height: 44.h,
            decoration: BoxDecoration(
              gradient: AppTheme.primaryGradient,
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: Center(
              child: Text(
                entry.displayName.isNotEmpty
                    ? entry.displayName[0].toUpperCase()
                    : '?',
                style: AppTheme.headlineMedium.copyWith(
                  color: AppTheme.textInverse,
                ),
              ),
            ),
          ),
          SizedBox(width: 12.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  entry.displayName,
                  style: AppTheme.bodyLarge.copyWith(
                    fontWeight: FontWeight.w600,
                    color: entry.isCurrentUser
                        ? AppTheme.violet
                        : AppTheme.textPrimary,
                  ),
                ),
                SizedBox(height: 2.h),
                Text('@${entry.username}', style: AppTheme.bodySmall),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.star_rounded, size: 14.w, color: AppTheme.warning),
                  SizedBox(width: 4.w),
                  Text(
                    entry.xp.compact,
                    style: AppTheme.labelLarge.copyWith(
                      color: AppTheme.warning,
                    ),
                  ),
                ],
              ),
              SizedBox(height: 2.h),
              if (entry.rankChange != 0)
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      entry.rankChange > 0
                          ? Icons.arrow_upward
                          : Icons.arrow_downward,
                      size: 12.w,
                      color: entry.rankChange > 0
                          ? AppTheme.success
                          : AppTheme.error,
                    ),
                    SizedBox(width: 2.w),
                    Text(
                      '${entry.rankChange.abs()}',
                      style: AppTheme.labelSmall.copyWith(
                        color: entry.rankChange > 0
                            ? AppTheme.success
                            : AppTheme.error,
                      ),
                    ),
                  ],
                ),
            ],
          ),
        ],
      ),
    );
  }
}
