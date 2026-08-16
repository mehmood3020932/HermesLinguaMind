import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:hermes_linguamind/core/constants/api_endpoints.dart';
import 'package:hermes_linguamind/core/constants/app_constants.dart';
import 'package:hermes_linguamind/core/utils/logger.dart';
import 'package:hermes_linguamind/data/adapters/api_client.dart';
import 'package:hermes_linguamind/data/models/auth_models.dart';
import 'package:hermes_linguamind/data/services/secure_storage_service.dart';

class AuthAdapter {
  factory AuthAdapter() => _instance;
  AuthAdapter._();
  static final AuthAdapter _instance = AuthAdapter._();

  final ApiClient _client = ApiClient();
  final SecureStorageService _storage = SecureStorageService();

  Future<AuthResponse> login(final LoginRequest request) async {
    try {
      final response = await _client.post<dynamic>(
        ApiEndpoints.login,
        data: request.toJson(),
      );
      final authResponse = _unwrapAuthEnvelope(
        response.data as Map<String, dynamic>,
      );
      await _saveTokens(authResponse);
      return authResponse;
    } on DioException catch (e) {
      AppLogger.error('Login failed', e);
      throw _handleError(e);
    }
  }

  Future<AuthResponse> register(final RegisterRequest request) async {
    try {
      final response = await _client.post<dynamic>(
        ApiEndpoints.register,
        data: request.toJson(),
      );
      final authResponse = _unwrapAuthEnvelope(
        response.data as Map<String, dynamic>,
      );
      await _saveTokens(authResponse);
      return authResponse;
    } on DioException catch (e) {
      AppLogger.error('Registration failed', e);
      throw _handleError(e);
    }
  }

  /// The gateway wraps every response in a `HermesResponse` envelope:
  /// `{success, data: {...}, error, request_id}`. Unwrap it here and
  /// surface `error` as a thrown exception when `success` is false, so
  /// only the actual payload reaches [AuthResponse.fromJson].
  AuthResponse _unwrapAuthEnvelope(final Map<String, dynamic> envelope) {
    final success = envelope['success'] as bool? ?? false;
    if (!success) {
      throw Exception(
        envelope['error'] as String? ?? 'Authentication request failed',
      );
    }
    final data = envelope['data'] as Map<String, dynamic>? ?? {};
    return AuthResponse.fromJson(data);
  }

  Future<void> logout() async {
    await _storage.delete(key: AppConstants.accessTokenKey);
    await _storage.delete(key: AppConstants.refreshTokenKey);
    await _storage.delete(key: AppConstants.userDataKey);
  }

  Future<bool> isAuthenticated() async {
    final token = await _storage.read(key: AppConstants.accessTokenKey);
    return token != null && token.isNotEmpty;
  }

  Future<String?> getToken() async {
    return _storage.read(key: AppConstants.accessTokenKey);
  }

  Future<Map<String, dynamic>?> getCurrentUser() async {
    try {
      final response = await _client.get<dynamic>(ApiEndpoints.me);
      final envelope = response.data as Map<String, dynamic>?;
      if (envelope == null) return null;
      // /v1/auth/me is also wrapped in the HermesResponse envelope.
      if (envelope.containsKey('success')) {
        if (envelope['success'] != true) return null;
        return envelope['data'] as Map<String, dynamic>?;
      }
      return envelope;
    } on DioException catch (e) {
      AppLogger.error('Get current user failed', e);
      return null;
    }
  }

  Future<void> _saveTokens(final AuthResponse response) async {
    await _storage.write(
      key: AppConstants.accessTokenKey,
      value: response.accessToken,
    );
    await _storage.write(
      key: AppConstants.refreshTokenKey,
      value: response.refreshToken,
    );
    await _storage.write(
      key: AppConstants.userDataKey,
      value: jsonEncode(response.user),
    );
  }

  Exception _handleError(final DioException e) {
    final response = e.response;
    if (response != null) {
      final data = response.data as Map<String, dynamic>?;
      final message =
          data?['detail'] as String? ??
          data?['message'] as String? ??
          'Request failed';
      return Exception(message);
    }
    return Exception('Network error. Please check your connection.');
  }
}
