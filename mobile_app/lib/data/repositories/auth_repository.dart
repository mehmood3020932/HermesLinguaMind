import 'package:hermes_linguamind/data/adapters/auth_adapter.dart';
import 'package:hermes_linguamind/data/models/auth_models.dart';
import 'package:hermes_linguamind/data/models/user_model.dart';

class AuthRepository {
  factory AuthRepository() => _instance;
  AuthRepository._();
  static final AuthRepository _instance = AuthRepository._();

  final AuthAdapter _adapter = AuthAdapter();

  Future<AuthResponse> login(final String email, final String password) async {
    return _adapter.login(LoginRequest(email: email, password: password));
  }

  Future<AuthResponse> register({
    required final String email,
    required final String password,
    required final String username,
    required final String displayName,
    final String targetLanguage = 'en',
    final String nativeLanguage = 'en',
  }) async {
    return _adapter.register(
      RegisterRequest(
        email: email,
        password: password,
        username: username,
        displayName: displayName,
        targetLanguage: targetLanguage,
        nativeLanguage: nativeLanguage,
      ),
    );
  }

  Future<void> logout() async {
    await _adapter.logout();
  }

  Future<bool> isAuthenticated() async {
    return _adapter.isAuthenticated();
  }

  Future<UserModel?> getCurrentUser() async {
    final data = await _adapter.getCurrentUser();
    if (data != null) {
      return UserModel.fromJson(data);
    }
    return null;
  }
}
