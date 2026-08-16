import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hermes_linguamind/data/models/user_model.dart';
import 'package:hermes_linguamind/data/repositories/auth_repository.dart';

class HomeState {
  const HomeState({this.user, this.selectedIndex = 0, this.isLoading = false});

  final UserModel? user;
  final int selectedIndex;
  final bool isLoading;

  HomeState copyWith({
    final UserModel? user,
    final int? selectedIndex,
    final bool? isLoading,
  }) => HomeState(
    user: user ?? this.user,
    selectedIndex: selectedIndex ?? this.selectedIndex,
    isLoading: isLoading ?? this.isLoading,
  );
}

class HomeNotifier extends StateNotifier<HomeState> {
  HomeNotifier() : super(const HomeState()) {
    _loadUser();
  }

  final AuthRepository _repository = AuthRepository();

  Future<void> _loadUser() async {
    state = state.copyWith(isLoading: true);
    try {
      final user = await _repository.getCurrentUser();
      state = state.copyWith(user: user, isLoading: false);
    } on Exception catch (_) {
      state = state.copyWith(isLoading: false);
    }
  }

  void setIndex(final int index) =>
      state = state.copyWith(selectedIndex: index);
}

final homeProvider = StateNotifierProvider<HomeNotifier, HomeState>(
  (final ref) => HomeNotifier(),
);
