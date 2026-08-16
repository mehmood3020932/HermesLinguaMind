import 'package:equatable/equatable.dart';

class ChatMessage extends Equatable {
  const ChatMessage({
    required this.id,
    required this.role,
    required this.content,
    required this.timestamp,
    this.audioUrl,
    this.visemeTimeline,
    this.gesture,
    this.coinsAwarded,
  });

  factory ChatMessage.fromJson(final Map<String, dynamic> json) => ChatMessage(
    id: json['id'] as String? ?? '',
    role: MessageRole.values.byName(json['role'] as String? ?? 'user'),
    content: json['content'] as String? ?? '',
    timestamp: json['timestamp'] != null
        ? DateTime.parse(json['timestamp'] as String)
        : DateTime.now(),
    audioUrl: json['audio_url'] as String?,
    visemeTimeline: (json['viseme_timeline'] as List<dynamic>? ?? [])
        .map((final v) => VisemeFrame.fromJson(v as Map<String, dynamic>))
        .toList(),
    gesture: json['gesture'] as String?,
    coinsAwarded: json['coins_awarded'] as int?,
  );

  final String id;
  final MessageRole role;
  final String content;
  final DateTime timestamp;
  final String? audioUrl;
  final List<VisemeFrame>? visemeTimeline;
  final String? gesture;
  final int? coinsAwarded;

  Map<String, dynamic> toJson() => {
    'id': id,
    'role': role.name,
    'content': content,
    'timestamp': timestamp.toIso8601String(),
    'audio_url': audioUrl,
    'viseme_timeline': visemeTimeline?.map((final v) => v.toJson()).toList(),
    'gesture': gesture,
    'coins_awarded': coinsAwarded,
  };

  @override
  List<Object?> get props => [id, role, timestamp];
}

enum MessageRole { user, assistant, system }

class VisemeFrame extends Equatable {
  const VisemeFrame({required this.time, required this.viseme});

  factory VisemeFrame.fromJson(final Map<String, dynamic> json) => VisemeFrame(
    time: (json['time'] as num).toDouble(),
    viseme: json['viseme'] as String? ?? 'sil',
  );
  final double time;
  final String viseme;

  Map<String, dynamic> toJson() => {'time': time, 'viseme': viseme};

  @override
  List<Object?> get props => [time, viseme];
}

class ChatRequest extends Equatable {
  const ChatRequest({
    required this.userId,
    required this.message,
    this.sessionContext,
  });

  final String userId;
  final String message;
  final Map<String, dynamic>? sessionContext;

  Map<String, dynamic> toJson() => {
    'user_id': userId,
    'message': message,
    if (sessionContext != null) 'session_context': sessionContext,
  };

  @override
  List<Object?> get props => [userId, message];
}

class ChatResponse extends Equatable {
  const ChatResponse({
    required this.success,
    required this.requestId,
    this.data,
    this.error,
  });

  factory ChatResponse.fromJson(final Map<String, dynamic> json) =>
      ChatResponse(
        success: json['success'] as bool? ?? false,
        requestId: json['request_id'] as String? ?? '',
        data: json['data'] != null
            ? ChatData.fromJson(json['data'] as Map<String, dynamic>)
            : null,
        error: json['error'] as String?,
      );

  final bool success;
  final String requestId;
  final ChatData? data;
  final String? error;

  @override
  List<Object?> get props => [success, requestId];
}

class ChatData extends Equatable {
  const ChatData({
    required this.text,
    this.audioUrl,
    this.visemeTimeline,
    this.gesture,
    this.coinsAwarded,
  });

  factory ChatData.fromJson(final Map<String, dynamic> json) => ChatData(
    text: json['text'] as String? ?? '',
    audioUrl: json['audio_url'] as String?,
    visemeTimeline: (json['viseme_timeline'] as List<dynamic>? ?? [])
        .map((final v) => VisemeFrame.fromJson(v as Map<String, dynamic>))
        .toList(),
    gesture: json['gesture'] as String?,
    coinsAwarded: json['coins_awarded'] as int?,
  );

  final String text;
  final String? audioUrl;
  final List<VisemeFrame>? visemeTimeline;
  final String? gesture;
  final int? coinsAwarded;

  @override
  List<Object?> get props => [text, audioUrl, gesture];
}

/// Response from the backend's /v1/stt endpoint (speech-to-text).
class SpeechToTextResponse extends Equatable {
  const SpeechToTextResponse({required this.text, this.confidence});

  factory SpeechToTextResponse.fromJson(final Map<String, dynamic> json) =>
      SpeechToTextResponse(
        text: json['text'] as String? ?? '',
        confidence: (json['confidence'] as num?)?.toDouble(),
      );

  final String text;
  final double? confidence;

  @override
  List<Object?> get props => [text, confidence];
}

/// Response from the backend's /v1/tts endpoint (text-to-speech).
/// [audioBytes] is the raw synthesized audio (mp3). [visemeTimeline] gives
/// mouth-shape timing derived from real word-boundary data returned by the
/// TTS engine, used to drive the companion's lip-sync.
class TextToSpeechResult extends Equatable {
  const TextToSpeechResult({
    required this.audioBytes,
    required this.visemeTimeline,
  });

  final List<int> audioBytes;
  final List<VisemeFrame> visemeTimeline;

  @override
  List<Object?> get props => [audioBytes.length, visemeTimeline];
}
