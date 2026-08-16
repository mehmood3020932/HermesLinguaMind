import 'dart:async';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart' as ap;
import 'package:hermes_linguamind/core/utils/logger.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

/// Real microphone recording + audio playback for the companion feature.
///
/// This talks to actual device hardware (mic + speaker) — it does not
/// simulate anything. Recording is written to a temp .m4a file which is
/// then uploaded to the backend's /v1/stt endpoint. Playback plays audio
/// bytes returned by the backend's /v1/tts endpoint.
class AudioService {
  factory AudioService() => _instance;
  AudioService._();
  static final AudioService _instance = AudioService._();

  final AudioRecorder _recorder = AudioRecorder();
  final ap.AudioPlayer _player = ap.AudioPlayer();

  String? _currentRecordingPath;
  bool _isRecording = false;

  bool get isRecording => _isRecording;

  /// Requests mic permission (via the `record` package) and starts capture.
  /// Throws a [StateError] if permission is denied.
  Future<void> startRecording() async {
    final hasPermission = await _recorder.hasPermission();
    if (!hasPermission) {
      throw StateError('Microphone permission denied.');
    }

    final dir = await getTemporaryDirectory();
    final path =
        '${dir.path}/hermes_recording_${DateTime.now().millisecondsSinceEpoch}.m4a';

    await _recorder.start(
      const RecordConfig(sampleRate: 16000, numChannels: 1),
      path: path,
    );

    _currentRecordingPath = path;
    _isRecording = true;
    AppLogger.debug('AudioService: recording started → $path');
  }

  /// Stops recording and returns the recorded audio file, or null if
  /// nothing was captured (e.g. recording was too short / cancelled).
  Future<File?> stopRecording() async {
    if (!_isRecording) return null;
    final path = await _recorder.stop();
    _isRecording = false;

    final resolvedPath = path ?? _currentRecordingPath;
    _currentRecordingPath = null;

    if (resolvedPath == null) return null;
    final file = File(resolvedPath);
    if (!file.existsSync()) return null;

    final sizeBytes = file.lengthSync();
    // Guard against near-empty captures (e.g. a stray tap).
    if (sizeBytes < 1024) {
      AppLogger.debug(
        'AudioService: recording discarded (too short, $sizeBytes bytes)',
      );
      return null;
    }

    AppLogger.debug(
      'AudioService: recording stopped → $resolvedPath ($sizeBytes bytes)',
    );
    return file;
  }

  Future<void> cancelRecording() async {
    if (!_isRecording) return;
    await _recorder.stop();
    _isRecording = false;
    if (_currentRecordingPath != null) {
      final f = File(_currentRecordingPath!);
      if (f.existsSync()) await f.delete();
    }
    _currentRecordingPath = null;
  }

  /// Plays raw audio bytes returned by the TTS backend.
  /// Returns a future that completes when playback finishes.
  Future<void> playBytes(
    final List<int> bytes, {
    final String format = 'mp3',
  }) async {
    final dir = await getTemporaryDirectory();
    final file = File(
      '${dir.path}/hermes_tts_${DateTime.now().millisecondsSinceEpoch}.$format',
    );
    await file.writeAsBytes(bytes, flush: true);
    await _player.play(ap.DeviceFileSource(file.path));
    final completer = Completer<void>();
    late final StreamSubscription<void> sub;
    sub = _player.onPlayerComplete.listen((_) {
      sub.cancel();
      if (!completer.isCompleted) completer.complete();
    });
    return completer.future;
  }

  Future<void> stopPlayback() => _player.stop();

  void dispose() {
    _recorder.dispose();
    _player.dispose();
  }
}
