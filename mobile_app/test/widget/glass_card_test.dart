import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hermes_linguamind/core/widgets/glass_card.dart';

void main() {
  testWidgets('GlassCard renders child', (final tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: GlassCard(child: Text('Test Content'))),
      ),
    );
    expect(find.text('Test Content'), findsOneWidget);
  });

  testWidgets('GlassCard onTap works', (final tester) async {
    bool tapped = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: GlassCard(
            onTap: () => tapped = true,
            child: const Text('Tap Me'),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Tap Me'));
    expect(tapped, true);
  });
}
