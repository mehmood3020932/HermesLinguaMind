import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:hermes_linguamind/data/models/avatar_models.dart';
import 'package:hermes_linguamind/features/companion/widgets/avatar_video_widget.dart';

void main() {
  testWidgets('AvatarVideoWidget shows a connecting placeholder before the '
      'video track arrives', (final tester) async {
    final renderer = RTCVideoRenderer();
    await renderer.initialize();
    addTearDown(renderer.dispose);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AvatarVideoWidget(
            renderer: renderer,
            connectionState: AvatarConnectionState.connectingWebrtc,
            characterName: 'Hermes',
          ),
        ),
      ),
    );

    expect(find.text('Connecting…'), findsOneWidget);
    expect(find.byType(RTCVideoView), findsNothing);
  });

  testWidgets('AvatarVideoWidget renders the video view once connected', (
    final tester,
  ) async {
    final renderer = RTCVideoRenderer();
    await renderer.initialize();
    addTearDown(renderer.dispose);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AvatarVideoWidget(
            renderer: renderer,
            connectionState: AvatarConnectionState.connected,
            characterName: 'Hermes',
          ),
        ),
      ),
    );

    expect(find.byType(RTCVideoView), findsOneWidget);
  });
}
