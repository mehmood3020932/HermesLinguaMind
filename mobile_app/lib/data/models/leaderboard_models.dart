import 'package:equatable/equatable.dart';

class LeaderboardEntry extends Equatable {
  const LeaderboardEntry({
    required this.rank,
    required this.userId,
    required this.username,
    required this.displayName,
    required this.xp,
    required this.streakDays,
    this.avatarUrl,
    this.isCurrentUser = false,
    this.rankChange = 0,
  });

  factory LeaderboardEntry.fromJson(final Map<String, dynamic> json) =>
      LeaderboardEntry(
        rank: json['rank'] as int? ?? 0,
        userId: json['user_id'] as String? ?? '',
        username: json['username'] as String? ?? '',
        displayName: json['display_name'] as String? ?? '',
        xp: json['xp'] as int? ?? 0,
        streakDays: json['streak_days'] as int? ?? 0,
        avatarUrl: json['avatar_url'] as String?,
        isCurrentUser: json['is_current_user'] as bool? ?? false,
        rankChange: json['rank_change'] as int? ?? 0,
      );

  final int rank;
  final String userId;
  final String username;
  final String displayName;
  final int xp;
  final int streakDays;
  final String? avatarUrl;
  final bool isCurrentUser;
  final int rankChange;

  Map<String, dynamic> toJson() => {
    'rank': rank,
    'user_id': userId,
    'username': username,
    'display_name': displayName,
    'xp': xp,
    'streak_days': streakDays,
    'avatar_url': avatarUrl,
    'is_current_user': isCurrentUser,
    'rank_change': rankChange,
  };

  @override
  List<Object?> get props => [rank, userId, xp];
}

class LeaderboardResponse extends Equatable {
  const LeaderboardResponse({
    required this.entries,
    required this.totalCount,
    required this.currentUserRank,
    required this.period,
  });

  factory LeaderboardResponse.fromJson(final Map<String, dynamic> json) =>
      LeaderboardResponse(
        entries: (json['entries'] as List<dynamic>? ?? [])
            .map(
              (final e) => LeaderboardEntry.fromJson(e as Map<String, dynamic>),
            )
            .toList(),
        totalCount: json['total_count'] as int? ?? 0,
        currentUserRank: json['current_user_rank'] as int? ?? 0,
        period: json['period'] as String? ?? 'weekly',
      );

  final List<LeaderboardEntry> entries;
  final int totalCount;
  final int currentUserRank;
  final String period;

  @override
  List<Object?> get props => [entries, totalCount, currentUserRank, period];
}
