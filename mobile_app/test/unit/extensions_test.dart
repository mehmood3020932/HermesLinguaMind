import 'package:flutter_test/flutter_test.dart';
import 'package:hermes_linguamind/core/utils/extensions.dart';

void main() {
  group('StringX', () {
    test('capitalize works', () {
      expect('hello'.capitalize, 'Hello');
      expect(''.capitalize, '');
    });

    test('titleCase works', () {
      expect('hello world'.titleCase, 'Hello World');
    });

    test('isValidEmail works', () {
      expect('test@example.com'.isValidEmail, true);
      expect('invalid'.isValidEmail, false);
    });
  });

  group('NumberX', () {
    test('compact works', () {
      expect(1500.compact, '1.5K');
      expect(1500000.compact, '1.5M');
      expect(500.compact, '500');
    });

    test('ordinal works', () {
      expect(1.ordinal, '1st');
      expect(2.ordinal, '2nd');
      expect(3.ordinal, '3rd');
      expect(4.ordinal, '4th');
      expect(11.ordinal, '11th');
    });
  });
}
