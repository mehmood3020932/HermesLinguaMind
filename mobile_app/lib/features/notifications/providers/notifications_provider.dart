import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hermes_linguamind/data/models/notification_model.dart';

class NotificationsState {
  const NotificationsState({
    this.notifications = const [],
    this.isLoading = false,
    this.unreadCount = 0,
  });

  final List<AppNotification> notifications;
  final bool isLoading;
  final int unreadCount;

  NotificationsState copyWith({
    final List<AppNotification>? notifications,
    final bool? isLoading,
    final int? unreadCount,
  }) => NotificationsState(
    notifications: notifications ?? this.notifications,
    isLoading: isLoading ?? this.isLoading,
    unreadCount: unreadCount ?? this.unreadCount,
  );
}

class NotificationsNotifier extends StateNotifier<NotificationsState> {
  NotificationsNotifier() : super(const NotificationsState()) {
    loadNotifications();
  }

  Future<void> loadNotifications() async {
    state = state.copyWith(isLoading: true);
    await Future<void>.delayed(const Duration(milliseconds: 500));

    final notifications = [
      AppNotification(
        id: '1',
        type: NotificationType.streakWarning,
        title: 'Streak in Danger!',
        body: 'Complete a lesson today to keep your 7-day streak alive.',
        timestamp: DateTime.now().subtract(const Duration(hours: 2)),
      ),
      AppNotification(
        id: '2',
        type: NotificationType.achievement,
        title: 'New Achievement!',
        body: 'You earned "Week Warrior" for 7-day streak.',
        timestamp: DateTime.now().subtract(const Duration(hours: 5)),
        isRead: true,
      ),
      AppNotification(
        id: '3',
        type: NotificationType.socialMatch,
        title: 'New Match!',
        body: 'Sarah wants to practice Spanish with you.',
        timestamp: DateTime.now().subtract(const Duration(days: 1)),
      ),
      AppNotification(
        id: '4',
        type: NotificationType.leaderboardChange,
        title: 'Rank Up!',
        body: 'You moved up to #42 on the weekly leaderboard.',
        timestamp: DateTime.now().subtract(const Duration(days: 2)),
        isRead: true,
      ),
    ];

    final unreadCount = notifications.where((final n) => !n.isRead).length;
    state = state.copyWith(
      notifications: notifications,
      isLoading: false,
      unreadCount: unreadCount,
    );
  }

  void markAsRead(final String id) {
    final updated = state.notifications.map((final n) {
      if (n.id == id) return n.copyWith(isRead: true);
      return n;
    }).toList();
    final unreadCount = updated.where((final n) => !n.isRead).length;
    state = state.copyWith(notifications: updated, unreadCount: unreadCount);
  }

  void markAllAsRead() {
    final updated = state.notifications
        .map((final n) => n.copyWith(isRead: true))
        .toList();
    state = state.copyWith(notifications: updated, unreadCount: 0);
  }

  void clearAll() {
    state = state.copyWith(notifications: [], unreadCount: 0);
  }
}

final notificationsProvider =
    StateNotifierProvider<NotificationsNotifier, NotificationsState>((
      final ref,
    ) {
      return NotificationsNotifier();
    });
