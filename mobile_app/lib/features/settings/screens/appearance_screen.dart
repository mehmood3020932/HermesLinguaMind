import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/constants/app_routes.dart';
import 'package:hermes_linguamind/core/theme/app_colors.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/widgets/widgets.dart';
import 'package:hermes_linguamind/features/profile/providers/profile_provider.dart';

class AppearanceScreen extends ConsumerWidget {
  const AppearanceScreen({super.key});

  @override
  Widget build(final BuildContext context, final WidgetRef ref) {
    final profileState = ref.watch(profileProvider);
    final currentSkin = profileState.user?.characterSkinIndex ?? 0;

    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
          onPressed: context.pop,
        ),
        title: Text('Character Skin', style: AppTheme.headlineLarge),
      ),
      body: SafeArea(
        child: Padding(
          padding: EdgeInsets.all(24.w),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("Choose your companion's color theme", style: AppTheme.bodyMedium),
              SizedBox(height: 24.h),
              Expanded(
                child: GridView.builder(
                  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    crossAxisSpacing: 16.w,
                    mainAxisSpacing: 16.h,
                    childAspectRatio: 1.2,
                  ),
                  itemCount: AppColors.characterSkins.length,
                  itemBuilder: (final context, final index) {
                    final color = AppColors.characterSkins[index];
                    final isSelected = index == currentSkin;

                    return GestureDetector(
                      onTap: () {
                        ref.read(profileProvider.notifier).updateProfile(characterSkinIndex: index);
                      },
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        decoration: BoxDecoration(
                          color: color.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(20.r),
                          border: Border.all(
                            color: isSelected ? color : Colors.transparent,
                            width: 3,
                          ),
                          boxShadow: isSelected
                              ? [
                                  BoxShadow(
                                    color: color.withValues(alpha: 0.3),
                                    blurRadius: 15,
                                    spreadRadius: 2,
                                  ),
                                ]
                              : null,
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Container(
                              width: 60.w,
                              height: 60.h,
                              decoration: BoxDecoration(
                                gradient: LinearGradient(
                                  colors: [color, color.withValues(alpha: 0.7)],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                borderRadius: BorderRadius.circular(20.r),
                              ),
                              child: Icon(Icons.smart_toy, size: 30.w, color: AppTheme.textInverse),
                            ),
                            SizedBox(height: 12.h),
                            if (isSelected)
                              Container(
                                padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 4.h),
                                decoration: BoxDecoration(
                                  color: color.withValues(alpha: 0.2),
                                  borderRadius: BorderRadius.circular(12.r),
                                ),
                                child: Text(
                                  'Selected',
                                  style: AppTheme.labelSmall.copyWith(color: color),
                                ),
                              ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
              SizedBox(height: 16.h),
              SecondaryButton(
                label: 'Preview new UI widgets',
                icon: const Icon(Icons.auto_awesome, size: 18),
                onPressed: () => context.push(AppRoutes.uiShowcase),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
