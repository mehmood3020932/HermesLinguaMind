import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hermes_linguamind/data/models/user_model.dart';
import 'package:hermes_linguamind/data/repositories/auth_repository.dart';

class AuthState {
  const AuthState({
    this.user,
    this.isLoading = false,
    this.error,
    this.isAuthenticated = false,
  });

  final UserModel? user;
  final bool isLoading;
  final String? error;
  final bool isAuthenticated;

  AuthState copyWith({
    final UserModel? user,
    final bool? isLoading,
    final String? error,
    final bool? isAuthenticated,
  }) => AuthState(
    user: user ?? this.user,
    isLoading: isLoading ?? this.isLoading,
    error: error,
    isAuthenticated: isAuthenticated ?? this.isAuthenticated,
  );
}

class AuthNotifier extends StateNotifier<AsyncValue<AuthState>> {
  AuthNotifier() : super(const AsyncValue.data(AuthState())) {
    _checkAuthStatus();
  }

  final AuthRepository _repository = AuthRepository();

  Future<void> _checkAuthStatus() async {
    state = const AsyncValue.loading();
    try {
      final isAuth = await _repository.isAuthenticated();
      if (isAuth) {
        final user = await _repository.getCurrentUser();
        state = AsyncValue.data(AuthState(user: user, isAuthenticated: true));
      } else {
        state = const AsyncValue.data(AuthState());
      }
    } on Exception catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  Future<void> login(final String email, final String password) async {
    state = const AsyncValue.loading();
    try {
      final response = await _repository.login(email, password);
      final user = UserModel.fromJson(response.user);
      state = AsyncValue.data(AuthState(user: user, isAuthenticated: true));
    } on Exception catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  Future<void> register({
    required final String email,
    required final String password,
    required final String username,
    required final String displayName,
    final String targetLanguage = 'en',
    final String nativeLanguage = 'en',
  }) async {
    state = const AsyncValue.loading();
    try {
      final response = await _repository.register(
        email: email,
        password: password,
        username: username,
        displayName: displayName,
        targetLanguage: targetLanguage,
        nativeLanguage: nativeLanguage,
      );
      final user = UserModel.fromJson(response.user);
      state = AsyncValue.data(AuthState(user: user, isAuthenticated: true));
    } on Exception catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  Future<void> logout() async {
    await _repository.logout();
    state = const AsyncValue.data(AuthState());
  }
}

final authStateProvider =
    StateNotifierProvider<AuthNotifier, AsyncValue<AuthState>>((final ref) {
      return AuthNotifier();
    });
