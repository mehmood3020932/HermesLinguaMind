import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hermes_linguamind/app.dart';
import 'package:hermes_linguamind/core/services/telemetry_service.dart';
import 'package:hermes_linguamind/core/utils/logger.dart';
import 'package:hermes_linguamind/data/services/connectivity_service.dart';
import 'package:hive_flutter/hive_flutter.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Required before any HiveCacheStore (used by the API client's HTTP
  // cache interceptor) touches disk.
  await Hive.initFlutter();

  // Route uncaught errors through the local logger + telemetry service
  // instead of a cloud crash reporter (none is configured by default).
  FlutterError.onError = (final details) {
    FlutterError.presentError(details);
    TelemetryService().logError(
      error: details.exceptionAsString(),
      stackTrace: details.stack ?? StackTrace.current,
    );
  };
  PlatformDispatcher.instance.onError = (final error, final stack) {
    TelemetryService().logError(error: error.toString(), stackTrace: stack);
    return true;
  };

  // Set preferred orientations
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Set system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: Color(0xFF0B0E1A),
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );

  // Initialize logger
  AppLogger.init();

  // Initialize connectivity monitoring
  ConnectivityService().startMonitoring();

  // Initialize telemetry
  await TelemetryService().initialize();

  runApp(const ProviderScope(child: HermesApp()));
}
