import 'package:equatable/equatable.dart';

class UserModel extends Equatable {
  const UserModel({
    required this.id,
    required this.email,
    required this.username,
    required this.displayName,
    this.avatarUrl,
    this.bio,
    this.targetLanguage = 'en',
    this.nativeLanguage = 'en',
    this.cefrLevel = 'A1',
    this.xp = 0,
    this.coins = 0,
    this.streakDays = 0,
    this.longestStreak = 0,
    this.lastStudyDate,
    this.characterSkinIndex = 0,
    this.isPremium = false,
    this.createdAt,
    this.updatedAt,
  });

  factory UserModel.fromJson(final Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String? ?? json['user_id'] as String? ?? '',
      email: json['email'] as String? ?? '',
      username: json['username'] as String? ?? '',
      displayName:
          json['display_name'] as String? ??
          json['displayName'] as String? ??
          '',
      avatarUrl: json['avatar_url'] as String? ?? json['avatarUrl'] as String?,
      bio: json['bio'] as String?,
      targetLanguage:
          json['target_language'] as String? ??
          json['targetLanguage'] as String? ??
          'en',
      nativeLanguage:
          json['native_language'] as String? ??
          json['nativeLanguage'] as String? ??
          'en',
      cefrLevel:
          json['cefr_level'] as String? ?? json['cefrLevel'] as String? ?? 'A1',
      xp: json['xp'] as int? ?? 0,
      coins: json['coins'] as int? ?? 0,
      streakDays:
          json['streak_days'] as int? ?? json['streakDays'] as int? ?? 0,
      longestStreak:
          json['longest_streak'] as int? ?? json['longestStreak'] as int? ?? 0,
      lastStudyDate: json['last_study_date'] != null
          ? DateTime.parse(json['last_study_date'] as String)
          : null,
      characterSkinIndex:
          json['character_skin_index'] as int? ??
          json['characterSkinIndex'] as int? ??
          0,
      isPremium:
          json['is_premium'] as bool? ?? json['isPremium'] as bool? ?? false,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : null,
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'] as String)
          : null,
    );
  }

  final String id;
  final String email;
  final String username;
  final String displayName;
  final String? avatarUrl;
  final String? bio;
  final String targetLanguage;
  final String nativeLanguage;
  final String cefrLevel;
  final int xp;
  final int coins;
  final int streakDays;
  final int longestStreak;
  final DateTime? lastStudyDate;
  final int characterSkinIndex;
  final bool isPremium;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  Map<String, dynamic> toJson() => {
    'id': id,
    'email': email,
    'username': username,
    'display_name': displayName,
    'avatar_url': avatarUrl,
    'bio': bio,
    'target_language': targetLanguage,
    'native_language': nativeLanguage,
    'cefr_level': cefrLevel,
    'xp': xp,
    'coins': coins,
    'streak_days': streakDays,
    'longest_streak': longestStreak,
    'last_study_date': lastStudyDate?.toIso8601String(),
    'character_skin_index': characterSkinIndex,
    'is_premium': isPremium,
    'created_at': createdAt?.toIso8601String(),
    'updated_at': updatedAt?.toIso8601String(),
  };

  UserModel copyWith({
    final String? id,
    final String? email,
    final String? username,
    final String? displayName,
    final String? avatarUrl,
    final String? bio,
    final String? targetLanguage,
    final String? nativeLanguage,
    final String? cefrLevel,
    final int? xp,
    final int? coins,
    final int? streakDays,
    final int? longestStreak,
    final DateTime? lastStudyDate,
    final int? characterSkinIndex,
    final bool? isPremium,
    final DateTime? createdAt,
    final DateTime? updatedAt,
  }) => UserModel(
    id: id ?? this.id,
    email: email ?? this.email,
    username: username ?? this.username,
    displayName: displayName ?? this.displayName,
    avatarUrl: avatarUrl ?? this.avatarUrl,
    bio: bio ?? this.bio,
    targetLanguage: targetLanguage ?? this.targetLanguage,
    nativeLanguage: nativeLanguage ?? this.nativeLanguage,
    cefrLevel: cefrLevel ?? this.cefrLevel,
    xp: xp ?? this.xp,
    coins: coins ?? this.coins,
    streakDays: streakDays ?? this.streakDays,
    longestStreak: longestStreak ?? this.longestStreak,
    lastStudyDate: lastStudyDate ?? this.lastStudyDate,
    characterSkinIndex: characterSkinIndex ?? this.characterSkinIndex,
    isPremium: isPremium ?? this.isPremium,
    createdAt: createdAt ?? this.createdAt,
    updatedAt: updatedAt ?? this.updatedAt,
  );

  @override
  List<Object?> get props => [
    id,
    email,
    username,
    displayName,
    xp,
    coins,
    streakDays,
    characterSkinIndex,
  ];
}
