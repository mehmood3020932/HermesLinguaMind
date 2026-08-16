import 'package:hermes_linguamind/data/adapters/social_adapter.dart';
import 'package:hermes_linguamind/data/models/social_models.dart';

class SocialRepository {
  factory SocialRepository() => _instance;
  SocialRepository._();
  static final SocialRepository _instance = SocialRepository._();

  final SocialAdapter _adapter = SocialAdapter();

  Future<MatchResult> findMatch({
    required final String userId,
    required final String targetLanguage,
  }) async {
    return _adapter.findMatch(userId: userId, targetLanguage: targetLanguage);
  }

  Future<SocialProfile> getSocialProfile(final String userId) async {
    return _adapter.getSocialProfile(userId);
  }

  Future<void> reportUser({
    required final String userId,
    required final String reason,
    final String? details,
  }) async {
    return _adapter.reportUser(
      userId: userId,
      reason: reason,
      details: details,
    );
  }
}
