import 'dart:async';

import 'package:dio/dio.dart';
import 'package:dio_cache_interceptor/dio_cache_interceptor.dart';
import 'package:dio_cache_interceptor_hive_store/dio_cache_interceptor_hive_store.dart';
import 'package:flutter/foundation.dart';
import 'package:hermes_linguamind/core/constants/api_endpoints.dart';
import 'package:hermes_linguamind/core/constants/app_constants.dart';
import 'package:hermes_linguamind/core/utils/logger.dart';
import 'package:hermes_linguamind/data/services/secure_storage_service.dart';

class ApiClient {
  factory ApiClient() => _instance;
  ApiClient._() {
    _initDio();
  }
  static final ApiClient _instance = ApiClient._();

  late final Dio _dio;
  final SecureStorageService _storage = SecureStorageService();

  Dio get dio => _dio;

  void _initDio() {
    final cacheStore = HiveCacheStore(null);
    final cacheOptions = CacheOptions(
      store: cacheStore,
      hitCacheOnErrorExcept: [401, 403],
      maxStale: const Duration(hours: 24),
    );

    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: AppConstants.apiConnectTimeout,
        receiveTimeout: AppConstants.apiTimeout,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(DioCacheInterceptor(options: cacheOptions));

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (final options, final handler) async {
          final token = await _storage.read(key: AppConstants.accessTokenKey);
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          AppLogger.debug('→ ${options.method} ${options.path}');
          handler.next(options);
        },
        onResponse: (final response, final handler) {
          AppLogger.debug(
            '← ${response.statusCode} ${response.requestOptions.path}',
          );
          handler.next(response);
        },
        onError: (final error, final handler) async {
          AppLogger.error(
            '✕ ${error.response?.statusCode} ${error.requestOptions.path}',
            error,
          );
          if (error.response?.statusCode == 401) {
            final refreshed = await _refreshToken();
            if (refreshed) {
              final opts = error.requestOptions;
              final token = await _storage.read(
                key: AppConstants.accessTokenKey,
              );
              opts.headers['Authorization'] = 'Bearer $token';
              final response = await _dio.fetch<dynamic>(opts);
              handler.resolve(response);
              return;
            }
          }
          handler.next(error);
        },
      ),
    );

    if (kDebugMode) {
      _dio.interceptors.add(
        LogInterceptor(
          requestBody: true,
          responseBody: true,
          logPrint: (final o) => AppLogger.debug(o.toString()),
        ),
      );
    }
  }

  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await _storage.read(
        key: AppConstants.refreshTokenKey,
      );
      if (refreshToken == null) return false;

      final response = await _dio.post<Map<String, dynamic>>(
        ApiEndpoints.refresh,
        data: {'refresh_token': refreshToken},
      );

      // Every backend response is wrapped in a HermesResponse envelope:
      // {"success": bool, "data": {...}, "error": ..., "error_code": ...}.
      // The actual tokens are nested under `data`, not at the top level —
      // reading response.data['access_token'] directly was always null,
      // so this cast to String would throw on every single refresh.
      final envelope = response.data ?? <String, dynamic>{};
      final success = envelope['success'] as bool? ?? false;
      final data = envelope['data'] as Map<String, dynamic>?;

      if (response.statusCode == 200 && success && data != null) {
        await _storage.write(
          key: AppConstants.accessTokenKey,
          value: data['access_token'] as String,
        );
        // The backend rotates the refresh token on every use and returns
        // the new one — must be saved too, or the *next* refresh attempt
        // fails with an already-consumed token.
        await _storage.write(
          key: AppConstants.refreshTokenKey,
          value: data['refresh_token'] as String,
        );
        return true;
      }
      return false;
    } on Exception catch (e, stack) {
      AppLogger.error('Token refresh failed', e, stack);
      return false;
    }
  }

  Future<Response<T>> get<T>(
    final String path, {
    final Map<String, dynamic>? queryParameters,
    final Options? options,
  }) async {
    return _dio.get<T>(
      path,
      queryParameters: queryParameters,
      options: options,
    );
  }

  Future<Response<T>> post<T>(
    final String path, {
    final dynamic data,
    final Options? options,
  }) async {
    return _dio.post<T>(path, data: data, options: options);
  }

  Future<Response<T>> put<T>(
    final String path, {
    final dynamic data,
    final Options? options,
  }) async {
    return _dio.put<T>(path, data: data, options: options);
  }

  Future<Response<T>> delete<T>(
    final String path, {
    final dynamic data,
    final Options? options,
  }) async {
    return _dio.delete<T>(path, data: data, options: options);
  }
}
