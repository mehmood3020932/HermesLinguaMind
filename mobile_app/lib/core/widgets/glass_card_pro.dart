import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

/// A richer sibling of [GlassCard] with a slowly rotating gradient
/// border — reserve for "hero" cards (featured lesson, streak card,
/// companion highlight) rather than every card on a list, where the
/// plain [GlassCard] remains the right, quieter choice.
class GlassCardPro extends StatefulWidget {
  const GlassCardPro({
    required this.child,
    super.key,
    this.padding,
    this.borderRadius = 20,
    this.animate = true,
  });

  final Widget child;
  final EdgeInsetsGeometry? padding;
  final double borderRadius;

  /// Set false to render a static (non-rotating) border — e.g. for
  /// screens with `prefers-reduced-motion`-style accessibility needs.
  final bool animate;

  @override
  State<GlassCardPro> createState() => _GlassCardProState();
}

class _GlassCardProState extends State<GlassCardPro>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 6),
    );
    if (widget.animate) {
      _controller.repeat();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(final BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (final context, final _) {
        return CustomPaint(
          painter: _RotatingBorderPainter(
            angle: _controller.value * 2 * math.pi,
            radius: widget.borderRadius,
          ),
          child: Container(
            margin: const EdgeInsets.all(1.5),
            padding: widget.padding ?? const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: AppTheme.darkSurface.withValues(alpha: 0.92),
              borderRadius: BorderRadius.circular(widget.borderRadius - 1.5),
            ),
            child: widget.child,
          ),
        );
      },
    );
  }
}

class _RotatingBorderPainter extends CustomPainter {
  _RotatingBorderPainter({required this.angle, required this.radius});

  final double angle;
  final double radius;

  @override
  void paint(final Canvas canvas, final Size size) {
    final rect = Offset.zero & size;
    final rrect = RRect.fromRectAndRadius(rect, Radius.circular(radius));

    final gradient = SweepGradient(
      transform: GradientRotation(angle),
      colors: const [
        AppTheme.violet,
        AppTheme.aqua,
        AppTheme.violet,
      ],
      stops: const [0.0, 0.5, 1.0],
    );

    final paint = Paint()
      ..shader = gradient.createShader(rect)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    canvas.drawRRect(rrect, paint);
  }

  @override
  bool shouldRepaint(covariant final _RotatingBorderPainter oldDelegate) =>
      oldDelegate.angle != angle;
}
