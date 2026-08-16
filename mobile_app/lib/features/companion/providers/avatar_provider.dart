import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart' show RTCPeerConnectionState;
import 'package:hermes_linguamind/core/utils/logger.dart';
import 'package:hermes_linguamind/data/adapters/avatar_adapter.dart';
import 'package:hermes_linguamind/data/adapters/chat_adapter.dart';
import 'package:hermes_linguamind/data/adapters/voice_adapter.dart';
import 'package:hermes_linguamind/data/models/avatar_models.dart';
import 'package:hermes_linguamind/data/models/chat_models.dart';
import 'package:hermes_linguamind/data/services/audio_service.dart';
import 'package:hermes_linguamind/data/services/avatar_webrtc_service.dart';

class AvatarTranscriptEntry {
  const AvatarTranscriptEntry({
    required this.isUser,
    required this.text,
    required this.timestamp,
  });
  final bool isUser;
  final String text;
  final DateTime timestamp;
}

class AvatarState {
  const AvatarState({
    this.connectionState = AvatarConnectionState.idle,
    this.renderMode = AvatarRenderMode.realVideo,
    this.session,
    this.transcript = const [],
    this.isListening = false,
    this.isSending = false,
    this.currentViseme = 'sil',
    this.currentEmotion = 'NEUTRAL',
    this.isSpeaking = false,
    this.error,
  });

  final AvatarConnectionState connectionState;
  final AvatarRenderMode renderMode;
  final AvatarSession? session;
  final List<AvatarTranscriptEntry> transcript;
  final bool isListening;
  final bool isSending;
  final String currentViseme;
  final String currentEmotion;
  final bool isSpeaking;
  final String? error;

  AvatarState copyWith({
    final AvatarConnectionState? connectionState,
    final AvatarRenderMode? renderMode,
    final AvatarSession? session,
    final List<AvatarTranscriptEntry>? transcript,
    final bool? isListening,
    final bool? isSending,
    final String? currentViseme,
    final String? currentEmotion,
    final bool? isSpeaking,
    final String? error,
    final bool clearError = false,
  }) => AvatarState(
    connectionState: connectionState ?? this.connectionState,
    renderMode: renderMode ?? this.renderMode,
    session: session ?? this.session,
    transcript: transcript ?? this.transcript,
    isListening: isListening ?? this.isListening,
    isSending: isSending ?? this.isSending,
    currentViseme: currentViseme ?? this.currentViseme,
    currentEmotion: currentEmotion ?? this.currentEmotion,
    isSpeaking: isSpeaking ?? this.isSpeaking,
    error: clearError ? null : (error ?? this.error),
  );
}

/// Drives the avatar. Tries the real OpenTalking WebRTC video first; if
/// it doesn't come up within [_webrtcConnectTimeout] (no GPU/model
/// configured server-side, or the link fails), automatically switches to
/// [AvatarRenderMode.animatedFallback] — a self-contained stylized
/// character lip-synced to real TTS phoneme timing via VoiceAdapter, so
/// the companion still talks with real audio and real lip movement
/// either way, rather than leaving the user looking at a dead screen.
class AvatarNotifier extends StateNotifier<AvatarState> {
  AvatarNotifier({
    final AvatarAdapter? adapter,
    final AvatarWebRTCService? webrtc,
    final AudioService? audioService,
    final ChatAdapter? chatAdapter,
    final VoiceAdapter? voiceAdapter,
  }) : _adapter = adapter ?? AvatarAdapter(),
       _webrtc = webrtc ?? AvatarWebRTCService(),
       _audio = audioService ?? AudioService(),
       _chatAdapter = chatAdapter ?? ChatAdapter(),
       _voiceAdapter = voiceAdapter ?? VoiceAdapter(),
       super(const AvatarState()) {
    _webrtc.connectionState.listen(_onWebrtcStateChanged);
  }

  static const _webrtcConnectTimeout = Duration(seconds: 6);

  final AvatarAdapter _adapter;
  final AvatarWebRTCService _webrtc;
  final AudioService _audio;
  final ChatAdapter _chatAdapter;
  final VoiceAdapter _voiceAdapter;

  Timer? _visemeTimer;
  Completer<void>? _webrtcConnectedCompleter;
  String? _userId;
  Map<String, dynamic>? _sessionContext;

  AvatarWebRTCService get webrtcService => _webrtc;

  void _onWebrtcStateChanged(final RTCPeerConnectionState rtcState) {
    switch (rtcState) {
      case RTCPeerConnectionState.RTCPeerConnectionStateConnected:
        state = state.copyWith(
          connectionState: AvatarConnectionState.connected,
          renderMode: AvatarRenderMode.realVideo,
        );
        _webrtcConnectedCompleter?.complete();
      case RTCPeerConnectionState.RTCPeerConnectionStateDisconnected:
        if (state.renderMode == AvatarRenderMode.realVideo) {
          state = state.copyWith(
            connectionState: AvatarConnectionState.reconnecting,
          );
        }
      case RTCPeerConnectionState.RTCPeerConnectionStateFailed:
      case RTCPeerConnectionState.RTCPeerConnectionStateClosed:
        if (!(_webrtcConnectedCompleter?.isCompleted ?? true)) {
          _webrtcConnectedCompleter?.complete();
        }
        if (state.renderMode == AvatarRenderMode.realVideo) {
          _fallbackToAnimated('Video connection lost');
        }
      default:
        break;
    }
  }

  /// Starts a session with [characterSlug] and attempts the real video
  /// call; falls back to the animated lip-synced character automatically
  /// if that doesn't come up in time.
  Future<void> startSession(
    final String characterSlug, {
    required final String userId,
    final Map<String, dynamic>? sessionContext,
  }) async {
    _userId = userId;
    _sessionContext = sessionContext;

    state = state.copyWith(
      connectionState: AvatarConnectionState.creatingSession,
      renderMode: AvatarRenderMode.realVideo,
      clearError: true,
    );
    try {
      final session = await _adapter.createSession(characterSlug);
      state = state.copyWith(
        session: session,
        connectionState: AvatarConnectionState.connectingWebrtc,
      );

      _webrtcConnectedCompleter = Completer<void>();
      unawaited(_webrtc.connect(session.webrtcOfferPath));
      await _webrtcConnectedCompleter!.future.timeout(
        _webrtcConnectTimeout,
        onTimeout: () {
          AppLogger.debug(
            'Real-avatar video did not connect within '
            '${_webrtcConnectTimeout.inSeconds}s — falling back to the '
            'animated character.',
          );
        },
      );

      if (state.connectionState != AvatarConnectionState.connected) {
        _fallbackToAnimated(
          "Couldn't reach the real-avatar video service",
        );
      }
    } on Exception catch (e) {
      AppLogger.error('Avatar session start failed', e);
      _fallbackToAnimated('Avatar session unavailable: $e');
    }
  }

  void _fallbackToAnimated(final String reason) {
    AppLogger.debug('Avatar falling back to animated mode: $reason');
    unawaited(_webrtc.disconnect());
    state = state.copyWith(
      renderMode: AvatarRenderMode.animatedFallback,
      connectionState: AvatarConnectionState.connected,
      currentViseme: 'sil',
      // Not surfaced as a blocking `error` banner — the animated
      // fallback IS a working companion, not a failure state the user
      // needs to dismiss or retry.
    );
  }

  Future<void> sendTextMessage(final String text) async {
    if (text.trim().isEmpty) return;

    state = state.copyWith(
      isSending: true,
      transcript: [
        ...state.transcript,
        AvatarTranscriptEntry(
          isUser: true,
          text: text,
          timestamp: DateTime.now(),
        ),
      ],
    );

    if (state.renderMode == AvatarRenderMode.realVideo) {
      await _sendViaRealAvatar(text);
    } else {
      await _sendViaAnimatedFallback(text);
    }
  }

  Future<void> _sendViaRealAvatar(final String text) async {
    final session = state.session;
    if (session == null) return;
    try {
      await _adapter.sendMessage(session.sessionId, text);
      // The spoken reply streams straight into the already-open WebRTC
      // track — nothing to append to the transcript here yet (would need
      // OpenTalking's events_path SSE stream wired up for captions).
      state = state.copyWith(isSending: false);
    } on Exception catch (e) {
      AppLogger.error('Avatar sendMessage failed', e);
      state = state.copyWith(isSending: false, error: e.toString());
    }
  }

  Future<void> _sendViaAnimatedFallback(final String text) async {
    try {
      final response = await _chatAdapter.sendMessage(
        ChatRequest(
          userId: _userId ?? 'guest',
          message: text,
          sessionContext: _sessionContext,
        ),
      );

      if (!response.success || response.data == null) {
        state = state.copyWith(
          isSending: false,
          error: response.error ?? 'Failed to get a reply',
        );
        return;
      }

      final reply = response.data!;
      state = state.copyWith(
        isSending: false,
        currentEmotion: reply.gesture ?? 'NEUTRAL',
        transcript: [
          ...state.transcript,
          AvatarTranscriptEntry(
            isUser: false,
            text: reply.text,
            timestamp: DateTime.now(),
          ),
        ],
      );

      final tts = await _voiceAdapter.synthesize(reply.text);
      _speak(tts.visemeTimeline, audioBytes: tts.audioBytes);
    } on Exception catch (e) {
      AppLogger.error('Animated fallback reply failed', e);
      state = state.copyWith(isSending: false, error: e.toString());
    }
  }

  /// Plays the reply audio and animates [AvatarState.currentViseme] in
  /// real time against the phoneme-timing timeline the real TTS engine
  /// returned — this is genuine lip sync, not a looping placeholder.
  void _speak(final List<VisemeFrame> timeline, {required final List<int> audioBytes}) {
    _visemeTimer?.cancel();
    state = state.copyWith(isSpeaking: true);

    if (audioBytes.isNotEmpty) {
      unawaited(_audio.playBytes(audioBytes));
    }

    if (timeline.isEmpty) {
      state = state.copyWith(isSpeaking: false, currentViseme: 'sil');
      return;
    }

    final stopwatch = Stopwatch()..start();
    var index = 0;

    void tick(final Timer timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      final elapsed = stopwatch.elapsedMilliseconds / 1000.0;
      while (index < timeline.length && timeline[index].time <= elapsed) {
        state = state.copyWith(currentViseme: timeline[index].viseme);
        index++;
      }
      if (index >= timeline.length) {
        timer.cancel();
        stopwatch.stop();
        state = state.copyWith(isSpeaking: false, currentViseme: 'sil');
      }
    }

    _visemeTimer = Timer.periodic(const Duration(milliseconds: 40), tick);
  }

  Future<void> startVoiceCapture() async {
    try {
      await _audio.startRecording();
      state = state.copyWith(isListening: true, clearError: true);
    } on Exception catch (e) {
      state = state.copyWith(isListening: false, error: 'Mic error: $e');
    }
  }

  Future<void> stopVoiceCaptureAndSend() async {
    state = state.copyWith(isListening: false);
    final file = await _audio.stopRecording();
    if (file == null) return;

    if (state.renderMode == AvatarRenderMode.realVideo) {
      final session = state.session;
      if (session == null) return;
      state = state.copyWith(isSending: true);
      try {
        await _adapter.sendAudio(session.sessionId, file);
        state = state.copyWith(isSending: false);
      } on Exception catch (e) {
        AppLogger.error('Avatar sendAudio failed', e);
        state = state.copyWith(isSending: false, error: e.toString());
      }
      return;
    }

    state = state.copyWith(isSending: true);
    try {
      final stt = await _voiceAdapter.transcribe(file);
      if (stt.text.trim().isEmpty) {
        state = state.copyWith(
          isSending: false,
          error: "Didn't catch that — try again?",
        );
        return;
      }
      await sendTextMessage(stt.text);
    } on Exception catch (e) {
      state = state.copyWith(isSending: false, error: e.toString());
    }
  }

  Future<void> cancelVoiceCapture() async {
    await _audio.cancelRecording();
    state = state.copyWith(isListening: false);
  }

  /// Barge-in — cancels whatever the avatar is currently saying.
  Future<void> interrupt() async {
    if (state.renderMode == AvatarRenderMode.realVideo) {
      final session = state.session;
      if (session != null) {
        await _adapter.interrupt(session.sessionId);
      }
    } else {
      _visemeTimer?.cancel();
      await _audio.stopPlayback();
      state = state.copyWith(isSpeaking: false, currentViseme: 'sil');
    }
  }

  Future<void> endSession() async {
    final session = state.session;
    _visemeTimer?.cancel();
    await _audio.stopPlayback();
    await _webrtc.disconnect();
    if (session != null) {
      await _adapter.endSession(session.sessionId);
    }
    state = const AvatarState();
  }

  void clearError() {
    state = state.copyWith(clearError: true);
  }

  @override
  void dispose() {
    _visemeTimer?.cancel();
    unawaited(_webrtc.dispose());
    super.dispose();
  }
}

final avatarProvider = StateNotifierProvider<AvatarNotifier, AvatarState>((
  final ref,
) {
  final notifier = AvatarNotifier();
  ref.onDispose(notifier.dispose);
  return notifier;
});
