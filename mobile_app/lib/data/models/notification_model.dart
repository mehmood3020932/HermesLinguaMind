import 'package:equatable/equatable.dart';

enum NotificationType {
  lessonReminder,
  streakWarning,
  achievement,
  socialMatch,
  leaderboardChange,
  system,
  message,
}

class AppNotification extends Equatable {
  const AppNotification({
    required this.id,
    required this.type,
    required this.title,
    required this.body,
    required this.timestamp,
    this.isRead = false,
    this.actionUrl,
    this.metadata,
  });

  factory AppNotification.fromJson(final Map<String, dynamic> json) =>
      AppNotification(
        id: json['id'] as String? ?? '',
        type: NotificationType.values.byName(
          json['type'] as String? ?? 'system',
        ),
        title: json['title'] as String? ?? '',
        body: json['body'] as String? ?? '',
        timestamp: DateTime.parse(json['timestamp'] as String),
        isRead: json['is_read'] as bool? ?? false,
        actionUrl: json['action_url'] as String?,
        metadata: json['metadata'] as Map<String, dynamic>?,
      );

  final String id;
  final NotificationType type;
  final String title;
  final String body;
  final DateTime timestamp;
  final bool isRead;
  final String? actionUrl;
  final Map<String, dynamic>? metadata;

  Map<String, dynamic> toJson() => {
    'id': id,
    'type': type.name,
    'title': title,
    'body': body,
    'timestamp': timestamp.toIso8601String(),
    'is_read': isRead,
    'action_url': actionUrl,
    'metadata': metadata,
  };

  AppNotification copyWith({final bool? isRead}) => AppNotification(
    id: id,
    type: type,
    title: title,
    body: body,
    timestamp: timestamp,
    isRead: isRead ?? this.isRead,
    actionUrl: actionUrl,
    metadata: metadata,
  );

  @override
  List<Object?> get props => [id, type, timestamp];
}
