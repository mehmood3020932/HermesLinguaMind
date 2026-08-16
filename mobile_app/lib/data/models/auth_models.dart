import 'package:equatable/equatable.dart';

class LoginRequest extends Equatable {
  const LoginRequest({required this.email, required this.password});
  final String email;
  final String password;

  // The backend's /v1/auth/login expects a `username` field, but it
  // indexes registered users by BOTH email and username internally, so
  // sending the email address under the `username` key resolves
  // correctly without requiring a separate "username" field in the UI.
  Map<String, dynamic> toJson() => {'username': email, 'password': password};

  @override
  List<Object?> get props => [email, password];
}

class RegisterRequest extends Equatable {
  const RegisterRequest({
    required this.email,
    required this.password,
    required this.username,
    required this.displayName,
    this.targetLanguage = 'en',
    this.nativeLanguage = 'en',
  });
  final String email;
  final String password;
  final String username;
  final String displayName;
  final String targetLanguage;
  final String nativeLanguage;

  Map<String, dynamic> toJson() => {
    'email': email,
    'password': password,
    'username': username,
    'display_name': displayName,
    // Backend field is `learning_language`, not `target_language`.
    'learning_language': targetLanguage,
    'native_language': nativeLanguage,
  };

  @override
  List<Object?> get props => [email, username, displayName];
}

class AuthResponse extends Equatable {
  const AuthResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresIn,
    required this.user,
  });

  factory AuthResponse.fromJson(final Map<String, dynamic> json) =>
      AuthResponse(
        accessToken: json['access_token'] as String? ?? '',
        refreshToken: json['refresh_token'] as String? ?? '',
        expiresIn: json['expires_in'] as int? ?? 3600,
        user: json['user'] as Map<String, dynamic>? ?? {},
      );
  final String accessToken;
  final String refreshToken;
  final int expiresIn;
  final Map<String, dynamic> user;

  @override
  List<Object?> get props => [accessToken, refreshToken, expiresIn];
}
