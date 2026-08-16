import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hermes_linguamind/core/widgets/animated_counter.dart';

void main() {
  testWidgets('AnimatedCounter displays value', (final tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: Scaffold(body: AnimatedCounter(value: 100))),
    );
    await tester.pumpAndSettle();
    expect(find.text('100'), findsOneWidget);
  });

  testWidgets('RankBadge displays rank', (final tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: Scaffold(body: RankBadge(rank: 1))),
    );
    expect(find.text('1'), findsOneWidget);
  });
}
