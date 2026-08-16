import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:hermes_linguamind/core/utils/logger.dart';
import 'package:timezone/data/latest.dart' as tz_data;
import 'package:timezone/timezone.dart' as tz;

class NotificationService {
  factory NotificationService() => _instance;
  NotificationService._();
  static final NotificationService _instance = NotificationService._();

  final FlutterLocalNotificationsPlugin _notifications =
      FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  Future<void> initialize() async {
    if (_initialized) return;
    tz_data.initializeTimeZones();
    const androidSettings = AndroidInitializationSettings(
      '@mipmap/ic_launcher',
    );
    const iosSettings = DarwinInitializationSettings();
    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );
    await _notifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onTap,
    );
    _initialized = true;
    AppLogger.info('NotificationService initialized');
  }

  void _onTap(final NotificationResponse response) {
    AppLogger.info('Notification tapped: ${response.payload}');
  }

  Future<void> showNotification({
    required final int id,
    required final String title,
    required final String body,
    final String? payload,
  }) async {
    if (!_initialized) await initialize();
    const androidDetails = AndroidNotificationDetails(
      'hermes_main_channel',
      'Hermes LinguaMind',
      channelDescription: 'Main notification channel for Hermes LinguaMind',
      importance: Importance.high,
      priority: Priority.high,
    );
    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );
    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );
    await _notifications.show(id, title, body, details, payload: payload);
  }

  Future<void> scheduleNotification({
    required final int id,
    required final String title,
    required final String body,
    required final DateTime scheduledDate,
    final String? payload,
  }) async {
    if (!_initialized) await initialize();
    const androidDetails = AndroidNotificationDetails(
      'hermes_reminder_channel',
      'Study Reminders',
      channelDescription: 'Daily study reminders',
      importance: Importance.high,
      priority: Priority.high,
    );
    const iosDetails = DarwinNotificationDetails();
    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );
    await _notifications.zonedSchedule(
      id,
      title,
      body,
      tz.TZDateTime.from(scheduledDate, tz.local),
      details,
      androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      payload: payload,
    );
  }

  Future<void> cancelNotification(final int id) async {
    await _notifications.cancel(id);
  }

  Future<void> cancelAll() async {
    await _notifications.cancelAll();
  }
}
