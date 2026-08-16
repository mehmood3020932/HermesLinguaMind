import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_slidable/flutter_slidable.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/utils/extensions.dart';
import 'package:hermes_linguamind/data/models/notification_model.dart';
import 'package:hermes_linguamind/features/notifications/providers/notifications_provider.dart';

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(final BuildContext context, final WidgetRef ref) {
    final state = ref.watch(notificationsProvider);

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
        actions: [
          if (state.unreadCount > 0)
            TextButton(
              onPressed: () => ref.read(notificationsProvider.notifier).markAllAsRead(),
              child: Text('Mark All Read', style: AppTheme.labelMedium.copyWith(color: AppTheme.aqua)),
            ),
        ],
      ),
      body: state.notifications.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.notifications_off_outlined, size: 64.w, color: AppTheme.textTertiary),
                  SizedBox(height: 16.h),
                  Text('No Notifications', style: AppTheme.headlineLarge),
                  SizedBox(height: 8.h),
                  Text("You're all caught up!", style: AppTheme.bodyMedium),
                ],
              ),
            )
          : ListView.builder(
              padding: EdgeInsets.all(16.w),
              itemCount: state.notifications.length,
              itemBuilder: (final context, final index) {
                final notification = state.notifications[index];
                return _buildNotificationTile(context, ref, notification);
              },
            ),
    );
  }

  Widget _buildNotificationTile(final BuildContext context, final WidgetRef ref, final AppNotification notification) {
    return Slidable(
      endActionPane: ActionPane(
        motion: const ScrollMotion(),
        children: [
          SlidableAction(
            onPressed: (_) => ref.read(notificationsProvider.notifier).markAsRead(notification.id),
            backgroundColor: AppTheme.success.withValues(alpha: 0.2),
            foregroundColor: AppTheme.success,
            icon: Icons.done_all,
            label: 'Read',
            borderRadius: BorderRadius.horizontal(right: Radius.circular(12.r)),
          ),
        ],
      ),
      child: GestureDetector(
        onTap: () {
          if (!notification.isRead) {
            ref.read(notificationsProvider.notifier).markAsRead(notification.id);
          }
        },
        child: Container(
          margin: EdgeInsets.only(bottom: 8.h),
          padding: EdgeInsets.all(16.w),
          decoration: BoxDecoration(
            color: notification.isRead ? AppTheme.darkSurface : AppTheme.violet.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(12.r),
            border: Border.all(
              color: notification.isRead ? AppTheme.borderSubtle : AppTheme.violet.withValues(alpha: 0.2),
            ),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 44.w,
                height: 44.h,
                decoration: BoxDecoration(
                  color: _getTypeColor(notification.type).withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(12.r),
                ),
                child: Icon(
                  _getTypeIcon(notification.type),
                  color: _getTypeColor(notification.type),
                  size: 22.w,
                ),
              ),
              SizedBox(width: 12.w),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            notification.title,
                            style: AppTheme.bodyLarge.copyWith(
                              fontWeight: notification.isRead ? FontWeight.w400 : FontWeight.w600,
                            ),
                          ),
                        ),
                        if (!notification.isRead)
                          Container(
                            width: 8.w,
                            height: 8.h,
                            decoration: const BoxDecoration(
                              color: AppTheme.violet,
                              shape: BoxShape.circle,
                            ),
                          ),
                      ],
                    ),
                    SizedBox(height: 4.h),
                    Text(notification.body, style: AppTheme.bodyMedium),
                    SizedBox(height: 8.h),
                    Text(notification.timestamp.relativeTime, style: AppTheme.labelSmall),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  IconData _getTypeIcon(final NotificationType type) {
    switch (type) {
      case NotificationType.lessonReminder:
        return Icons.school_outlined;
      case NotificationType.streakWarning:
        return Icons.local_fire_department_outlined;
      case NotificationType.achievement:
        return Icons.emoji_events_outlined;
      case NotificationType.socialMatch:
        return Icons.people_outline;
      case NotificationType.leaderboardChange:
        return Icons.leaderboard_outlined;
      case NotificationType.system:
        return Icons.info_outline;
      case NotificationType.message:
        return Icons.message_outlined;
    }
  }

  Color _getTypeColor(final NotificationType type) {
    switch (type) {
      case NotificationType.lessonReminder:
        return AppTheme.violet;
      case NotificationType.streakWarning:
        return AppTheme.error;
      case NotificationType.achievement:
        return AppTheme.warning;
      case NotificationType.socialMatch:
        return AppTheme.aqua;
      case NotificationType.leaderboardChange:
        return AppTheme.success;
      case NotificationType.system:
        return AppTheme.textSecondary;
      case NotificationType.message:
        return AppTheme.violet;
    }
  }
}
