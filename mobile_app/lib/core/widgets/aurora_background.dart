import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

/// The Aurora Glass design system's signature visual: a slow, living
/// mesh of blurred gradient blobs that drift and breathe behind the UI.
///
/// Drop this once behind a `Scaffold`'s body (as the bottom layer of a
/// `Stack`) and every screen instantly reads as "alive" instead of a flat
/// dark background — this is intentionally the one visual element every
/// screen in the app shares, so the whole product feels like one place.
///
/// Cheap by design: 3–4 blurred circles animated with a single
/// `AnimationController`, no shaders, no per-frame rebuilds of the rest
/// of the tree (it paints on its own `RepaintBoundary`).
class AuroraBackground extends StatefulWidget {
  const AuroraBackground({
    super.key,
    this.intensity = 1.0,
    this.child,
  });

  /// 0.0 = nearly still & dim, 1.0 = full motion & full glow. Use a lower
  /// value on screens with dense content (e.g. lesson player) so the
  /// background supports rather than competes with foreground text.
  final double intensity;

  final Widget? child;

  @override
  State<AuroraBackground> createState() => _AuroraBackgroundState();
}

class _AuroraBackgroundState extends State<AuroraBackground>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 20),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(final BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        ColoredBox(color: AppTheme.darkBase),
        RepaintBoundary(
          child: AnimatedBuilder(
            animation: _controller,
            builder: (final context, final _) {
              return CustomPaint(
                painter: _AuroraPainter(
                  t: _controller.value,
                  intensity: widget.intensity.clamp(0.0, 1.0),
                ),
              );
            },
          ),
        ),
        if (widget.child != null) widget.child!,
      ],
    );
  }
}

class _AuroraPainter extends CustomPainter {
  _AuroraPainter({required this.t, required this.intensity});

  final double t;
  final double intensity;

  static const List<Color> _blobColors = [
    AppTheme.violet,
    AppTheme.aqua,
    Color(0xFF5B8DEF),
  ];

  @override
  void paint(final Canvas canvas, final Size size) {
    if (intensity <= 0) return;

    final w = size.width;
    final h = size.height;
    final angle = t * 2 * math.pi;

    final blobs = <Offset>[
      Offset(
        w * 0.25 + math.sin(angle) * w * 0.18,
        h * 0.22 + math.cos(angle * 0.8) * h * 0.10,
      ),
      Offset(
        w * 0.78 + math.cos(angle * 0.7) * w * 0.16,
        h * 0.30 + math.sin(angle * 1.1) * h * 0.12,
      ),
      Offset(
        w * 0.50 + math.sin(angle * 0.5 + 1.3) * w * 0.20,
        h * 0.82 + math.cos(angle * 0.6) * h * 0.08,
      ),
    ];

    for (var i = 0; i < blobs.length; i++) {
      final radius = size.shortestSide * 0.42;
      final paint = Paint()
        ..shader = RadialGradient(
          colors: [
            _blobColors[i].withValues(alpha: 0.32 * intensity),
            _blobColors[i].withValues(alpha: 0.0),
          ],
        ).createShader(
          Rect.fromCircle(center: blobs[i], radius: radius),
        )
        ..maskFilter = MaskFilter.blur(BlurStyle.normal, radius * 0.35);

      canvas.drawCircle(blobs[i], radius, paint);
    }
  }

  @override
  bool shouldRepaint(covariant final _AuroraPainter oldDelegate) =>
      oldDelegate.t != t || oldDelegate.intensity != intensity;
}
