import 'package:flutter_test/flutter_test.dart';
import 'package:hermes_linguamind/data/models/leaderboard_models.dart';

void main() {
  group('LeaderboardEntry', () {
    test('fromJson parses correctly', () {
      final json = {
        'rank': 1,
        'user_id': 'user_1',
        'username': 'test_user',
        'display_name': 'Test User',
        'xp': 1000,
        'streak_days': 7,
        'is_current_user': false,
        'rank_change': 2,
      };
      final entry = LeaderboardEntry.fromJson(json);
      expect(entry.rank, 1);
      expect(entry.userId, 'user_1');
      expect(entry.xp, 1000);
    });

    test('toJson serializes correctly', () {
      const entry = LeaderboardEntry(
        rank: 1,
        userId: 'user_1',
        username: 'test',
        displayName: 'Test',
        xp: 100,
        streakDays: 5,
      );
      final json = entry.toJson();
      expect(json['rank'], 1);
      expect(json['user_id'], 'user_1');
    });
  });
}
