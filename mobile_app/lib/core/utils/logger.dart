import 'package:logger/logger.dart';

/// Centralized application logger.
class AppLogger {
  AppLogger._();

  static late final Logger _logger;

  static void init() {
    _logger = Logger(
      printer: PrettyPrinter(
        dateTimeFormat: DateTimeFormat.onlyTimeAndSinceStart,
      ),
      level: Level.debug,
    );
  }

  static void debug(
    final String message, [
    final dynamic error,
    final StackTrace? stackTrace,
  ]) {
    _logger.d(message, error: error, stackTrace: stackTrace);
  }

  static void info(
    final String message, [
    final dynamic error,
    final StackTrace? stackTrace,
  ]) {
    _logger.i(message, error: error, stackTrace: stackTrace);
  }

  static void warning(
    final String message, [
    final dynamic error,
    final StackTrace? stackTrace,
  ]) {
    _logger.w(message, error: error, stackTrace: stackTrace);
  }

  static void error(
    final String message, [
    final dynamic error,
    final StackTrace? stackTrace,
  ]) {
    _logger.e(message, error: error, stackTrace: stackTrace);
  }

  static void wtf(
    final String message, [
    final dynamic error,
    final StackTrace? stackTrace,
  ]) {
    _logger.f(message, error: error, stackTrace: stackTrace);
  }
}
