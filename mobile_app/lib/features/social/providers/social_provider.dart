import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hermes_linguamind/data/models/social_models.dart';
import 'package:hermes_linguamind/data/repositories/social_repository.dart';

class SocialState {
  const SocialState({
    this.profiles = const [],
    this.currentMatch,
    this.isLoading = false,
    this.error,
    this.messages = const [],
  });

  final List<SocialProfile> profiles;
  final MatchResult? currentMatch;
  final bool isLoading;
  final String? error;
  final List<ConversationMessage> messages;

  SocialState copyWith({
    final List<SocialProfile>? profiles,
    final MatchResult? currentMatch,
    final bool? isLoading,
    final String? error,
    final List<ConversationMessage>? messages,
  }) => SocialState(
    profiles: profiles ?? this.profiles,
    currentMatch: currentMatch ?? this.currentMatch,
    isLoading: isLoading ?? this.isLoading,
    error: error,
    messages: messages ?? this.messages,
  );
}

class SocialNotifier extends StateNotifier<SocialState> {
  SocialNotifier() : super(const SocialState());

  final SocialRepository _repository = SocialRepository();

  Future<void> findMatch(
    final String userId,
    final String targetLanguage,
  ) async {
    state = state.copyWith(isLoading: true);
    try {
      final match = await _repository.findMatch(
        userId: userId,
        targetLanguage: targetLanguage,
      );
      state = state.copyWith(currentMatch: match, isLoading: false);
    } on Exception catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> loadProfiles() async {
    state = state.copyWith(isLoading: true);
    try {
      // Mock profiles for demo
      final profiles = [
        const SocialProfile(
          userId: 'user_2',
          username: 'sarah_learns',
          displayName: 'Sarah',
          xp: 1250,
          streakDays: 14,
          languages: ['en', 'es'],
          isOnline: true,
        ),
        SocialProfile(
          userId: 'user_3',
          username: 'mike_lang',
          displayName: 'Mike',
          xp: 890,
          streakDays: 7,
          languages: const ['en', 'fr'],
          lastActive: DateTime.now().subtract(const Duration(minutes: 30)),
        ),
        const SocialProfile(
          userId: 'user_4',
          username: 'yuki_nihongo',
          displayName: 'Yuki',
          xp: 2100,
          streakDays: 30,
          languages: ['en', 'ja'],
          isOnline: true,
        ),
      ];
      state = state.copyWith(profiles: profiles, isLoading: false);
    } on Exception catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void clearMatch() {
    state = state.copyWith();
  }

  void sendMessage(final String content, final String senderId) {
    final message = ConversationMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      senderId: senderId,
      content: content,
      timestamp: DateTime.now(),
    );
    state = state.copyWith(messages: [...state.messages, message]);
  }
}

final socialProvider = StateNotifierProvider<SocialNotifier, SocialState>((
  final ref,
) {
  return SocialNotifier();
});
