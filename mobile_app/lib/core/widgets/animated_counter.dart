import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

/// Animated number counter with scale and color transitions.
class AnimatedCounter extends StatefulWidget {
  const AnimatedCounter({
    required this.value,
    super.key,
    this.duration = const Duration(milliseconds: 800),
    this.style,
    this.prefix,
    this.suffix,
    this.color,
  });

  final int value;
  final Duration duration;
  final TextStyle? style;
  final String? prefix;
  final String? suffix;
  final Color? color;

  @override
  State<AnimatedCounter> createState() => _AnimatedCounterState();
}

class _AnimatedCounterState extends State<AnimatedCounter>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<int> _animation;
  int _previousValue = 0;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: widget.duration);
    _animation = IntTween(
      begin: 0,
      end: widget.value,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOutExpo));
    _previousValue = widget.value;
    _controller.forward();
  }

  @override
  void didUpdateWidget(final AnimatedCounter oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value) {
      _previousValue = oldWidget.value;
      _animation = IntTween(begin: _previousValue, end: widget.value).animate(
        CurvedAnimation(parent: _controller, curve: Curves.easeOutExpo),
      );
      _controller.forward(from: 0);
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
      animation: _animation,
      builder: (final context, final child) {
        return Text(
          '${widget.prefix ?? ''}${_animation.value}${widget.suffix ?? ''}',
          style:
              widget.style ??
              AppTheme.displayMedium.copyWith(
                color: widget.color ?? AppTheme.textPrimary,
              ),
        );
      },
    );
  }
}

/// Rank badge with animated glow for leaderboard.
class RankBadge extends StatelessWidget {
  const RankBadge({required this.rank, super.key, this.size = 40});

  final int rank;
  final double size;

  Color get _rankColor {
    if (rank == 1) return const Color(0xFFFFD700);
    if (rank == 2) return const Color(0xFFC0C0C0);
    if (rank == 3) return const Color(0xFFCD7F32);
    return AppTheme.textTertiary;
  }

  @override
  Widget build(final BuildContext context) {
    final isTopThree = rank <= 3;

    return Container(
      width: size.w,
      height: size.h,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: isTopThree
            ? LinearGradient(
                colors: [
                  _rankColor.withValues(alpha: 0.3),
                  _rankColor.withValues(alpha: 0.1),
                ],
              )
            : null,
        color: isTopThree ? null : AppTheme.darkElevated,
        border: Border.all(
          color: isTopThree ? _rankColor : AppTheme.borderSubtle,
          width: isTopThree ? 2 : 1,
        ),
        boxShadow: isTopThree
            ? [
                BoxShadow(
                  color: _rankColor.withValues(alpha: 0.3),
                  blurRadius: 8,
                  spreadRadius: 2,
                ),
              ]
            : null,
      ),
      child: Center(
        child: Text(
          rank.toString(),
          style: AppTheme.labelLarge.copyWith(
            color: isTopThree ? _rankColor : AppTheme.textSecondary,
            fontSize: (size * 0.4).sp,
          ),
        ),
      ),
    ).animate().scale(
      begin: const Offset(0.5, 0.5),
      end: const Offset(1, 1),
      duration: const Duration(milliseconds: 400),
      curve: Curves.elasticOut,
    );
  }
}
