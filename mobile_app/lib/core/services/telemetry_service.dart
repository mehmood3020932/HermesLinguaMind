import 'package:hermes_linguamind/core/utils/logger.dart';

/// Lightweight local telemetry — logs events/errors through [AppLogger].
///
/// No cloud analytics service is wired up by default (that would require
/// your own Firebase/Sentry/PostHog project + config files, which this
/// project doesn't assume you have). Swap the method bodies below for real
/// SDK calls if/when you add one — the call sites elsewhere in the app
/// don't need to change.
class TelemetryService {
  factory TelemetryService() => _instance;
  TelemetryService._();
  static final TelemetryService _instance = TelemetryService._();

  bool _initialized = false;

  Future<void> initialize() async {
    _initialized = true;
    AppLogger.info('TelemetryService initialized (local logging only)');
  }

  Future<void> logEvent({
    required final String name,
    final Map<String, dynamic>? parameters,
  }) async {
    if (!_initialized) return;
    AppLogger.debug('event: $name ${parameters ?? {}}');
  }

  Future<void> logScreenView({
    required final String screenName,
    final String? screenClass,
  }) async {
    if (!_initialized) return;
    AppLogger.debug('screen_view: $screenName');
  }

  Future<void> logError({
    required final String error,
    required final StackTrace stackTrace,
    final Map<String, dynamic>? context,
  }) async {
    if (!_initialized) return;
    AppLogger.error(
      'telemetry error: $error ${context ?? {}}',
      error,
      stackTrace,
    );
  }

  Future<void> setUserId(final String userId) async {
    if (!_initialized) return;
    AppLogger.debug('telemetry user set: $userId');
  }
}
