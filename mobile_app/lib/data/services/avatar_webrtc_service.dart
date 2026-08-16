import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:hermes_linguamind/core/constants/app_constants.dart';
import 'package:hermes_linguamind/core/utils/logger.dart';

/// Opens a receive-only WebRTC connection DIRECTLY against OpenTalking's
/// public endpoint (via nginx, see AppConstants.avatarPublicBaseUrl) for
/// this session's rendered avatar video + audio. avatar_service (our own
/// backend) is not in this data path at all — it only issued the session
/// and handed back `webrtcOfferPath` (see avatar_service.py docstring).
///
/// Signaling protocol: a single non-trickle offer/answer HTTP exchange —
/// this client creates a receive-only offer, waits for local ICE
/// gathering to finish, then POSTs the complete SDP offer (as plain
/// `application/sdp` text, the common convention for this kind of
/// single-shot "offer path" API — e.g. WHIP-style ingestion/egress
/// endpoints) and expects the SDP answer back as the response body. If
/// OpenTalking's actual endpoint expects a JSON-wrapped offer instead,
/// only `_postOffer` below needs to change — everything else in this
/// class is protocol-agnostic.
class AvatarWebRTCService {
  RTCPeerConnection? _peerConnection;
  final RTCVideoRenderer remoteRenderer = RTCVideoRenderer();
  final _connectionStateController =
      StreamController<RTCPeerConnectionState>.broadcast();

  Stream<RTCPeerConnectionState> get connectionState =>
      _connectionStateController.stream;

  bool _rendererInitialized = false;

  Future<void> _ensureRenderer() async {
    if (_rendererInitialized) return;
    await remoteRenderer.initialize();
    _rendererInitialized = true;
  }

  /// [webrtcOfferPath] is the relative path returned by avatar_service
  /// (e.g. "/avatar-api/sessions/{id}/webrtc/offer") — resolved against
  /// AppConstants.avatarPublicBaseUrl, not the gateway.
  Future<void> connect(final String webrtcOfferPath) async {
    await _ensureRenderer();
    await disconnect(); // clean up any previous session first

    final configuration = <String, dynamic>{
      'iceServers': [
        {
          'urls': ['stun:stun.l.google.com:19302'],
        },
      ],
      'sdpSemantics': 'unified-plan',
    };

    final pc = await createPeerConnection(configuration);
    _peerConnection = pc;

    pc.onConnectionState = (final state) {
      AppLogger.debug('Avatar WebRTC connection state: $state');
      _connectionStateController.add(state);
    };

    pc.onTrack = (final event) {
      if (event.track.kind == 'video' && event.streams.isNotEmpty) {
        remoteRenderer.srcObject = event.streams.first;
      }
    };

    // Receive-only transceivers — this client never sends its own camera
    // or mic over this connection (voice input goes through the separate
    // REST /audio endpoint, transcribed server-side by our own STT).
    await pc.addTransceiver(
      kind: RTCRtpMediaType.RTCRtpMediaTypeVideo,
      init: RTCRtpTransceiverInit(direction: TransceiverDirection.RecvOnly),
    );
    await pc.addTransceiver(
      kind: RTCRtpMediaType.RTCRtpMediaTypeAudio,
      init: RTCRtpTransceiverInit(direction: TransceiverDirection.RecvOnly),
    );

    final offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    await _waitForIceGatheringComplete(pc);

    final localDesc = await pc.getLocalDescription();
    if (localDesc?.sdp == null) {
      throw StateError('Failed to generate local SDP offer');
    }

    final answerSdp = await _postOffer(webrtcOfferPath, localDesc!.sdp!);
    await pc.setRemoteDescription(RTCSessionDescription(answerSdp, 'answer'));
  }

  Future<void> _waitForIceGatheringComplete(
    final RTCPeerConnection pc, {
    final Duration timeout = const Duration(seconds: 5),
  }) async {
    if (pc.iceGatheringState ==
        RTCIceGatheringState.RTCIceGatheringStateComplete) {
      return;
    }
    final completer = Completer<void>();
    pc.onIceGatheringState = (final state) {
      if (state == RTCIceGatheringState.RTCIceGatheringStateComplete &&
          !completer.isCompleted) {
        completer.complete();
      }
    };
    await completer.future.timeout(
      timeout,
      onTimeout: () {
        // Proceed with whatever candidates gathered so far rather than
        // hanging indefinitely — most STUN-only setups finish well
        // under this window.
        AppLogger.debug('ICE gathering timed out, proceeding anyway');
      },
    );
  }

  final Dio _sdpClient = Dio();

  Future<String> _postOffer(
    final String webrtcOfferPath,
    final String offerSdp,
  ) async {
    final uri = '${AppConstants.avatarPublicBaseUrl}$webrtcOfferPath';
    final response = await _sdpClient.post<dynamic>(
      uri,
      data: offerSdp,
      options: Options(
        contentType: 'application/sdp',
        responseType: ResponseType.plain,
        validateStatus: (final status) => status != null && status < 500,
      ),
    );

    if (response.statusCode != 200 && response.statusCode != 201) {
      throw StateError(
        'Avatar WebRTC offer rejected: HTTP ${response.statusCode}',
      );
    }

    final contentType = response.headers.value('content-type') ?? '';
    final body = response.data;
    if (contentType.contains('application/json') && body is Map) {
      return (body['sdp'] as String?) ?? (body['answer'] as String?) ?? '';
    }
    if (contentType.contains('application/json') && body is String) {
      final decoded = jsonDecode(body) as Map<String, dynamic>;
      return (decoded['sdp'] as String?) ?? (decoded['answer'] as String?) ?? '';
    }
    return body as String;
  }

  Future<void> disconnect() async {
    final pc = _peerConnection;
    _peerConnection = null;
    if (pc != null) {
      await pc.close();
      await pc.dispose();
    }
    remoteRenderer.srcObject = null;
  }

  Future<void> dispose() async {
    await disconnect();
    if (_rendererInitialized) {
      await remoteRenderer.dispose();
      _rendererInitialized = false;
    }
    await _connectionStateController.close();
  }
}
