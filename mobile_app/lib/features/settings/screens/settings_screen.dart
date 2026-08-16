import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/constants/app_routes.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/features/settings/providers/settings_provider.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

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
        title: Text('Settings', style: AppTheme.headlineLarge),
      ),
      body: SafeArea(
        child: ListView(
          padding: EdgeInsets.all(16.w),
          children: [
            _buildSection('Appearance'),
            _buildTile(
              icon: Icons.palette_outlined,
              label: 'Appearance',
              subtitle: 'Theme & colors',
              onTap: () => context.push(AppRoutes.appearance),
            ),
            _buildTile(
              icon: Icons.text_fields_outlined,
              label: 'Text Size',
              subtitle: '${(settings.fontScale * 100).toInt()}%',
              onTap: () => _showFontScaleDialog(context, ref),
            ),
            SizedBox(height: 24.h),
            _buildSection('Preferences'),
            _buildSwitchTile(
              icon: Icons.notifications_outlined,
              label: 'Notifications',
              value: settings.notificationsEnabled,
              onChanged: (final v) =>
                  ref.read(settingsProvider.notifier).toggleNotifications(value: v),
            ),
            _buildSwitchTile(
              icon: Icons.volume_up_outlined,
              label: 'Sound Effects',
              value: settings.soundEnabled,
              onChanged: (final v) =>
                  ref.read(settingsProvider.notifier).toggleSound(value: v),
            ),
            _buildSwitchTile(
              icon: Icons.vibration_outlined,
              label: 'Haptics',
              value: settings.hapticsEnabled,
              onChanged: (final v) =>
                  ref.read(settingsProvider.notifier).toggleHaptics(value: v),
            ),
            _buildSwitchTile(
              icon: Icons.play_circle_outline,
              label: 'Auto-play Audio',
              value: settings.autoPlayAudio,
              onChanged: (final v) =>
                  ref.read(settingsProvider.notifier).toggleAutoPlayAudio(value: v),
            ),
            SizedBox(height: 24.h),
            _buildSection('About'),
            _buildTile(
              icon: Icons.info_outline,
              label: 'Version',
              subtitle: '2.0.0 (Build 8)',
            ),
            _buildTile(
              icon: Icons.privacy_tip_outlined,
              label: 'Privacy Policy',
              onTap: () {},
            ),
            _buildTile(
              icon: Icons.description_outlined,
              label: 'Terms of Service',
              onTap: () {},
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(final String title) {
    return Padding(
      padding: EdgeInsets.only(left: 16.w, bottom: 8.h, top: 8.h),
      child: Text(
        title,
        style: AppTheme.labelMedium.copyWith(color: AppTheme.textTertiary),
      ),
    );
  }

  Widget _buildTile({
    required final IconData icon,
    required final String label,
    final String? subtitle,
    final VoidCallback? onTap,
  }) {
    return ListTile(
      leading: Icon(icon, color: AppTheme.textSecondary, size: 24.w),
      title: Text(label, style: AppTheme.bodyLarge),
      subtitle: subtitle != null
          ? Text(subtitle, style: AppTheme.bodySmall)
          : null,
      trailing: onTap != null
          ? Icon(Icons.chevron_right, color: AppTheme.textTertiary, size: 20.w)
          : null,
      onTap: onTap,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.r)),
    );
  }

  Widget _buildSwitchTile({
    required final IconData icon,
    required final String label,
    required final bool value,
    required final ValueChanged<bool> onChanged,
  }) {
    return SwitchListTile(
      secondary: Icon(icon, color: AppTheme.textSecondary, size: 24.w),
      title: Text(label, style: AppTheme.bodyLarge),
      value: value,
      onChanged: onChanged,
      activeThumbColor: AppTheme.violet,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.r)),
    );
  }

  void _showFontScaleDialog(final BuildContext context, final WidgetRef ref) {
    showDialog<void>(
      context: context,
      builder: (final context) => AlertDialog(
        backgroundColor: AppTheme.darkSurface,
        title: Text('Text Size', style: AppTheme.headlineMedium),
        content: StatefulBuilder(
          builder: (final context, final setState) {
            final currentScale = ref.watch(settingsProvider).fontScale;
            return Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Slider(
                  value: currentScale,
                  min: 0.8,
                  max: 1.4,
                  divisions: 6,
                  label: '${(currentScale * 100).toInt()}%',
                  onChanged: (final v) =>
                      ref.read(settingsProvider.notifier).setFontScale(v),
                ),
                Text(
                  '${(currentScale * 100).toInt()}%',
                  style: AppTheme.bodyLarge,
                ),
              ],
            );
          },
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(
              'Done',
              style: AppTheme.labelMedium.copyWith(color: AppTheme.violet),
            ),
          ),
        ],
      ),
    );
  }
}
