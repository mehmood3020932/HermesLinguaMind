import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/features/companion/screens/companion_screen.dart';
import 'package:hermes_linguamind/features/home/providers/home_provider.dart';
import 'package:hermes_linguamind/features/home/widgets/home_app_bar.dart';
import 'package:hermes_linguamind/features/leaderboard/screens/leaderboard_screen.dart';
import 'package:hermes_linguamind/features/learning/screens/curriculum_screen.dart';
import 'package:hermes_linguamind/features/profile/screens/profile_screen.dart';
import 'package:hermes_linguamind/features/social/screens/social_screen.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  static const List<Widget> _screens = [
    CurriculumScreen(),
    CompanionScreen(),
    LeaderboardScreen(),
    SocialScreen(),
    ProfileScreen(),
  ];

  static const List<_NavItem> _navItems = [
    _NavItem(
      icon: Icons.school_outlined,
      activeIcon: Icons.school,
      label: 'Learn',
    ),
    _NavItem(
      icon: Icons.smart_toy_outlined,
      activeIcon: Icons.smart_toy,
      label: 'Companion',
    ),
    _NavItem(
      icon: Icons.emoji_events_outlined,
      activeIcon: Icons.emoji_events,
      label: 'Rank',
    ),
    _NavItem(
      icon: Icons.people_outline,
      activeIcon: Icons.people,
      label: 'Social',
    ),
    _NavItem(
      icon: Icons.person_outline,
      activeIcon: Icons.person,
      label: 'Profile',
    ),
  ];

  @override
  Widget build(final BuildContext context, final WidgetRef ref) {
    final homeState = ref.watch(homeProvider);

    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      appBar: const HomeAppBar(),
      body: IndexedStack(index: homeState.selectedIndex, children: _screens),
      bottomNavigationBar: DecoratedBox(
        decoration: BoxDecoration(
          color: AppTheme.darkElevated,
          border: const Border(top: BorderSide(color: AppTheme.borderSubtle)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.2),
              blurRadius: 10,
              offset: const Offset(0, -4),
            ),
          ],
        ),
        child: SafeArea(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 8.h),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: List.generate(_navItems.length, (final index) {
                final item = _navItems[index];
                final isSelected = homeState.selectedIndex == index;
                return _NavBarItem(
                  item: item,
                  isSelected: isSelected,
                  onTap: () => ref.read(homeProvider.notifier).setIndex(index),
                );
              }),
            ),
          ),
        ),
      ),
    );
  }
}

class _NavItem {
  const _NavItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
  });
  final IconData icon;
  final IconData activeIcon;
  final String label;
}

class _NavBarItem extends StatelessWidget {
  const _NavBarItem({
    required this.item,
    required this.isSelected,
    required this.onTap,
  });
  final _NavItem item;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(final BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
        decoration: BoxDecoration(
          color: isSelected
              ? AppTheme.violet.withValues(alpha: 0.15)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(12.r),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isSelected ? item.activeIcon : item.icon,
              color: isSelected ? AppTheme.violet : AppTheme.textTertiary,
              size: 24.w,
            ),
            SizedBox(height: 4.h),
            Text(
              item.label,
              style: AppTheme.labelSmall.copyWith(
                color: isSelected ? AppTheme.violet : AppTheme.textTertiary,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
