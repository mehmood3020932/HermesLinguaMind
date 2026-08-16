import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

/// A progress indicator that fills like liquid with a gently animated
/// wave surface — used for XP bars, lesson progress, and daily-goal
/// rings where a flat rectangle would feel lifeless.
class LiquidProgressBar extends StatefulWidget {
  const LiquidProgressBar({
    required this.progress,
    super.key,
    this.height = 16,
    this.borderRadius = 12,
    this.fillColor = AppTheme.aqua,
    this.trackColor = AppTheme.darkSurface,
  });

  /// 0.0 – 1.0
  final double progress;
  final double height;
  final double borderRadius;
  final Color fillColor;
  final Color trackColor;

  @override
  State<LiquidProgressBar> createState() => _LiquidProgressBarState();
}

class _LiquidProgressBarState extends State<LiquidProgressBar>
    with SingleTickerProviderStateMixin {
  late final AnimationController _waveController;
  late double _animatedProgress;

  @override
  void initState() {
    super.initState();
    _animatedProgress = widget.progress.clamp(0.0, 1.0);
    _waveController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();
  }

  @override
  void didUpdateWidget(covariant final LiquidProgressBar oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.progress != widget.progress) {
      _animatedProgress = widget.progress.clamp(0.0, 1.0);
    }
  }

  @override
  void dispose() {
    _waveController.dispose();
    super.dispose();
  }

  @override
  Widget build(final BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(widget.borderRadius),
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: 0, end: _animatedProgress),
        duration: const Duration(milliseconds: 700),
        curve: Curves.easeOutCubic,
        builder: (final context, final value, final _) {
          return AnimatedBuilder(
            animation: _waveController,
            builder: (final context, final _) {
              return CustomPaint(
                size: Size(double.infinity, widget.height),
                painter: _LiquidPainter(
                  progress: value,
                  wavePhase: _waveController.value * 2 * math.pi,
                  fillColor: widget.fillColor,
                  trackColor: widget.trackColor,
                ),
              );
            },
          );
        },
      ),
    );
  }
}

class _LiquidPainter extends CustomPainter {
  _LiquidPainter({
    required this.progress,
    required this.wavePhase,
    required this.fillColor,
    required this.trackColor,
  });

  final double progress;
  final double wavePhase;
  final Color fillColor;
  final Color trackColor;

  @override
  void paint(final Canvas canvas, final Size size) {
    canvas.drawRect(Offset.zero & size, Paint()..color = trackColor);

    if (progress <= 0) return;

    final fillWidth = size.width * progress;
    final waveAmplitude = size.height * 0.12;
    final path = Path()..moveTo(0, size.height);

    const steps = 24;
    for (var i = 0; i <= steps; i++) {
      final x = fillWidth * (i / steps);
      final y =
          size.height * 0.5 +
          math.sin((i / steps) * 4 * math.pi + wavePhase) * waveAmplitude;
      path.lineTo(x, y);
    }
    path
      ..lineTo(fillWidth, size.height)
      ..close();

    final paint = Paint()
      ..shader = LinearGradient(
        colors: [fillColor.withValues(alpha: 0.85), fillColor],
      ).createShader(Rect.fromLTWH(0, 0, fillWidth, size.height));

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant final _LiquidPainter oldDelegate) =>
      oldDelegate.progress != progress || oldDelegate.wavePhase != wavePhase;
}
