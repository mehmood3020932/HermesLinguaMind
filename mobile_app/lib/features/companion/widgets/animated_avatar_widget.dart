import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

/// A stylized, fully self-contained animated character — NOT a
/// photorealistic human. This is the honest fallback for when the real
/// OpenTalking video avatar isn't connected (no GPU infra / real model
/// weights configured, or the WebRTC link failed) — see
/// AvatarNotifier._fallbackToAnimated in avatar_provider.dart. Its lip
/// sync is real: [viseme] is driven by the actual phoneme-timing data
/// api_gateway's /v1/tts returns from the real Piper TTS synthesis, not
/// a canned animation loop.
class AnimatedAvatarWidget extends StatefulWidget {
  const AnimatedAvatarWidget({
    required this.viseme,
    required this.emotion,
    required this.isListening,
    required this.isSpeaking,
    super.key,
  });

  final String viseme;
  final String emotion;
  final bool isListening;
  final bool isSpeaking;

  @override
  State<AnimatedAvatarWidget> createState() => _AnimatedAvatarWidgetState();
}

class _AnimatedAvatarWidgetState extends State<AnimatedAvatarWidget>
    with TickerProviderStateMixin {
  late final AnimationController _idleController;
  late final AnimationController _blinkController;

  @override
  void initState() {
    super.initState();
    _idleController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 4),
    )..repeat(reverse: true);

    _blinkController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 140),
    );
    _scheduleNextBlink();
  }

  void _scheduleNextBlink() {
    final delay = Duration(milliseconds: 2200 + math.Random().nextInt(2600));
    Future.delayed(delay, () async {
      if (!mounted) return;
      await _blinkController.forward();
      if (!mounted) return;
      await _blinkController.reverse();
      _scheduleNextBlink();
    });
  }

  @override
  void dispose() {
    _idleController.dispose();
    _blinkController.dispose();
    super.dispose();
  }

  @override
  Widget build(final BuildContext context) => AnimatedBuilder(
    animation: Listenable.merge([_idleController, _blinkController]),
    builder: (final context, final _) => CustomPaint(
      painter: _AvatarPainter(
        viseme: widget.viseme,
        emotion: widget.emotion,
        isListening: widget.isListening,
        isSpeaking: widget.isSpeaking,
        idleT: _idleController.value,
        blinkT: _blinkController.value,
      ),
      size: Size.infinite,
    ),
  );
}

class _AvatarPainter extends CustomPainter {
  _AvatarPainter({
    required this.viseme,
    required this.emotion,
    required this.isListening,
    required this.isSpeaking,
    required this.idleT,
    required this.blinkT,
  });

  final String viseme;
  final String emotion;
  final bool isListening;
  final bool isSpeaking;
  final double idleT; // 0..1..0, breathing/bob cycle
  final double blinkT; // 0..1, eyelid closed fraction

  // Mouth openness per viseme code (matches the phoneme_timings the real
  // Piper-driven TTS pipeline emits: sil, aa, ee, oh, ff, mm, ...).
  static const Map<String, double> _mouthOpenness = {
    'sil': 0.06,
    'aa': 0.85,
    'ee': 0.35,
    'oh': 0.65,
    'oo': 0.4,
    'ff': 0.2,
    'mm': 0.05,
    'th': 0.25,
    'l': 0.3,
    'r': 0.4,
  };

  static const Map<String, double> _mouthWidth = {
    'sil': 0.55,
    'aa': 0.5,
    'ee': 0.85,
    'oh': 0.45,
    'oo': 0.35,
    'ff': 0.6,
    'mm': 0.55,
    'th': 0.6,
    'l': 0.55,
    'r': 0.5,
  };

  @override
  void paint(final Canvas canvas, final Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) / 2 * 0.62;
    final bob = math.sin(idleT * math.pi) * radius * 0.015;
    final faceCenter = center.translate(0, bob);

    final accent = _emotionAccent();

    // Glow ring — pulses gently while listening/speaking.
    if (isListening || isSpeaking) {
      final pulse = 1.0 + math.sin(idleT * math.pi * 2) * 0.03;
      final glowPaint = Paint()
        ..color = accent.withValues(alpha: 0.18)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 10;
      canvas.drawCircle(faceCenter, radius * 1.14 * pulse, glowPaint);
    }

    // Face base.
    final facePaint = Paint()..color = AppTheme.darkSurface;
    canvas.drawCircle(faceCenter, radius, facePaint);
    final faceBorder = Paint()
      ..color = accent.withValues(alpha: 0.55)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    canvas.drawCircle(faceCenter, radius, faceBorder);

    _paintEyes(canvas, faceCenter, radius, accent);
    _paintBrows(canvas, faceCenter, radius, accent);
    _paintMouth(canvas, faceCenter, radius, accent);
  }

  Color _emotionAccent() {
    switch (emotion.toUpperCase()) {
      case 'HAPPY':
      case 'ENCOURAGING':
        return AppTheme.aqua;
      case 'CONCERNED':
      case 'THINKING':
        return AppTheme.violetLight;
      default:
        return AppTheme.violet;
    }
  }

  void _paintEyes(
    final Canvas canvas,
    final Offset center,
    final double radius,
    final Color accent,
  ) {
    final eyeY = center.dy - radius * 0.15;
    final eyeDx = radius * 0.32;
    final eyeOpenH = radius * 0.16 * (1 - blinkT * 0.92);
    final eyeW = radius * 0.14;

    for (final side in [-1, 1]) {
      final eyeCenter = Offset(center.dx + eyeDx * side, eyeY);
      final rect = Rect.fromCenter(
        center: eyeCenter,
        width: eyeW,
        height: math.max(eyeOpenH, 1.5),
      );
      canvas.drawRRect(
        RRect.fromRectAndRadius(rect, Radius.circular(eyeW / 2)),
        Paint()..color = accent.withValues(alpha: 0.95),
      );
    }
  }

  void _paintBrows(
    final Canvas canvas,
    final Offset center,
    final double radius,
    final Color accent,
  ) {
    final browY = center.dy - radius * 0.34;
    final browTilt = emotion.toUpperCase() == 'CONCERNED' ? 0.18 : 0.0;
    final browPaint = Paint()
      ..color = AppTheme.textSecondary
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;

    for (final side in [-1, 1]) {
      final dx = radius * 0.32 * side;
      final start = Offset(center.dx + dx - radius * 0.09, browY + browTilt * radius * side.sign * -1);
      final end = Offset(center.dx + dx + radius * 0.09, browY - browTilt * radius * side.sign * -1);
      canvas.drawLine(start, end, browPaint);
    }
  }

  void _paintMouth(
    final Canvas canvas,
    final Offset center,
    final double radius,
    final Color accent,
  ) {
    final openness = _mouthOpenness[viseme] ?? _mouthOpenness['sil']!;
    final width = _mouthWidth[viseme] ?? _mouthWidth['sil']!;

    final mouthY = center.dy + radius * 0.38;
    final mouthW = radius * width;
    final mouthH = radius * openness * 0.6;

    final rect = Rect.fromCenter(
      center: Offset(center.dx, mouthY),
      width: mouthW,
      height: math.max(mouthH, radius * 0.04),
    );

    canvas.drawRRect(
      RRect.fromRectAndRadius(rect, Radius.circular(mouthH / 2 + 2)),
      Paint()..color = accent,
    );
  }

  @override
  bool shouldRepaint(covariant final _AvatarPainter oldDelegate) =>
      oldDelegate.viseme != viseme ||
      oldDelegate.emotion != emotion ||
      oldDelegate.isListening != isListening ||
      oldDelegate.isSpeaking != isSpeaking ||
      oldDelegate.idleT != idleT ||
      oldDelegate.blinkT != blinkT;
}
