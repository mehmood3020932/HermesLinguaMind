import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Smoke Tests', () {
    test('basic arithmetic works', () {
      expect(1 + 1, equals(2));
    });

    test('string operations work', () {
      final greeting = 'Hello Hermes';
      expect(greeting.contains('Hermes'), isTrue);
    });

    test('list operations work', () {
      final languages = ['Urdu', 'English', 'Arabic'];
      expect(languages.length, equals(3));
      expect(languages, contains('Urdu'));
    });
  });
}
