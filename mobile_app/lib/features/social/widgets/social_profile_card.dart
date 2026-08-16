import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/utils/extensions.dart';
import 'package:hermes_linguamind/data/models/social_models.dart';

class SocialProfileCard extends StatelessWidget {
  const SocialProfileCard({required this.profile, super.key, this.onTap});

  final SocialProfile profile;
  final VoidCallback? onTap;

  @override
  Widget build(final BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: EdgeInsets.symmetric(horizontal: 16.w, vertical: 6.h),
        padding: EdgeInsets.all(16.w),
        decoration: BoxDecoration(
          color: AppTheme.darkSurface,
          borderRadius: BorderRadius.circular(16.r),
          border: Border.all(color: AppTheme.borderSubtle),
        ),
        child: Row(
          children: [
            Stack(
              children: [
                Container(
                  width: 52.w,
                  height: 52.h,
                  decoration: BoxDecoration(
                    gradient: AppTheme.primaryGradient,
                    borderRadius: BorderRadius.circular(16.r),
                  ),
                  child: Center(
                    child: Text(
                      profile.displayName.isNotEmpty
                          ? profile.displayName[0].toUpperCase()
                          : '?',
                      style: AppTheme.headlineLarge.copyWith(
                        color: AppTheme.textInverse,
                      ),
                    ),
                  ),
                ),
                if (profile.isOnline)
                  Positioned(
                    bottom: 0,
                    right: 0,
                    child: Container(
                      width: 14.w,
                      height: 14.h,
                      decoration: BoxDecoration(
                        color: AppTheme.success,
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: AppTheme.darkSurface,
                          width: 2,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            SizedBox(width: 16.w),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        profile.displayName,
                        style: AppTheme.bodyLarge.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      SizedBox(width: 8.w),
                      if (profile.isOnline)
                        Container(
                          padding: EdgeInsets.symmetric(
                            horizontal: 6.w,
                            vertical: 2.h,
                          ),
                          decoration: BoxDecoration(
                            color: AppTheme.success.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(4.r),
                          ),
                          child: Text(
                            'Online',
                            style: AppTheme.labelSmall.copyWith(
                              color: AppTheme.success,
                              fontSize: 9.sp,
                            ),
                          ),
                        )
                      else if (profile.lastActive != null)
                        Text(
                          profile.lastActive!.relativeTime,
                          style: AppTheme.labelSmall,
                        ),
                    ],
                  ),
                  SizedBox(height: 4.h),
                  Wrap(
                    spacing: 4.w,
                    children: profile.languages.map((final lang) {
                      return Container(
                        padding: EdgeInsets.symmetric(
                          horizontal: 6.w,
                          vertical: 2.h,
                        ),
                        decoration: BoxDecoration(
                          color: AppTheme.darkElevated,
                          borderRadius: BorderRadius.circular(4.r),
                        ),
                        child: Text(
                          lang.toUpperCase(),
                          style: AppTheme.labelSmall.copyWith(fontSize: 9.sp),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.star_rounded,
                      size: 14.w,
                      color: AppTheme.warning,
                    ),
                    SizedBox(width: 4.w),
                    Text(
                      profile.xp.compact,
                      style: AppTheme.labelMedium.copyWith(
                        color: AppTheme.warning,
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 4.h),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.local_fire_department_rounded,
                      size: 12.w,
                      color: AppTheme.warning,
                    ),
                    SizedBox(width: 2.w),
                    Text('${profile.streakDays}', style: AppTheme.labelSmall),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
