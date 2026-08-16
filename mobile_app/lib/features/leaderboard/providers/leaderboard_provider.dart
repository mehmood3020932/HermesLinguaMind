import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hermes_linguamind/data/models/leaderboard_models.dart';
import 'package:hermes_linguamind/data/repositories/leaderboard_repository.dart';

class LeaderboardState {
  const LeaderboardState({
    this.entries = const [],
    this.isLoading = false,
    this.error,
    this.selectedPeriod = 'weekly',
    this.currentUserRank = 0,
    this.hasMore = true,
    this.page = 1,
  });

  final List<LeaderboardEntry> entries;
  final bool isLoading;
  final String? error;
  final String selectedPeriod;
  final int currentUserRank;
  final bool hasMore;
  final int page;

  LeaderboardState copyWith({
    final List<LeaderboardEntry>? entries,
    final bool? isLoading,
    final String? error,
    final String? selectedPeriod,
    final int? currentUserRank,
    final bool? hasMore,
    final int? page,
  }) => LeaderboardState(
    entries: entries ?? this.entries,
    isLoading: isLoading ?? this.isLoading,
    error: error,
    selectedPeriod: selectedPeriod ?? this.selectedPeriod,
    currentUserRank: currentUserRank ?? this.currentUserRank,
    hasMore: hasMore ?? this.hasMore,
    page: page ?? this.page,
  );
}

class LeaderboardNotifier extends StateNotifier<LeaderboardState> {
  LeaderboardNotifier() : super(const LeaderboardState()) {
    loadLeaderboard();
  }

  final LeaderboardRepository _repository = LeaderboardRepository();

  Future<void> loadLeaderboard({final bool refresh = false}) async {
    if (refresh) {
      state = state.copyWith(page: 1, entries: [], hasMore: true);
    }
    if (!state.hasMore && !refresh) return;

    state = state.copyWith(isLoading: true);

    try {
      final response = await _repository.getLeaderboard(
        period: state.selectedPeriod,
        page: state.page,
      );

      final allEntries = refresh
          ? response.entries
          : [...state.entries, ...response.entries];

      state = state.copyWith(
        entries: allEntries,
        isLoading: false,
        currentUserRank: response.currentUserRank,
        hasMore: response.entries.length >= 20,
        page: state.page + 1,
      );
    } on Exception catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void setPeriod(final String period) {
    state = state.copyWith(
      selectedPeriod: period,
      page: 1,
      entries: [],
      hasMore: true,
    );
    loadLeaderboard(refresh: true);
  }
}

final leaderboardProvider =
    StateNotifierProvider<LeaderboardNotifier, LeaderboardState>((final ref) {
      return LeaderboardNotifier();
    });
