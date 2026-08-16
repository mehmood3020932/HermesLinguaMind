import 'package:dio/dio.dart';
import 'package:hermes_linguamind/core/constants/api_endpoints.dart';
import 'package:hermes_linguamind/core/utils/logger.dart';
import 'package:hermes_linguamind/data/adapters/api_client.dart';
import 'package:hermes_linguamind/data/models/leaderboard_models.dart';

class LeaderboardAdapter {
  factory LeaderboardAdapter() => _instance;
  LeaderboardAdapter._();
  static final LeaderboardAdapter _instance = LeaderboardAdapter._();

  final ApiClient _client = ApiClient();

  Future<LeaderboardResponse> getLeaderboard({
    final String period = 'weekly',
    final int page = 1,
    final int pageSize = 20,
  }) async {
    try {
      final response = await _client.get<dynamic>(
        ApiEndpoints.leaderboard,
        queryParameters: {
          'period': period,
          'page': page,
          'page_size': pageSize,
        },
      );
      return LeaderboardResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      AppLogger.error('Get leaderboard failed', e);
      throw _handleError(e);
    }
  }

  Future<void> submitScore({
    required final String userId,
    required final int xp,
    required final int streakDays,
  }) async {
    try {
      await _client.post<dynamic>(
        ApiEndpoints.submitScore,
        data: {'user_id': userId, 'xp': xp, 'streak_days': streakDays},
      );
    } on DioException catch (e) {
      AppLogger.error('Submit score failed', e);
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
          'Leaderboard request failed';
      return Exception(message);
    }
    return Exception('Network error. Please check your connection.');
  }
}
