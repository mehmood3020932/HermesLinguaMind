import 'package:flutter_test/flutter_test.dart';
import 'package:hermes_linguamind/features/auth/providers/auth_provider.dart';

void main() {
  group('AuthNotifier', () {
    test('initial state is unauthenticated', () {
      final notifier = AuthNotifier();
      final state = notifier.state;
      expect(state.value?.isAuthenticated, false);
      expect(state.value?.user, null);
    });
  });
}
