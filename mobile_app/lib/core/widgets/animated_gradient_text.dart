import 'package:flutter/material.dart';
import 'package:hermes_linguamind/core/theme/app_motion.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

/// Text whose gradient fill slowly sweeps left-to-right on a loop —
/// use sparingly, for hero moments only (streak milestones, level-up
/// headlines, the companion's name on first meet). Not for body text.
class AnimatedGradientText extends StatefulWidget {
  const AnimatedGradientText(
    this.text, {
    super.key,
    this.style,
    this.colors = const [AppTheme.violet, AppTheme.aqua, AppTheme.violet],
    this.duration = AppMotion.ambient,
    this.textAlign,
  });

  final String text;
  final TextStyle? style;
  final List<Color> colors;
  final Duration duration;
  final TextAlign? textAlign;

  @override
  State<AnimatedGradientText> createState() => _AnimatedGradientTextState();
}

class _AnimatedGradientTextState extends State<AnimatedGradientText>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: widget.duration)
      ..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(final BuildContext context) {
    final baseStyle = widget.style ?? AppTheme.headlineLarge;

    return AnimatedBuilder(
      animation: _controller,
      builder: (final context, final _) {
        return ShaderMask(
          blendMode: BlendMode.srcIn,
          shaderCallback: (final bounds) {
            final shift = _controller.value;
            return LinearGradient(
              begin: Alignment(-1.5 + shift * 3, 0),
              end: Alignment(0.5 + shift * 3, 0),
              colors: widget.colors,
            ).createShader(bounds);
          },
          child: Text(
            widget.text,
            style: baseStyle.copyWith(color: Colors.white),
            textAlign: widget.textAlign,
          ),
        );
      },
    );
  }
}
