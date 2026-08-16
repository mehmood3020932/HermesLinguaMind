import 'package:equatable/equatable.dart';

class SocialProfile extends Equatable {
  const SocialProfile({
    required this.userId,
    required this.username,
    required this.displayName,
    this.avatarUrl,
    this.bio,
    this.xp = 0,
    this.streakDays = 0,
    this.languages = const [],
    this.isOnline = false,
    this.lastActive,
  });

  factory SocialProfile.fromJson(final Map<String, dynamic> json) =>
      SocialProfile(
        userId: json['user_id'] as String? ?? '',
        username: json['username'] as String? ?? '',
        displayName: json['display_name'] as String? ?? '',
        avatarUrl: json['avatar_url'] as String?,
        bio: json['bio'] as String?,
        xp: json['xp'] as int? ?? 0,
        streakDays: json['streak_days'] as int? ?? 0,
        languages: (json['languages'] as List<dynamic>? ?? []).cast<String>(),
        isOnline: json['is_online'] as bool? ?? false,
        lastActive: json['last_active'] != null
            ? DateTime.parse(json['last_active'] as String)
            : null,
      );

  final String userId;
  final String username;
  final String displayName;
  final String? avatarUrl;
  final String? bio;
  final int xp;
  final int streakDays;
  final List<String> languages;
  final bool isOnline;
  final DateTime? lastActive;

  @override
  List<Object?> get props => [userId, username, xp];
}

class MatchResult extends Equatable {
  const MatchResult({
    required this.matchId,
    required this.partner,
    required this.commonLanguages,
    required this.compatibilityScore,
  });

  factory MatchResult.fromJson(final Map<String, dynamic> json) => MatchResult(
    matchId: json['match_id'] as String? ?? '',
    partner: SocialProfile.fromJson(
      json['partner'] as Map<String, dynamic>? ?? {},
    ),
    commonLanguages: (json['common_languages'] as List<dynamic>? ?? [])
        .cast<String>(),
    compatibilityScore: (json['compatibility_score'] as num? ?? 0).toDouble(),
  );

  final String matchId;
  final SocialProfile partner;
  final List<String> commonLanguages;
  final double compatibilityScore;

  @override
  List<Object?> get props => [matchId, partner.userId, compatibilityScore];
}

class ConversationMessage extends Equatable {
  const ConversationMessage({
    required this.id,
    required this.senderId,
    required this.content,
    required this.timestamp,
    this.isRead = false,
  });

  factory ConversationMessage.fromJson(final Map<String, dynamic> json) =>
      ConversationMessage(
        id: json['id'] as String? ?? '',
        senderId: json['sender_id'] as String? ?? '',
        content: json['content'] as String? ?? '',
        timestamp: DateTime.parse(json['timestamp'] as String),
        isRead: json['is_read'] as bool? ?? false,
      );

  final String id;
  final String senderId;
  final String content;
  final DateTime timestamp;
  final bool isRead;

  Map<String, dynamic> toJson() => {
    'id': id,
    'sender_id': senderId,
    'content': content,
    'timestamp': timestamp.toIso8601String(),
    'is_read': isRead,
  };

  @override
  List<Object?> get props => [id, senderId, timestamp];
}
