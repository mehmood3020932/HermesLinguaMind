import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

/// Primary action button with gradient and shimmer effect.
class PrimaryButton extends StatelessWidget {
  const PrimaryButton({
    required this.label,
    required this.onPressed,
    super.key,
    this.isLoading = false,
    this.isDisabled = false,
    this.icon,
    this.height,
    this.width,
    this.borderRadius,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool isDisabled;
  final Widget? icon;
  final double? height;
  final double? width;
  final double? borderRadius;

  @override
  Widget build(final BuildContext context) {
    final isActive = onPressed != null && !isDisabled && !isLoading;
    final radius = borderRadius ?? 12.r;

    return SizedBox(
      width: width ?? double.infinity,
      height: height ?? 48.h,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        decoration: BoxDecoration(
          gradient: isActive ? AppTheme.primaryGradient : null,
          color: isActive ? null : AppTheme.darkSurfaceHover,
          borderRadius: BorderRadius.circular(radius),
          boxShadow: isActive
              ? [
                  BoxShadow(
                    color: AppTheme.violet.withValues(alpha: 0.3),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ]
              : null,
        ),
        child: Material(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(radius),
          child: InkWell(
            onTap: isActive ? onPressed : null,
            borderRadius: BorderRadius.circular(radius),
            splashColor: Colors.white.withValues(alpha: 0.2),
            child: Center(
              child: isLoading
                  ? SizedBox(
                      width: 20.w,
                      height: 20.h,
                      child: const CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          AppTheme.textInverse,
                        ),
                      ),
                    )
                  : Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (icon != null) ...[icon!, SizedBox(width: 8.w)],
                        Text(
                          label,
                          style: AppTheme.labelLarge.copyWith(
                            color: isActive
                                ? AppTheme.textInverse
                                : AppTheme.textTertiary,
                          ),
                        ),
                      ],
                    ),
            ),
          ),
        ),
      ),
    );
  }
}
