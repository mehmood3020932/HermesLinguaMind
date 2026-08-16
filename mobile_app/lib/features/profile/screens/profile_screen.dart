import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/constants/app_routes.dart';
import 'package:hermes_linguamind/core/theme/app_colors.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/widgets/glass_card.dart';
import 'package:hermes_linguamind/data/models/user_model.dart';
import 'package:hermes_linguamind/features/auth/providers/auth_provider.dart';
import 'package:hermes_linguamind/features/profile/providers/profile_provider.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(final BuildContext context, final WidgetRef ref) {
    final profileState = ref.watch(profileProvider);
    final user = profileState.user;

    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      body: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(
            child: Padding(
              padding: EdgeInsets.all(16.w),
              child: Column(
                children: [
                  _buildProfileHeader(user),
                  SizedBox(height: 24.h),
                  _buildStatsRow(user),
                  SizedBox(height: 24.h),
                  _buildMenuItems(context, ref),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProfileHeader(final UserModel? user) {
    return Column(
      children: [
        Container(
          width: 100.w,
          height: 100.h,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                AppColors.characterSkins[user?.characterSkinIndex ?? 0],
                AppColors.characterSkins[(user?.characterSkinIndex ?? 0 + 1) %
                    AppColors.characterSkins.length],
              ],
            ),
            borderRadius: BorderRadius.circular(30.r),
            boxShadow: [
              BoxShadow(
                color: AppColors.characterSkins[user?.characterSkinIndex ?? 0]
                    .withValues(alpha: 0.4),
                blurRadius: 20,
                spreadRadius: 5,
              ),
            ],
          ),
          child: Center(
            child: Text(
              (user?.displayName.isNotEmpty ?? false)
                  ? user!.displayName[0].toUpperCase()
                  : '?',
              style: AppTheme.displayLarge.copyWith(
                color: AppTheme.textInverse,
              ),
            ),
          ),
        ),
        SizedBox(height: 16.h),
        Text(user?.displayName ?? 'Guest', style: AppTheme.headlineLarge),
        SizedBox(height: 4.h),
        Text('@${user?.username ?? 'guest'}', style: AppTheme.bodyMedium),
        if (user?.bio != null && user!.bio!.isNotEmpty) ...[
          SizedBox(height: 8.h),
          Text(
            user.bio!,
            style: AppTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
        ],
      ],
    ).animate().fadeIn().slideY(begin: 0.2, end: 0);
  }

  Widget _buildStatsRow(final UserModel? user) {
    return GlassCard(
      padding: EdgeInsets.all(20.w),
      child: Row(
        children: [
          _buildStat(
            'XP',
            '${user?.xp ?? 0}',
            Icons.star_rounded,
            AppTheme.warning,
          ),
          Container(width: 1, height: 40.h, color: AppTheme.divider),
          _buildStat(
            'Coins',
            '${user?.coins ?? 0}',
            Icons.monetization_on_rounded,
            AppTheme.aqua,
          ),
          Container(width: 1, height: 40.h, color: AppTheme.divider),
          _buildStat(
            'Streak',
            '${user?.streakDays ?? 0}d',
            Icons.local_fire_department_rounded,
            AppTheme.error,
          ),
        ],
      ),
    );
  }

  Widget _buildStat(
    final String label,
    final String value,
    final IconData icon,
    final Color color,
  ) {
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

  Widget _buildMenuItems(final BuildContext context, final WidgetRef ref) {
    final items = [
      const _MenuItem(
        icon: Icons.edit_outlined,
        label: 'Edit Profile',
        route: AppRoutes.editProfile,
      ),
      const _MenuItem(
        icon: Icons.palette_outlined,
        label: 'Character Skin',
        route: AppRoutes.appearance,
      ),
      const _MenuItem(
        icon: Icons.settings_outlined,
        label: 'Settings',
        route: AppRoutes.settings,
      ),
      const _MenuItem(icon: Icons.help_outline, label: 'Help & Support'),
      const _MenuItem(
        icon: Icons.logout_outlined,
        label: 'Sign Out',
        isDestructive: true,
      ),
    ];

    return Column(
      children: items.map((final item) {
        return _buildMenuTile(context, ref, item);
      }).toList(),
    );
  }

  Widget _buildMenuTile(
    final BuildContext context,
    final WidgetRef ref,
    final _MenuItem item,
  ) {
    return GestureDetector(
      onTap: () {
        if (item.label == 'Sign Out') {
          ref.read(authStateProvider.notifier).logout();
        } else if (item.route != null) {
          context.push(item.route!);
        }
      },
      child: Container(
        margin: EdgeInsets.only(bottom: 8.h),
        padding: EdgeInsets.all(16.w),
        decoration: BoxDecoration(
          color: AppTheme.darkSurface,
          borderRadius: BorderRadius.circular(12.r),
          border: Border.all(color: AppTheme.borderSubtle),
        ),
        child: Row(
          children: [
            Icon(
              item.icon,
              color: item.isDestructive
                  ? AppTheme.error
                  : AppTheme.textSecondary,
              size: 24.w,
            ),
            SizedBox(width: 16.w),
            Expanded(
              child: Text(
                item.label,
                style: AppTheme.bodyLarge.copyWith(
                  color: item.isDestructive
                      ? AppTheme.error
                      : AppTheme.textPrimary,
                ),
              ),
            ),
            if (!item.isDestructive)
              Icon(
                Icons.chevron_right,
                color: AppTheme.textTertiary,
                size: 20.w,
              ),
          ],
        ),
      ),
    );
  }
}

class _MenuItem {
  const _MenuItem({
    required this.icon,
    required this.label,
    this.route,
    this.isDestructive = false,
  });
  final IconData icon;
  final String label;
  final String? route;
  final bool isDestructive;
}
