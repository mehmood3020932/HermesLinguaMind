import 'package:flutter_test/flutter_test.dart';
import 'package:hermes_linguamind/data/models/social_models.dart';

void main() {
  group('SocialProfile', () {
    test('fromJson parses correctly', () {
      final json = {
        'user_id': 'user_1',
        'username': 'test_user',
        'display_name': 'Test User',
        'xp': 500,
        'streak_days': 3,
        'languages': ['en', 'es'],
        'is_online': true,
      };
      final profile = SocialProfile.fromJson(json);
      expect(profile.userId, 'user_1');
      expect(profile.languages.length, 2);
      expect(profile.isOnline, true);
    });
  });
}
