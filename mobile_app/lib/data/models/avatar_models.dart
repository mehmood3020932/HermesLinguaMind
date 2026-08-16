import 'package:equatable/equatable.dart';

/// Mirrors avatar_service's `POST /v1/sessions` response `data` payload
/// exactly (see backend/phase3/services/avatar_service/main.py,
/// `create_session`). `webrtcOfferPath` and `eventsPath` are relative to
/// AppConstants.avatarPublicBaseUrl, NOT avatarServiceBaseUrl — they are
/// OpenTalking's own paths, proxied by nginx, not by this service.
class AvatarSession extends Equatable {
  const AvatarSession({
    required this.sessionId,
    required this.opentalkingSessionId,
    required this.webrtcOfferPath,
    required this.eventsPath,
    required this.character,
  });

  factory AvatarSession.fromJson(final Map<String, dynamic> json) =>
      AvatarSession(
        sessionId: json['session_id'] as String? ?? '',
        opentalkingSessionId: json['opentalking_session_id'] as String? ?? '',
        webrtcOfferPath: json['webrtc_offer_path'] as String? ?? '',
        eventsPath: json['events_path'] as String? ?? '',
        character: AvatarCharacterInfo.fromJson(
          (json['character'] as Map<String, dynamic>?) ?? const {},
        ),
      );

  final String sessionId;
  final String opentalkingSessionId;
  final String webrtcOfferPath;
  final String eventsPath;
  final AvatarCharacterInfo character;

  @override
  List<Object?> get props => [sessionId, opentalkingSessionId];
}

class AvatarCharacterInfo extends Equatable {
  const AvatarCharacterInfo({
    required this.slug,
    required this.displayName,
    required this.teachingStyle,
  });

  factory AvatarCharacterInfo.fromJson(final Map<String, dynamic> json) =>
      AvatarCharacterInfo(
        slug: json['slug'] as String? ?? '',
        displayName: json['display_name'] as String? ?? '',
        teachingStyle: json['teaching_style'] as String? ?? '',
      );

  final String slug;
  final String displayName;
  final String teachingStyle;

  @override
  List<Object?> get props => [slug];
}

/// Connection lifecycle for the WebRTC link to the avatar's rendered
/// video/audio — distinct from whether a message send/receive is in
/// flight, which is tracked separately in AvatarState.
enum AvatarConnectionState {
  idle,
  creatingSession,
  connectingWebrtc,
  connected,
  reconnecting,
  failed,
  ended,
}

/// Which visual is actually driving the on-screen avatar right now.
/// `realVideo` = OpenTalking's rendered video track over WebRTC (needs
/// real GPU infra + real model weights configured server-side).
/// `animatedFallback` = the self-contained, code-only stylized character
/// (AnimatedAvatarWidget), lip-synced to real TTS phoneme timing from
/// api_gateway's /v1/tts — used automatically whenever realVideo isn't
/// available, so the companion still talks and lip-syncs either way.
enum AvatarRenderMode { realVideo, animatedFallback }
