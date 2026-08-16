import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:hermes_linguamind/core/constants/api_endpoints.dart';
import 'package:hermes_linguamind/core/utils/logger.dart';
import 'package:hermes_linguamind/data/adapters/api_client.dart';
import 'package:hermes_linguamind/data/models/chat_models.dart';

class TranscriptionResult {
  const TranscriptionResult({required this.text, this.confidence});
  final String text;
  final double? confidence;
}

class SynthesisResult {
  const SynthesisResult({required this.audioBytes, required this.visemeTimeline});
  final List<int> audioBytes;
  final List<VisemeFrame> visemeTimeline;
}

/// STT (`/v1/stt`) + TTS (`/v1/tts`) via api_gateway — the real, verified
/// contract in backend/phase3/services/api_gateway/main.py's
/// `mobile_stt`/`mobile_tts` bridge endpoints. This is the fallback
/// speech path used when the real-avatar WebRTC connection (OpenTalking)
/// isn't available — see avatar_provider.dart's `_fallbackToAnimated`.
class VoiceAdapter {
  factory VoiceAdapter() => _instance;
  VoiceAdapter._();
  static final VoiceAdapter _instance = VoiceAdapter._();

  final ApiClient _client = ApiClient();

  Future<TranscriptionResult> transcribe(final File audioFile) async {
    try {
      final formData = FormData.fromMap({
        'audio': await MultipartFile.fromFile(audioFile.path),
      });
      final response = await _client.post<Map<String, dynamic>>(
        ApiEndpoints.speechToText,
        data: formData,
      );
      final data = response.data ?? const {};
      return TranscriptionResult(
        text: data['text'] as String? ?? '',
        confidence: (data['confidence'] as num?)?.toDouble(),
      );
    } on DioException catch (e) {
      AppLogger.error('STT transcribe failed', e);
      throw Exception('Transcription failed. Please try again.');
    }
  }

  Future<SynthesisResult> synthesize(
    final String text, {
    final String voice = 'en-US-AriaNeural',
  }) async {
    try {
      final response = await _client.post<Map<String, dynamic>>(
        ApiEndpoints.textToSpeech,
        data: {'text': text, 'voice': voice},
      );
      final data = response.data ?? const {};
      final audioB64 = data['audio_base64'] as String? ?? '';
      final timeline = (data['viseme_timeline'] as List<dynamic>? ?? [])
          .map((final v) => VisemeFrame.fromJson(v as Map<String, dynamic>))
          .toList();
      return SynthesisResult(
        audioBytes: audioB64.isEmpty ? const [] : base64Decode(audioB64),
        visemeTimeline: timeline,
      );
    } on DioException catch (e) {
      AppLogger.error('TTS synthesize failed', e);
      throw Exception('Voice synthesis failed.');
    }
  }
}
