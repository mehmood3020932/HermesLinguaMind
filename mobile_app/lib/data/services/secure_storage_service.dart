import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:hermes_linguamind/core/utils/logger.dart';

class SecureStorageService {
  factory SecureStorageService() => _instance;
  SecureStorageService._();
  static final SecureStorageService _instance = SecureStorageService._();

  final FlutterSecureStorage _storage = const FlutterSecureStorage(
    aOptions: AndroidOptions.defaultOptions,
    iOptions: IOSOptions(accountName: 'hermes_linguamind'),
  );

  Future<void> write({
    required final String key,
    required final String value,
  }) async {
    try {
      await _storage.write(key: key, value: value);
    } on Exception catch (e, stack) {
      AppLogger.error('SecureStorage write failed: $key', e, stack);
      rethrow;
    }
  }

  Future<String?> read({required final String key}) async {
    try {
      return await _storage.read(key: key);
    } on Exception catch (e, stack) {
      AppLogger.error('SecureStorage read failed: $key', e, stack);
      return null;
    }
  }

  Future<void> delete({required final String key}) async {
    try {
      await _storage.delete(key: key);
    } on Exception catch (e, stack) {
      AppLogger.error('SecureStorage delete failed: $key', e, stack);
    }
  }

  Future<void> deleteAll() async {
    try {
      await _storage.deleteAll();
    } on Exception catch (e, stack) {
      AppLogger.error('SecureStorage deleteAll failed', e, stack);
    }
  }
}
