import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

/// Frosted glass card with glow border effect.
class GlassCard extends StatelessWidget {
  const GlassCard({
    required this.child,
    super.key,
    this.padding,
    this.margin,
    this.borderRadius,
    this.borderColor,
    this.backgroundColor,
    this.elevation = 0,
    this.onTap,
    this.onLongPress,
    this.alignment,
    this.width,
    this.height,
    this.glowIntensity = 0.0,
  });

  final Widget child;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final double? borderRadius;
  final Color? borderColor;
  final Color? backgroundColor;
  final double elevation;
  final VoidCallback? onTap;
  final VoidCallback? onLongPress;
  final AlignmentGeometry? alignment;
  final double? width;
  final double? height;
  final double glowIntensity;

  @override
  Widget build(final BuildContext context) {
    final radius = borderRadius ?? 16.r;
    final bgColor = backgroundColor ?? AppTheme.darkSurface;
    final border = borderColor ?? AppTheme.borderSubtle;

    Widget card = Container(
      width: width,
      height: height,
      alignment: alignment,
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(
          color: glowIntensity > 0
              ? AppTheme.violet.withValues(alpha: glowIntensity.clamp(0.0, 1.0))
              : border,
          width: glowIntensity > 0 ? 1.5 : 1,
        ),
        boxShadow: glowIntensity > 0
            ? [
                BoxShadow(
                  color: AppTheme.violet.withValues(alpha: glowIntensity * 0.3),
                  blurRadius: 12,
                  spreadRadius: 2,
                ),
              ]
            : elevation > 0
            ? [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.2),
                  blurRadius: elevation * 2,
                  offset: Offset(0, elevation),
                ),
              ]
            : null,
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(radius),
        child: Padding(padding: padding ?? EdgeInsets.all(16.w), child: child),
      ),
    );

    if (onTap != null || onLongPress != null) {
      card = Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(radius),
        child: InkWell(
          onTap: onTap,
          onLongPress: onLongPress,
          borderRadius: BorderRadius.circular(radius),
          splashColor: AppTheme.violet.withValues(alpha: 0.1),
          highlightColor: AppTheme.violet.withValues(alpha: 0.05),
          child: card,
        ),
      );
    }

    if (margin != null) {
      card = Padding(padding: margin!, child: card);
    }

    return card;
  }
}
