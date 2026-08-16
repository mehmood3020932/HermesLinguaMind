import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/features/settings/providers/settings_provider.dart';

class NotificationsSettingsScreen extends ConsumerWidget {
  const NotificationsSettingsScreen({super.key});

  @override
  Widget build(final BuildContext context, final WidgetRef ref) {
    final settings = ref.watch(settingsProvider);

    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
          onPressed: context.pop,
        ),
        title: Text('Notifications', style: AppTheme.headlineLarge),
      ),
      body: SafeArea(
        child: ListView(
          padding: EdgeInsets.all(16.w),
          children: [
            _buildSwitchTile(
              icon: Icons.notifications_active_outlined,
              label: 'Study Reminders',
              subtitle: 'Daily reminders to practice',
              value: settings.notificationsEnabled,
              onChanged: (final v) =>
                  ref.read(settingsProvider.notifier).toggleNotifications(value: v),
            ),
            _buildSwitchTile(
              icon: Icons.local_fire_department_outlined,
              label: 'Streak Alerts',
              subtitle: 'Warn when streak is about to break',
              value: true,
              onChanged: (_) {},
            ),
            _buildSwitchTile(
              icon: Icons.emoji_events_outlined,
              label: 'Achievement Notifications',
              subtitle: 'When you unlock new achievements',
              value: true,
              onChanged: (_) {},
            ),
            _buildSwitchTile(
              icon: Icons.people_outline,
              label: 'Social Notifications',
              subtitle: 'New matches and messages',
              value: true,
              onChanged: (_) {},
            ),
            _buildSwitchTile(
              icon: Icons.leaderboard_outlined,
              label: 'Leaderboard Updates',
              subtitle: 'When your rank changes',
              value: true,
              onChanged: (_) {},
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSwitchTile({
    required final IconData icon,
    required final String label,
    required final String subtitle,
    required final bool value,
    required final ValueChanged<bool> onChanged,
  }) {
    return SwitchListTile(
      secondary: Container(
        width: 44.w,
        height: 44.h,
        decoration: BoxDecoration(
          color: AppTheme.darkSurface,
          borderRadius: BorderRadius.circular(12.r),
        ),
        child: Icon(icon, color: AppTheme.textSecondary, size: 22.w),
      ),
      title: Text(label, style: AppTheme.bodyLarge),
      subtitle: Text(subtitle, style: AppTheme.bodySmall),
      value: value,
      onChanged: onChanged,
      activeThumbColor: AppTheme.violet,
      contentPadding: EdgeInsets.symmetric(vertical: 8.h, horizontal: 8.w),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.r)),
    );
  }
}
