import 'package:hermes_linguamind/core/utils/extensions.dart';

/// Input validation utilities
class Validators {
  Validators._();

  static String? required(
    final String? value, {
    final String fieldName = 'This field',
  }) {
    if (value == null || value.trim().isEmpty) {
      return '$fieldName is required';
    }
    return null;
  }

  static String? email(final String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Email is required';
    }
    if (!value.isValidEmail) {
      return 'Please enter a valid email address';
    }
    return null;
  }

  static String? password(final String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }
    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }
    if (!value.isStrongPassword) {
      return 'Password must contain uppercase, lowercase, number, and special character';
    }
    return null;
  }

  static String? confirmPassword(final String? value, final String? original) {
    if (value == null || value.isEmpty) {
      return 'Please confirm your password';
    }
    if (value != original) {
      return 'Passwords do not match';
    }
    return null;
  }

  static String? username(final String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Username is required';
    }
    if (value.length < 3) {
      return 'Username must be at least 3 characters';
    }
    if (value.length > 30) {
      return 'Username must be at most 30 characters';
    }
    final validChars = RegExp(r'^[a-zA-Z0-9_]+$');
    if (!validChars.hasMatch(value)) {
      return 'Username can only contain letters, numbers, and underscores';
    }
    return null;
  }

  static String? displayName(final String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Display name is required';
    }
    if (value.length < 2) {
      return 'Display name must be at least 2 characters';
    }
    if (value.length > 50) {
      return 'Display name must be at most 50 characters';
    }
    return null;
  }

  static String? bio(final String? value) {
    if (value == null) return null;
    if (value.length > 500) {
      return 'Bio must be at most 500 characters';
    }
    return null;
  }
}
