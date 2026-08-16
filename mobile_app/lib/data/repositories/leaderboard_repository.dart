import 'package:hermes_linguamind/data/adapters/leaderboard_adapter.dart';
import 'package:hermes_linguamind/data/models/leaderboard_models.dart';

class LeaderboardRepository {
  factory LeaderboardRepository() => _instance;
  LeaderboardRepository._();
  static final LeaderboardRepository _instance = LeaderboardRepository._();

  final LeaderboardAdapter _adapter = LeaderboardAdapter();

  Future<LeaderboardResponse> getLeaderboard({
    final String period = 'weekly',
    final int page = 1,
    final int pageSize = 20,
  }) async {
    return _adapter.getLeaderboard(
      period: period,
      page: page,
      pageSize: pageSize,
    );
  }

  Future<void> submitScore({
    required final String userId,
    required final int xp,
    required final int streakDays,
  }) async {
    return _adapter.submitScore(userId: userId, xp: xp, streakDays: streakDays);
  }
}
