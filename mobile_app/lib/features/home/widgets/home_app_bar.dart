import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/constants/app_routes.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/features/auth/providers/auth_provider.dart';

class HomeAppBar extends ConsumerWidget implements PreferredSizeWidget {
  const HomeAppBar({super.key});

  @override
  Size get preferredSize => Size.fromHeight(60.h);

  @override
  Widget build(final BuildContext context, final WidgetRef ref) {
    final authState = ref.watch(authStateProvider);
    final user = authState.valueOrNull?.user;

    return AppBar(
      backgroundColor: AppTheme.darkBase.withValues(alpha: 0.9),
      elevation: 0,
      automaticallyImplyLeading: false,
      title: Row(
        children: [
          Container(
            width: 36.w,
            height: 36.h,
            decoration: BoxDecoration(
              gradient: AppTheme.primaryGradient,
              borderRadius: BorderRadius.circular(10.r),
            ),
            child: Icon(
              Icons.language_rounded,
              size: 20.w,
              color: AppTheme.textInverse,
            ),
          ),
          SizedBox(width: 12.w),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Hermes',
                style: AppTheme.labelLarge.copyWith(fontSize: 16.sp),
              ),
              Text(
                user?.displayName ?? 'Learner',
                style: AppTheme.labelSmall.copyWith(
                  color: AppTheme.textTertiary,
                ),
              ),
            ],
          ),
        ],
      ),
      actions: [
        _ActionButton(
          icon: Icons.notifications_outlined,
          badge: true,
          onTap: () => context.push(AppRoutes.notifications),
        ),
        SizedBox(width: 8.w),
        _ActionButton(
          icon: Icons.settings_outlined,
          onTap: () => context.push(AppRoutes.settings),
        ),
        SizedBox(width: 16.w),
      ],
    );
  }
}

class _ActionButton extends StatelessWidget {
  const _ActionButton({
    required this.icon,
    required this.onTap,
    this.badge = false,
  });
  final IconData icon;
  final bool badge;
  final VoidCallback onTap;

  @override
  Widget build(final BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 40.w,
        height: 40.h,
        decoration: BoxDecoration(
          color: AppTheme.darkSurface,
          borderRadius: BorderRadius.circular(12.r),
          border: Border.all(color: AppTheme.borderSubtle),
        ),
        child: Stack(
          alignment: Alignment.center,
          children: [
            Icon(icon, size: 20.w, color: AppTheme.textSecondary),
            if (badge)
              Positioned(
                top: 8.h,
                right: 8.w,
                child: Container(
                  width: 8.w,
                  height: 8.h,
                  decoration: const BoxDecoration(
                    color: AppTheme.error,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
