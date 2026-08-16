import 'dart:io';

import 'package:dio/dio.dart';
import 'package:hermes_linguamind/core/constants/api_endpoints.dart';
import 'package:hermes_linguamind/core/constants/app_constants.dart';
import 'package:hermes_linguamind/core/utils/logger.dart';
import 'package:hermes_linguamind/data/models/avatar_models.dart';
import 'package:hermes_linguamind/data/services/secure_storage_service.dart';

/// REST calls to avatar_service (JWT-protected session control). This is
/// a SEPARATE Dio instance from ApiClient — avatar_service is mounted at
/// the gateway root (/svc/avatar), not under /svc/api-gateway, so it
/// needs its own baseUrl (AppConstants.avatarServiceBaseUrl). It still
/// attaches the same bearer token, since avatar_service's routes are all
/// `Depends(get_current_user)`.
class AvatarAdapter {
  factory AvatarAdapter() => _instance;
  AvatarAdapter._() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.avatarServiceBaseUrl,
        connectTimeout: AppConstants.apiConnectTimeout,
        receiveTimeout: AppConstants.apiTimeout,
        headers: {'Accept': 'application/json'},
      ),
    );
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (final options, final handler) async {
          final token = await _storage.read(key: AppConstants.accessTokenKey);
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
      ),
    );
  }
  static final AvatarAdapter _instance = AvatarAdapter._();

  late final Dio _dio;
  final SecureStorageService _storage = SecureStorageService();

  /// Starts a new avatar session for [characterSlug] (e.g.
  /// 'hermes-default'). Returns everything needed to open the WebRTC
  /// connection directly against OpenTalking.
  Future<AvatarSession> createSession(final String characterSlug) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        ApiEndpoints.avatarSessions,
        data: {'character_slug': characterSlug},
      );
      final envelope = response.data ?? const {};
      if (envelope['success'] != true) {
        throw AvatarException(
          (envelope['error'] as String?) ?? 'Failed to start avatar session',
          code: envelope['error_code'] as String?,
        );
      }
      return AvatarSession.fromJson(
        (envelope['data'] as Map<String, dynamic>?) ?? const {},
      );
    } on DioException catch (e) {
      AppLogger.error('Avatar session creation failed', e);
      throw _handleError(e);
    }
  }

  /// Sends a text turn — OpenTalking drives the LLM→TTS→render pipeline
  /// itself and streams the reply back over the already-open WebRTC
  /// connection; this call only kicks the turn off.
  Future<void> sendMessage(final String sessionId, final String text) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        ApiEndpoints.avatarSessionMessage(sessionId),
        data: {'text': text},
      );
      final envelope = response.data ?? const {};
      if (envelope['success'] != true) {
        throw AvatarException(
          (envelope['error'] as String?) ?? 'Failed to deliver message',
          code: envelope['error_code'] as String?,
        );
      }
    } on DioException catch (e) {
      AppLogger.error('Avatar sendMessage failed', e);
      throw _handleError(e);
    }
  }

  /// Uploads a captured voice clip; the backend transcribes it with its
  /// own STT service and forwards the transcript exactly like
  /// [sendMessage] — one STT stack, not two (see avatar_service docstring).
  Future<void> sendAudio(final String sessionId, final File audioFile) async {
    try {
      final formData = FormData.fromMap({
        'audio': await MultipartFile.fromFile(audioFile.path),
      });
      final response = await _dio.post<Map<String, dynamic>>(
        ApiEndpoints.avatarSessionAudio(sessionId),
        data: formData,
      );
      final envelope = response.data ?? const {};
      if (envelope['success'] != true) {
        throw AvatarException(
          (envelope['error'] as String?) ?? 'Failed to send audio',
          code: envelope['error_code'] as String?,
        );
      }
    } on DioException catch (e) {
      AppLogger.error('Avatar sendAudio failed', e);
      throw _handleError(e);
    }
  }

  /// Barge-in: cancels the avatar's in-flight LLM/TTS/render turn.
  Future<void> interrupt(final String sessionId) async {
    try {
      await _dio.post<Map<String, dynamic>>(
        ApiEndpoints.avatarSessionInterrupt(sessionId),
      );
    } on DioException catch (e) {
      AppLogger.error('Avatar interrupt failed', e);
      // Non-fatal — don't throw; the call is a best-effort UX nicety.
    }
  }

  Future<void> endSession(final String sessionId) async {
    try {
      await _dio.delete<Map<String, dynamic>>(
        ApiEndpoints.avatarSession(sessionId),
      );
    } on DioException catch (e) {
      AppLogger.error('Avatar endSession failed', e);
      // Non-fatal — the session idles out on OpenTalking's side regardless.
    }
  }

  Exception _handleError(final DioException e) {
    final response = e.response;
    if (response != null) {
      final data = response.data;
      final message = data is Map
          ? (data['error'] as String? ??
                data['detail'] as String? ??
                'Avatar request failed')
          : 'Avatar request failed';
      return AvatarException(message);
    }
    return AvatarException('Network error. Please check your connection.');
  }
}

class AvatarException implements Exception {
  AvatarException(this.message, {this.code});
  final String message;
  final String? code;

  @override
  String toString() => message;
}
