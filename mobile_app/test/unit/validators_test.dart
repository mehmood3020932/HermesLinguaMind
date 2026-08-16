import 'package:flutter_test/flutter_test.dart';
import 'package:hermes_linguamind/core/utils/validators.dart';

void main() {
  group('Validators', () {
    test('email validates correctly', () {
      expect(Validators.email('test@example.com'), null);
      expect(Validators.email('invalid'), isNotNull);
      expect(Validators.email(''), isNotNull);
      expect(Validators.email(null), isNotNull);
    });

    test('password validates correctly', () {
      expect(Validators.password('StrongP@ss1'), null);
      expect(Validators.password('weak'), isNotNull);
      expect(Validators.password(''), isNotNull);
    });

    test('username validates correctly', () {
      expect(Validators.username('john_doe'), null);
      expect(Validators.username('ab'), isNotNull);
      expect(Validators.username(''), isNotNull);
    });

    test('displayName validates correctly', () {
      expect(Validators.displayName('John Doe'), null);
      expect(Validators.displayName('A'), isNotNull);
      expect(Validators.displayName(''), isNotNull);
    });

    test('confirmPassword validates correctly', () {
      expect(Validators.confirmPassword('password', 'password'), null);
      expect(Validators.confirmPassword('password', 'different'), isNotNull);
    });
  });
}
