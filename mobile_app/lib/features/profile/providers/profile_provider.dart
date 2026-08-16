import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hermes_linguamind/data/models/user_model.dart';
import 'package:hermes_linguamind/data/repositories/auth_repository.dart';

class ProfileState {
  const ProfileState({
    this.user,
    this.isLoading = false,
    this.error,
    this.isEditing = false,
  });

  final UserModel? user;
  final bool isLoading;
  final String? error;
  final bool isEditing;

  ProfileState copyWith({
    final UserModel? user,
    final bool? isLoading,
    final String? error,
    final bool? isEditing,
  }) => ProfileState(
    user: user ?? this.user,
    isLoading: isLoading ?? this.isLoading,
    error: error,
    isEditing: isEditing ?? this.isEditing,
  );
}

class ProfileNotifier extends StateNotifier<ProfileState> {
  ProfileNotifier() : super(const ProfileState()) {
    loadProfile();
  }

  final AuthRepository _repository = AuthRepository();

  Future<void> loadProfile() async {
    state = state.copyWith(isLoading: true);
    try {
      final user = await _repository.getCurrentUser();
      state = state.copyWith(user: user, isLoading: false);
    } on Exception catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void setEditing({required final bool editing}) {
    state = state.copyWith(isEditing: editing);
  }

  Future<void> updateProfile({
    final String? displayName,
    final String? bio,
    final int? characterSkinIndex,
  }) async {
    state = state.copyWith(isLoading: true);
    try {
      // In production, this would call the backend
      final updatedUser = state.user?.copyWith(
        displayName: displayName,
        bio: bio,
        characterSkinIndex: characterSkinIndex,
      );
      state = state.copyWith(
        user: updatedUser,
        isLoading: false,
        isEditing: false,
      );
    } on Exception catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }
}

final profileProvider = StateNotifierProvider<ProfileNotifier, ProfileState>((
  final ref,
) {
  return ProfileNotifier();
});
