import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

class ThinkingDots extends StatefulWidget {
  const ThinkingDots({super.key});

  @override
  State<ThinkingDots> createState() => _ThinkingDotsState();
}

class _ThinkingDotsState extends State<ThinkingDots>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(final BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(3, (final index) {
        return AnimatedBuilder(
          animation: _controller,
          builder: (final context, final child) {
            final delay = index * 0.3;
            final value = (_controller.value + delay) % 1.0;
            final opacity =
                0.3 + (value < 0.5 ? value * 2 : (1 - value) * 2) * 0.7;
            final scale =
                0.8 + (value < 0.5 ? value * 2 : (1 - value) * 2) * 0.4;

            return Container(
              margin: EdgeInsets.symmetric(horizontal: 4.w),
              width: 8.w * scale,
              height: 8.h * scale,
              decoration: BoxDecoration(
                color: AppTheme.violet.withValues(alpha: opacity),
                shape: BoxShape.circle,
              ),
            );
          },
        );
      }),
    );
  }
}
