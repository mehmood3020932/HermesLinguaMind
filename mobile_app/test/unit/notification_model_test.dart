import 'package:flutter_test/flutter_test.dart';
import 'package:hermes_linguamind/data/models/notification_model.dart';

void main() {
  group('AppNotification', () {
    test('fromJson parses correctly', () {
      final json = {
        'id': '1',
        'type': 'achievement',
        'title': 'Test',
        'body': 'Body',
        'timestamp': '2024-01-01T00:00:00Z',
        'is_read': false,
      };
      final notification = AppNotification.fromJson(json);
      expect(notification.id, '1');
      expect(notification.type, NotificationType.achievement);
      expect(notification.isRead, false);
    });

    test('copyWith works', () {
      final notification = AppNotification(
        id: '1',
        type: NotificationType.system,
        title: 'Test',
        body: 'Body',
        timestamp: DateTime(2024),
      );
      final updated = notification.copyWith(isRead: true);
      expect(updated.isRead, true);
      expect(updated.id, '1');
    });
  });
}
