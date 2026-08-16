import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

/// Secondary outlined button with glow on hover.
class SecondaryButton extends StatelessWidget {
  const SecondaryButton({
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
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(radius),
          border: Border.all(
            color: isActive ? AppTheme.violet : AppTheme.borderSubtle,
            width: 1.5,
          ),
        ),
        child: Material(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(radius),
          child: InkWell(
            onTap: isActive ? onPressed : null,
            borderRadius: BorderRadius.circular(radius),
            splashColor: AppTheme.violet.withValues(alpha: 0.1),
            child: Center(
              child: isLoading
                  ? SizedBox(
                      width: 20.w,
                      height: 20.h,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          isActive ? AppTheme.violet : AppTheme.textTertiary,
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
                                ? AppTheme.violet
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
