import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

/// A short-lived burst of gradient particles radiating outward — fires
/// once and disposes itself. Use for genuine reward moments (streak
/// saved, lesson perfect score, level up), never for routine taps.
///
/// ```dart
/// ParticleBurst.fire(context, center: tapPosition);
/// ```
class ParticleBurst extends StatefulWidget {
  const ParticleBurst({
    required this.center,
    super.key,
    this.particleCount = 24,
    this.colors = const [
      AppTheme.violet,
      AppTheme.aqua,
      AppTheme.warning,
    ],
    this.onComplete,
  });

  final Offset center;
  final int particleCount;
  final List<Color> colors;
  final VoidCallback? onComplete;

  /// Convenience: insert a self-removing burst into the nearest
  /// [Overlay] centered at [center].
  static void fire(
    final BuildContext context, {
    required final Offset center,
    int particleCount = 24,
  }) {
    final overlay = Overlay.of(context);
    late final OverlayEntry entry;
    entry = OverlayEntry(
      builder: (final context) => ParticleBurst(
        center: center,
        particleCount: particleCount,
        onComplete: () => entry.remove(),
      ),
    );
    overlay.insert(entry);
  }

  @override
  State<ParticleBurst> createState() => _ParticleBurstState();
}

class _ParticleBurstState extends State<ParticleBurst>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final List<_Particle> _particles;

  @override
  void initState() {
    super.initState();
    final random = math.Random();
    _particles = List.generate(widget.particleCount, (final i) {
      final angle = random.nextDouble() * 2 * math.pi;
      final speed = 80 + random.nextDouble() * 140;
      return _Particle(
        velocity: Offset(math.cos(angle), math.sin(angle)) * speed,
        color: widget.colors[i % widget.colors.length],
        size: 3 + random.nextDouble() * 5,
      );
    });

    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..forward();

    _controller.addStatusListener((final status) {
      if (status == AnimationStatus.completed) {
        widget.onComplete?.call();
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(final BuildContext context) {
    return IgnorePointer(
      child: AnimatedBuilder(
        animation: _controller,
        builder: (final context, final _) {
          return CustomPaint(
            size: Size.infinite,
            painter: _ParticlePainter(
              center: widget.center,
              particles: _particles,
              t: _controller.value,
            ),
          );
        },
      ),
    );
  }
}

class _Particle {
  _Particle({required this.velocity, required this.color, required this.size});

  final Offset velocity;
  final Color color;
  final double size;
}

class _ParticlePainter extends CustomPainter {
  _ParticlePainter({
    required this.center,
    required this.particles,
    required this.t,
  });

  final Offset center;
  final List<_Particle> particles;
  final double t;

  @override
  void paint(final Canvas canvas, final Size size) {
    final eased = Curves.easeOutCubic.transform(t);
    final fade = (1 - t).clamp(0.0, 1.0);

    for (final p in particles) {
      final position = center + p.velocity * eased;
      final paint = Paint()
        ..color = p.color.withValues(alpha: fade)
        ..style = PaintingStyle.fill;
      canvas.drawCircle(position, p.size * fade.clamp(0.3, 1.0), paint);
    }
  }

  @override
  bool shouldRepaint(covariant final _ParticlePainter oldDelegate) =>
      oldDelegate.t != t;
}
