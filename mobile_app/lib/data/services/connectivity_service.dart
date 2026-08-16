import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:hermes_linguamind/core/utils/logger.dart';

class ConnectivityService {
  factory ConnectivityService() => _instance;
  ConnectivityService._();
  static final ConnectivityService _instance = ConnectivityService._();

  final Connectivity _connectivity = Connectivity();
  final StreamController<bool> _controller = StreamController<bool>.broadcast();
  bool _isConnected = true;

  Stream<bool> get connectionStream => _controller.stream;
  bool get isConnected => _isConnected;

  void startMonitoring() {
    _connectivity.onConnectivityChanged.listen((final results) {
      final hasConnection =
          results.isNotEmpty &&
          results.any((final r) => r != ConnectivityResult.none);
      if (_isConnected != hasConnection) {
        _isConnected = hasConnection;
        _controller.add(_isConnected);
        AppLogger.info('Connectivity changed: $_isConnected');
      }
    });
  }

  Future<bool> checkConnection() async {
    final results = await _connectivity.checkConnectivity();
    return _isConnected =
        results.isNotEmpty &&
        results.any((final r) => r != ConnectivityResult.none);
  }

  void dispose() {
    _controller.close();
  }
}
