import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/constants/app_routes.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/widgets/glass_card.dart';
import 'package:hermes_linguamind/core/widgets/loading_shimmer.dart';
import 'package:hermes_linguamind/features/learning/providers/learning_provider.dart';
import 'package:hermes_linguamind/features/learning/widgets/skill_tree_node.dart';

class CurriculumScreen extends ConsumerWidget {
  const CurriculumScreen({super.key});

  @override
  Widget build(final BuildContext context, final WidgetRef ref) {
    final learningState = ref.watch(learningProvider);

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
                  _buildProgressHeader(learningState),
                  SizedBox(height: 24.h),
                  Text('Your Path', style: AppTheme.headlineLarge),
                  SizedBox(height: 16.h),
                ],
              ),
            ),
          ),
          if (learningState.isLoading)
            const SliverToBoxAdapter(child: ListShimmer(itemCount: 3))
          else
            SliverList(
              delegate: SliverChildBuilderDelegate((
                final context,
                final index,
              ) {
                final unit = learningState.units[index];
                return _buildUnitCard(context, ref, unit, index);
              }, childCount: learningState.units.length),
            ),
          SliverPadding(padding: EdgeInsets.only(bottom: 32.h)),
        ],
      ),
    );
  }

  Widget _buildProgressHeader(final LearningState state) {
    return GlassCard(
      padding: EdgeInsets.all(20.w),
      child: Row(
        children: [
          _buildStatItem(
            icon: Icons.local_fire_department_rounded,
            value: '${state.streakDays}',
            label: 'Day Streak',
            color: AppTheme.warning,
          ),
          Container(width: 1, height: 40.h, color: AppTheme.divider),
          _buildStatItem(
            icon: Icons.star_rounded,
            value: '${state.totalXp}',
            label: 'Total XP',
            color: AppTheme.violet,
          ),
          Container(width: 1, height: 40.h, color: AppTheme.divider),
          _buildStatItem(
            icon: Icons.monetization_on_rounded,
            value: '120',
            label: 'Coins',
            color: AppTheme.aqua,
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem({
    required final IconData icon,
    required final String value,
    required final String label,
    required final Color color,
  }) {
    return Expanded(
      child: Column(
        children: [
          Icon(icon, color: color, size: 24.w),
          SizedBox(height: 8.h),
          Text(value, style: AppTheme.headlineMedium.copyWith(color: color)),
          SizedBox(height: 4.h),
          Text(label, style: AppTheme.labelSmall),
        ],
      ),
    );
  }

  Widget _buildUnitCard(
    final BuildContext context,
    final WidgetRef ref,
    final CurriculumUnit unit,
    final int index,
  ) {
    final isUnlocked = unit.isUnlocked;
    final progress = unit.completionRate;

    return Padding(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
          child: GlassCard(
            padding: EdgeInsets.all(20.w),
            borderColor: isUnlocked ? null : AppTheme.borderSubtle,
            backgroundColor: isUnlocked ? null : AppTheme.darkBase,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 48.w,
                      height: 48.h,
                      decoration: BoxDecoration(
                        gradient: isUnlocked ? AppTheme.primaryGradient : null,
                        color: isUnlocked ? null : AppTheme.darkSurface,
                        borderRadius: BorderRadius.circular(12.r),
                      ),
                      child: Icon(
                        isUnlocked
                            ? Icons.lock_open_rounded
                            : Icons.lock_outline,
                        color: isUnlocked
                            ? AppTheme.textInverse
                            : AppTheme.textTertiary,
                        size: 24.w,
                      ),
                    ),
                    SizedBox(width: 16.w),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            unit.title,
                            style: AppTheme.headlineMedium.copyWith(
                              color: isUnlocked
                                  ? AppTheme.textPrimary
                                  : AppTheme.textTertiary,
                            ),
                          ),
                          SizedBox(height: 4.h),
                          Text(
                            unit.description,
                            style: AppTheme.bodySmall,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                    if (isUnlocked)
                      Container(
                        padding: EdgeInsets.symmetric(
                          horizontal: 12.w,
                          vertical: 6.h,
                        ),
                        decoration: BoxDecoration(
                          color: AppTheme.violet.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(20.r),
                        ),
                        child: Text(
                          '${unit.completedLessons}/${unit.totalLessons}',
                          style: AppTheme.labelSmall.copyWith(
                            color: AppTheme.violet,
                          ),
                        ),
                      ),
                  ],
                ),
                if (isUnlocked) ...[
                  SizedBox(height: 16.h),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4.r),
                    child: LinearProgressIndicator(
                      value: progress,
                      backgroundColor: AppTheme.darkElevated,
                      valueColor: const AlwaysStoppedAnimation<Color>(
                        AppTheme.violet,
                      ),
                      minHeight: 6.h,
                    ),
                  ),
                  SizedBox(height: 16.h),
                  Wrap(
                    spacing: 12.w,
                    runSpacing: 12.h,
                    children: unit.lessons.map((final lesson) {
                      return SkillTreeNode(
                        lesson: lesson,
                        onTap: isUnlocked && !lesson.isLocked
                            ? () => context.push(
                                '${AppRoutes.lessonPlayer}?lessonId=${lesson.id}',
                              )
                            : null,
                      );
                    }).toList(),
                  ),
                ] else ...[
                  SizedBox(height: 12.h),
                  Row(
                    children: [
                      Icon(
                        Icons.lock_outline,
                        size: 14.w,
                        color: AppTheme.textTertiary,
                      ),
                      SizedBox(width: 6.w),
                      Text(
                        'Requires ${unit.requiredXp} XP',
                        style: AppTheme.bodySmall.copyWith(
                          color: AppTheme.textTertiary,
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        )
        .animate(delay: Duration(milliseconds: index * 100))
        .fadeIn()
        .slideY(begin: 0.2, end: 0);
  }
}
