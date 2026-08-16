import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/data/models/avatar_models.dart';

/// Renders the real avatar video stream from OpenTalking. Replaces the
/// deprecated CompanionCharacterWidget (custom-painted 2D character with
/// viseme mouth shapes) — lip-sync, gesture, and emotion now come from
/// the server-rendered video track itself, not client-side animation.
class AvatarVideoWidget extends StatelessWidget {
  const AvatarVideoWidget({
    required this.renderer,
    required this.connectionState,
    this.characterName,
    super.key,
  });

  final RTCVideoRenderer renderer;
  final AvatarConnectionState connectionState;
  final String? characterName;

  @override
  Widget build(final BuildContext context) => ClipRRect(
    borderRadius: BorderRadius.circular(24),
    child: AspectRatio(
      aspectRatio: 3 / 4,
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: AppTheme.surfaceGradient,
          border: Border.all(color: AppTheme.borderGlow, width: 1.5),
        ),
        child: Stack(
          fit: StackFit.expand,
          children: [
            if (connectionState == AvatarConnectionState.connected)
              RTCVideoView(renderer, objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitCover)
            else
              _buildPlaceholder(),
          ],
        ),
      ),
    ),
  );

  Widget _buildPlaceholder() {
    final (icon, label) = switch (connectionState) {
      AvatarConnectionState.idle => (Icons.face_retouching_natural, 'Ready to connect'),
      AvatarConnectionState.creatingSession => (Icons.hourglass_top, 'Starting session…'),
      AvatarConnectionState.connectingWebrtc => (Icons.wifi_tethering, 'Connecting…'),
      AvatarConnectionState.reconnecting => (Icons.sync, 'Reconnecting…'),
      AvatarConnectionState.failed => (Icons.error_outline, "Couldn't connect"),
      AvatarConnectionState.ended => (Icons.stop_circle_outlined, 'Session ended'),
      AvatarConnectionState.connected => (Icons.face, characterName ?? 'Hermes'),
    };

    final isBusy =
        connectionState == AvatarConnectionState.creatingSession ||
        connectionState == AvatarConnectionState.connectingWebrtc ||
        connectionState == AvatarConnectionState.reconnecting;

    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
                icon,
                size: 56,
                color: connectionState == AvatarConnectionState.failed
                    ? AppTheme.error
                    : AppTheme.violetLight,
              )
              .animate(
                onPlay: (final c) => isBusy ? c.repeat() : null,
              )
              .rotate(
                duration: isBusy ? const Duration(seconds: 2) : Duration.zero,
              ),
          const SizedBox(height: 12),
          Text(
            label,
            style: AppTheme.bodyLarge.copyWith(color: AppTheme.textSecondary),
          ),
        ],
      ),
    );
  }
}
