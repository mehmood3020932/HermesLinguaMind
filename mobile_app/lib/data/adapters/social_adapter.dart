import 'package:dio/dio.dart';
import 'package:hermes_linguamind/core/constants/api_endpoints.dart';
import 'package:hermes_linguamind/core/utils/logger.dart';
import 'package:hermes_linguamind/data/adapters/api_client.dart';
import 'package:hermes_linguamind/data/models/social_models.dart';

class SocialAdapter {
  factory SocialAdapter() => _instance;
  SocialAdapter._();
  static final SocialAdapter _instance = SocialAdapter._();

  final ApiClient _client = ApiClient();

  Future<MatchResult> findMatch({
    required final String userId,
    required final String targetLanguage,
  }) async {
    try {
      final response = await _client.post<dynamic>(
        ApiEndpoints.socialMatch,
        data: {'user_id': userId, 'target_language': targetLanguage},
      );
      return MatchResult.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      AppLogger.error('Find match failed', e);
      throw _handleError(e);
    }
  }

  Future<SocialProfile> getSocialProfile(final String userId) async {
    try {
      final response = await _client.get<dynamic>(
        '${ApiEndpoints.socialProfile}/$userId',
      );
      return SocialProfile.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      AppLogger.error('Get social profile failed', e);
      throw _handleError(e);
    }
  }

  Future<void> reportUser({
    required final String userId,
    required final String reason,
    final String? details,
  }) async {
    try {
      await _client.post<dynamic>(
        ApiEndpoints.socialReport,
        data: {'user_id': userId, 'reason': reason, 'details': details},
      );
    } on DioException catch (e) {
      AppLogger.error('Report user failed', e);
      throw _handleError(e);
    }
  }

  Exception _handleError(final DioException e) {
    final response = e.response;
    if (response != null) {
      final data = response.data as Map<String, dynamic>?;
      final message =
          data?['detail'] as String? ??
          data?['message'] as String? ??
          'Social request failed';
      return Exception(message);
    }
    return Exception('Network error. Please check your connection.');
  }
}
